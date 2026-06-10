"""Session management service with device tracking.

Supports:
- Device-aware session tracking
- Concurrent session limits
- Session idle timeout detection
- Remote session revocation
- Geographic/IP tracking for anomaly detection
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.src.core.settings import settings
from backend.src.core.constants import MAX_SESSIONS_PER_USER, SESSION_IDLE_TIMEOUT_MINUTES


@dataclass
class Session:
    """Represents an active user session."""
    session_id: str
    user_id: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    school_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    is_revoked: bool = False
    location: Optional[Dict[str, Any]] = None  # Geo-ip data


class SessionService:
    """Manages user sessions with device tracking and revocation.

    Uses Redis for session storage with TTL for automatic cleanup.
    Tracks device fingerprints and enforces concurrent session limits.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self._redis = redis_client
        self._sessions: Dict[str, Session] = {}  # In-memory fallback
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        return f"user_sessions:{user_id}"

    def _user_device_key(self, user_id: str, device_id: str) -> str:
        return f"user_device:{user_id}:{device_id}"

    # ---------------------------------------------------------------------
    # Session Creation
    # ---------------------------------------------------------------------
    async def create_session(
        self,
        user_id: str,
        *,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None,
    ) -> Session:
        """Create a new session for a user.

        Automatically enforces concurrent session limits by revoking
        the oldest session if the limit is exceeded.

        Args:
            user_id: The user identifier.
            device_id: Unique device identifier.
            device_name: Human-readable device name.
            ip_address: Client IP address.
            user_agent: User-Agent header value.
            tenant_id: Tenant identifier.
            organization_id: Organization identifier.
            school_id: School identifier.

        Returns:
            The newly created Session.
        """
        # Enforce session limits
        await self._enforce_session_limit(user_id)

        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id,
            organization_id=organization_id,
            school_id=school_id,
            created_at=now,
            last_activity_at=now,
            expires_at=datetime.fromtimestamp(
                time.time() + settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
            ),
            is_active=True,
            is_revoked=False,
        )

        # Store session
        if self._redis:
            ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
            await self._redis.setex(
                self._session_key(session_id),
                ttl,
                json.dumps({
                    "session_id": session_id,
                    "user_id": user_id,
                    "device_id": device_id,
                    "device_name": device_name,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "tenant_id": tenant_id,
                    "organization_id": organization_id,
                    "school_id": school_id,
                    "created_at": now.isoformat(),
                    "last_activity_at": now.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "is_active": True,
                    "is_revoked": False,
                }),
            )
            # Add to user's session list
            await self._redis.sadd(self._user_sessions_key(user_id), session_id)
            await self._redis.expire(
                self._user_sessions_key(user_id),
                settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            )
        else:
            self._sessions[session_id] = session
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)

        return session

    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum concurrent sessions per user.

        If the limit is exceeded, revoke the oldest session.
        """
        active_sessions = await self.get_active_sessions(user_id)
        if len(active_sessions) >= MAX_SESSIONS_PER_USER:
            # Revoke the oldest session
            active_sessions.sort(key=lambda s: s.last_activity_at)
            oldest = active_sessions[0]
            self.revoke_session(oldest.session_id, user_id)

    # ---------------------------------------------------------------------
    # Session Retrieval
    # ---------------------------------------------------------------------
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        if self._redis:
            data = await self._redis.get(self._session_key(session_id))
            if not data:
                return None
            session_data = json.loads(data)
            return Session(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                device_id=session_data.get("device_id"),
                device_name=session_data.get("device_name"),
                ip_address=session_data.get("ip_address"),
                user_agent=session_data.get("user_agent"),
                tenant_id=session_data.get("tenant_id"),
                organization_id=session_data.get("organization_id"),
                school_id=session_data.get("school_id"),
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity_at=datetime.fromisoformat(session_data["last_activity_at"]),
                expires_at=datetime.fromisoformat(session_data["expires_at"]),
                is_active=session_data.get("is_active", True),
                is_revoked=session_data.get("is_revoked", False),
            )
        return self._sessions.get(session_id)

    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        sessions = []
        if self._redis:
            session_ids = await self._redis.smembers(self._user_sessions_key(user_id))
            for sid in session_ids:
                session = await self.get_session(sid.decode() if isinstance(sid, bytes) else sid)
                if session and session.is_active and not session.is_revoked:
                    # Check expiration
                    if session.expires_at > datetime.now(timezone.utc):
                        sessions.append(session)
        else:
            for sid in self._user_sessions.get(user_id, []):
                session = self._sessions.get(sid)
                if session and session.is_active and not session.is_revoked:
                    if session.expires_at > datetime.now(timezone.utc):
                        sessions.append(session)

        return sessions

    # ---------------------------------------------------------------------
    # Session Activity
    # ---------------------------------------------------------------------
    async def update_session_activity(self, session_id: str) -> None:
        """Update the last activity timestamp for a session."""
        now = datetime.now(timezone.utc)

        if self._redis:
            data = await self._redis.get(self._session_key(session_id))
            if data:
                session_data = json.loads(data)
                session_data["last_activity_at"] = now.isoformat()
                ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
                await self._redis.setex(
                    self._session_key(session_id), ttl, json.dumps(session_data)
                )
        else:
            session = self._sessions.get(session_id)
            if session:
                session.last_activity_at = now

    async def is_session_idle(self, session_id: str) -> bool:
        """Check if a session has been idle beyond the timeout."""
        session = await self.get_session(session_id)
        if not session:
            return True

        idle_seconds = (datetime.now(timezone.utc) - session.last_activity_at).total_seconds()
        return idle_seconds > SESSION_IDLE_TIMEOUT_MINUTES * 60

    # ---------------------------------------------------------------------
    # Session Revocation
    # ---------------------------------------------------------------------
    def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a specific session."""
        if self._redis:
            data = self._redis.get(self._session_key(session_id))
            if data:
                session_data = json.loads(data)
                session_data["is_revoked"] = True
                session_data["is_active"] = False
                ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
                self._redis.setex(
                    self._session_key(session_id), ttl, json.dumps(session_data)
                )
                # Remove from user's session set
                self._redis.srem(self._user_sessions_key(user_id), session_id)
                return True
            return False

        session = self._sessions.get(session_id)
        if session:
            session.is_revoked = True
            session.is_active = False
            if user_id in self._user_sessions:
                self._user_sessions[user_id] = [
                    s for s in self._user_sessions[user_id] if s != session_id
                ]
            return True
        return False

    async def revoke_all_user_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user, optionally excluding one.

        Args:
            user_id: The user identifier.
            exclude_session_id: Optional session ID to keep active.

        Returns:
            Number of sessions revoked.
        """
        count = 0
        active_sessions = await self.get_active_sessions(user_id)
        for session in active_sessions:
            if exclude_session_id and session.session_id == exclude_session_id:
                continue
            if self.revoke_session(session.session_id, user_id):
                count += 1
        return count

    # ---------------------------------------------------------------------
    # Session Validation
    # ---------------------------------------------------------------------
    async def validate_session(self, session_id: str) -> bool:
        """Check if a session is still valid (active, not revoked, not expired, not idle)."""
        session = await self.get_session(session_id)
        if not session:
            return False
        if session.is_revoked:
            return False
        if not session.is_active:
            return False
        if session.expires_at < datetime.now(timezone.utc):
            return False
        if await self.is_session_idle(session_id):
            return False
        return True

    # ---------------------------------------------------------------------
    # Session Cleanup
    # ---------------------------------------------------------------------
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from the store.

        Returns the number of sessions cleaned up.
        """
        count = 0
        now = datetime.now(timezone.utc)

        if self._redis:
            # Redis handles TTL automatically, but we can still iterate
            # This is a no-op for Redis
            return 0

        expired_session_ids = []
        for session_id, session in self._sessions.items():
            if session.expires_at < now or session.is_revoked:
                expired_session_ids.append(session_id)
                if session.user_id in self._user_sessions:
                    self._user_sessions[session.user_id] = [
                        s for s in self._user_sessions[session.user_id] if s != session_id
                    ]

        for sid in expired_session_ids:
            del self._sessions[sid]
            count += 1

        return count