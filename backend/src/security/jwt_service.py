"""Production-grade JWT generation and validation service.

Uses **PyJWT** with RSA‑256 keys. Supports:
- Access and refresh tokens with distinct claims
- jti (JWT ID) for revocation tracking
- Device tracking via device_id claim
- Token type distinction (access vs refresh)
- Issuer, audience validation
- MFA verification status embedding
- Tenant, organization, school isolation
"""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import jwt

from backend.src.core.settings import settings
from backend.src.core.constants import (
    CLAIM_SUBJECT,
    CLAIM_TENANT,
    CLAIM_ROLES,
    CLAIM_PERMISSIONS,
    CLAIM_JTI,
    CLAIM_ISSUER,
    CLAIM_AUDIENCE,
    CLAIM_ISSUED_AT,
    CLAIM_EXPIRATION,
    CLAIM_NOT_BEFORE,
    CLAIM_DEVICE_ID,
    CLAIM_DEVICE_NAME,
    CLAIM_TOKEN_TYPE,
    CLAIM_ORGANIZATION_ID,
    CLAIM_SCHOOL_ID,
    CLAIM_MFA_VERIFIED,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)
from backend.src.core.exceptions import TokenExpiredError, TokenInvalidError


class JWTService:
    """Service responsible for creating and verifying JWTs.

    The private/public RSA keys are read from the paths defined in ``settings``.
    Tokens contain standard claims plus optional tenant, roles, permissions,
    device info, and MFA verification status.

    Uses RS256 (RSA Signature with SHA-256) for asymmetric signing.
    The private key signs tokens; the public key verifies them.
    """

    def __init__(self) -> None:
        self._private_key = Path(settings.JWT_PRIVATE_KEY_PATH).read_text()
        self._public_key = Path(settings.JWT_PUBLIC_KEY_PATH).read_text()
        self._algorithm = settings.JWT_ALGORITHM
        self._issuer = settings.JWT_ISSUER
        self._audience = settings.JWT_AUDIENCE
        self._leeway = settings.JWT_LEEWAY_SECONDS

    # ---------------------------------------------------------------------
    # Helper to compute timestamps
    # ---------------------------------------------------------------------
    def _now(self) -> dt.datetime:
        return dt.datetime.now(dt.timezone.utc)

    def _generate_jti(self) -> str:
        """Generate a unique JWT ID for revocation tracking."""
        return str(uuid.uuid4())

    # ---------------------------------------------------------------------
    # Token creation
    # ---------------------------------------------------------------------
    def create_access_token(
        self,
        subject: str,
        *,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        mfa_verified: bool = False,
        expires_delta: Optional[dt.timedelta] = None,
    ) -> str:
        now = self._now()
        exp = now + (expires_delta or dt.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        jti = self._generate_jti()

        payload: Dict[str, Any] = {
            CLAIM_SUBJECT: subject,
            CLAIM_JTI: jti,
            CLAIM_ISSUER: self._issuer,
            CLAIM_ISSUED_AT: now,
            CLAIM_EXPIRATION: exp,
            CLAIM_NOT_BEFORE: now,
            CLAIM_TOKEN_TYPE: TOKEN_TYPE_ACCESS,
            CLAIM_MFA_VERIFIED: mfa_verified,
        }

        if self._audience:
            payload[CLAIM_AUDIENCE] = self._audience
        if tenant_id:
            payload[CLAIM_TENANT] = tenant_id
        if organization_id:
            payload[CLAIM_ORGANIZATION_ID] = organization_id
        if school_id:
            payload[CLAIM_SCHOOL_ID] = school_id
        if roles:
            payload[CLAIM_ROLES] = roles
        if permissions:
            payload[CLAIM_PERMISSIONS] = permissions
        if device_id:
            payload[CLAIM_DEVICE_ID] = device_id
        if device_name:
            payload[CLAIM_DEVICE_NAME] = device_name

        token = jwt.encode(payload, self._private_key, algorithm=self._algorithm)
        return token

    def create_refresh_token(
        self,
        subject: str,
        *,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        expires_delta: Optional[dt.timedelta] = None,
    ) -> str:
        now = self._now()
        exp = now + (expires_delta or dt.timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))
        jti = self._generate_jti()

        payload: Dict[str, Any] = {
            CLAIM_SUBJECT: subject,
            CLAIM_JTI: jti,
            CLAIM_ISSUER: self._issuer,
            CLAIM_ISSUED_AT: now,
            CLAIM_EXPIRATION: exp,
            CLAIM_NOT_BEFORE: now,
            CLAIM_TOKEN_TYPE: TOKEN_TYPE_REFRESH,
        }

        if self._audience:
            payload[CLAIM_AUDIENCE] = self._audience
        if tenant_id:
            payload[CLAIM_TENANT] = tenant_id
        if organization_id:
            payload[CLAIM_ORGANIZATION_ID] = organization_id
        if school_id:
            payload[CLAIM_SCHOOL_ID] = school_id
        if device_id:
            payload[CLAIM_DEVICE_ID] = device_id
        if device_name:
            payload[CLAIM_DEVICE_NAME] = device_name

        token = jwt.encode(payload, self._private_key, algorithm=self._algorithm)
        return token

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    def decode(self, token: str, *, verify_exp: bool = True) -> Dict[str, Any]:
        """Decode and verify a JWT.

        Args:
            token: The JWT string to decode.
            verify_exp: Whether to verify expiration. Set False for testing only.

        Returns:
            Decoded payload as a dictionary.

        Raises:
            TokenExpiredError: If the token has expired.
            TokenInvalidError: If the token is invalid or malformed.
        """
        try:
            options = {
                "verify_exp": verify_exp,
                "verify_iat": True,
                "verify_signature": True,
            }
            if self._audience:
                options["verify_aud"] = True

            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._leeway,
                options=options,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def get_jti(self, token: str) -> str:
        """Extract the JWT ID from a token without full verification.

        Useful for checking revocation status before full decode.
        """
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False, "verify_signature": True},
            )
            return payload.get(CLAIM_JTI, "")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def get_token_type(self, token: str) -> str:
        """Extract the token type from a decoded token."""
        payload = self.decode(token)
        return payload.get(CLAIM_TOKEN_TYPE, "")

    def is_access_token(self, token: str) -> bool:
        """Check if the token is an access token."""
        return self.get_token_type(token) == TOKEN_TYPE_ACCESS

    def is_refresh_token(self, token: str) -> bool:
        """Check if the token is a refresh token."""
        return self.get_token_type(token) == TOKEN_TYPE_REFRESH