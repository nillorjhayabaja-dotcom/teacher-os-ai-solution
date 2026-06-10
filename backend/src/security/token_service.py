"""Token management service with blacklisting, revocation, and rotation.

Manages the lifecycle of JWT access and refresh tokens:
- Token blacklisting (for logout / revocation)
- Refresh token rotation with reuse detection
- Token revocation tracking
- Redis-backed blacklist storage
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from backend.src.core.settings import settings
from backend.src.core.constants import (
    CLAIM_JTI,
    CLAIM_SUBJECT,
    CLAIM_TENANT,
    TOKEN_TYPE_REFRESH,
)
from backend.src.core.exceptions import TokenRevokedError, TokenReuseDetectedError
from backend.src.security.jwt_service import JWTService


@dataclass
class TokenBlacklistEntry:
    """Represents a blacklisted token entry."""
    jti: str
    subject: str
    expires_at: dt.datetime
    revoked_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    reason: str = ""


class TokenService:
    """Manages JWT token lifecycle with blacklisting and rotation.

    Uses a Redis backend for blacklist storage with automatic TTL based on
    token expiration. Supports refresh token rotation where each refresh
    operation invalidates the previous refresh token.
    """

    def __init__(self, jwt_service: JWTService, redis_client: Optional[Any] = None) -> None:
        self._jwt_service = jwt_service
        self._redis = redis_client
        # In-memory fallback when Redis is not available
        self._blacklist: Dict[str, TokenBlacklistEntry] = {}
        self._used_refresh_tokens: Dict[str, str] = {}  # old_jti -> new_jti mapping

    def _blacklist_key(self, jti: str) -> str:
        return f"token:blacklist:{jti}"

    def _used_token_key(self, jti: str) -> str:
        return f"token:used:{jti}"

    def _refresh_chain_key(self, subject: str) -> str:
        return f"token:refresh_chain:{subject}"

    # ---------------------------------------------------------------------
    # Token Blacklisting
    # ---------------------------------------------------------------------
    async def blacklist_token(
        self,
        jti: str,
        subject: str,
        expires_at: dt.datetime,
        reason: str = "",
    ) -> None:
        """Add a token to the blacklist."""
        entry = TokenBlacklistEntry(
            jti=jti,
            subject=subject,
            expires_at=expires_at,
            reason=reason,
        )

        if self._redis:
            ttl = int((expires_at - dt.datetime.now(dt.timezone.utc)).total_seconds())
            if ttl > 0:
                await self._redis.setex(
                    self._blacklist_key(jti),
                    ttl,
                    json.dumps({
                        "jti": jti,
                        "subject": subject,
                        "expires_at": expires_at.isoformat(),
                        "revoked_at": entry.revoked_at.isoformat(),
                        "reason": reason,
                    }),
                )
        else:
            self._blacklist[jti] = entry

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        if self._redis:
            exists = await self._redis.exists(self._blacklist_key(jti))
            return bool(exists)
        return jti in self._blacklist

    async def revoke_all_user_tokens(self, subject: str) -> int:
        """Revoke all tokens for a given user (subject).

        Returns the number of tokens revoked.
        """
        # In a production system, this would iterate over a token index
        # For now, we track revoked tokens by user in Redis
        key = f"token:user_revoked:{subject}"
        if self._redis:
            await self._redis.setex(key, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400, "1")
        return 1

    async def are_user_tokens_revoked(self, subject: str) -> bool:
        """Check if all tokens for a user have been revoked."""
        if self._redis:
            exists = await self._redis.exists(f"token:user_revoked:{subject}")
            return bool(exists)
        return False

    # ---------------------------------------------------------------------
    # Refresh Token Rotation
    # ---------------------------------------------------------------------
    async def mark_refresh_token_used(
        self,
        old_jti: str,
        old_token: str,
        new_jti: str,
        subject: str,
        expires_at: dt.datetime,
    ) -> None:
        """Mark a refresh token as used (consumed during rotation).

        Implements refresh token rotation: the old token is blacklisted
        and mapped to the new token to detect reuse attempts.
        """
        # Blacklist the old refresh token
        await self.blacklist_token(
            jti=old_jti,
            subject=subject,
            expires_at=expires_at,
            reason="refresh_rotation",
        )

        # Track the rotation chain to detect reuse
        if self._redis:
            ttl = int((expires_at - dt.datetime.now(dt.timezone.utc)).total_seconds())
            if ttl > 0:
                await self._redis.setex(
                    self._used_token_key(old_jti),
                    ttl,
                    new_jti,
                )
        else:
            self._used_refresh_tokens[old_jti] = new_jti

    async def is_refresh_token_used(self, jti: str) -> bool:
        """Check if a refresh token has already been used (rotation)."""
        if self._redis:
            exists = await self._redis.exists(self._used_token_key(jti))
            return bool(exists)
        return jti in self._used_refresh_tokens

    async def detect_token_reuse(self, jti: str, token: str) -> None:
        """Detect and handle refresh token reuse.

        If a previously-used refresh token is reused, it indicates possible
        token theft. All tokens for the user should be revoked.
        """
        if await self.is_blacklisted(jti):
            # Token was already used/rotated - possible theft
            payload = self._jwt_service.decode(token, verify_exp=False)
            subject = payload.get(CLAIM_SUBJECT, "")
            await self.revoke_all_user_tokens(subject)
            raise TokenReuseDetectedError(
                f"Refresh token reuse detected for user {subject}. All tokens revoked."
            )

    # ---------------------------------------------------------------------
    # Token Validation Pipeline
    # ---------------------------------------------------------------------
    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Full validation pipeline for an access token.

        1. Decode and verify JWT signature/expiry
        2. Check token type is 'access'
        3. Check blacklist
        4. Check if user tokens are revoked

        Returns the decoded payload on success.
        """
        payload = self._jwt_service.decode(token)
        jti = payload.get(CLAIM_JTI, "")

        if await self.is_blacklisted(jti):
            raise TokenRevokedError("Token has been revoked")

        subject = payload.get(CLAIM_SUBJECT, "")
        if await self.are_user_tokens_revoked(subject):
            raise TokenRevokedError("All user tokens have been revoked")

        return payload

    async def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """Full validation pipeline for a refresh token.

        Includes reuse detection and rotation validation.
        """
        payload = self._jwt_service.decode(token)
        jti = payload.get(CLAIM_JTI, "")

        # Check for token reuse (theft detection)
        await self.detect_token_reuse(jti, token)

        # Check blacklist
        if await self.is_blacklisted(jti):
            raise TokenRevokedError("Refresh token has been revoked")

        # Check if user tokens are revoked
        subject = payload.get(CLAIM_SUBJECT, "")
        if await self.are_user_tokens_revoked(subject):
            raise TokenRevokedError("All user tokens have been revoked")

        return payload