"""Authentication API endpoints.

Provides login, registration, token refresh, MFA verification,
password management, and session management endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from backend.src.core.constants import (
    EVENT_LOGIN_SUCCESS,
    EVENT_LOGIN_FAILED,
    EVENT_LOGOUT,
    EVENT_PASSWORD_CHANGE,
    EVENT_PASSWORD_RESET,
    EVENT_PASSWORD_RESET_REQUEST,
    EVENT_TOKEN_REFRESH,
    EVENT_TOKEN_REVOKE,
    EVENT_MFA_ENABLED,
    EVENT_MFA_DISABLED,
    EVENT_MFA_VERIFIED,
    EVENT_MFA_FAILED,
    EVENT_SESSION_CREATED,
    EVENT_SESSION_REVOKED,
    ROLE_TEACHER,
    PERM_MFA_ENABLE,
    PERM_MFA_DISABLE,
    PERM_SESSION_REVOKE,
    PERM_TOKEN_REVOKE,
)
from backend.src.core.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    TokenReuseDetectedError,
    InsufficientPermissionsError,
    MFANotEnabledError,
    MFAVerificationFailedError,
)
from backend.src.security.jwt_service import JWTService
from backend.src.security.password_service import PasswordService
from backend.src.security.token_service import TokenService
from backend.src.security.refresh_token_service import RefreshTokenService
from backend.src.security.mfa_service import MFAService
from backend.src.security.session_service import SessionService
from backend.src.security.rbac import RBACService
from backend.src.security.security_event_service import SecurityEventService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    mfa_code: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    mfa_required: bool = False


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=12)
    first_name: str
    last_name: str
    organization_id: Optional[str] = None
    school_id: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    message: str = "Registration successful. Please verify your email."


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)


class MFAEnableResponse(BaseModel):
    secret: str
    qr_code_url: str
    recovery_codes: List[str]


class MFAVerifyRequest(BaseModel):
    code: str


class SessionInfo(BaseModel):
    session_id: str
    device_name: Optional[str] = None
    created_at: str
    last_activity: str
    is_current: bool = False


class UserInfo(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    mfa_enabled: bool
    organization_id: Optional[str] = None
    school_id: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory user store (temporary – will be replaced by DB)
# ---------------------------------------------------------------------------

_users_db: Dict[str, Dict[str, Any]] = {}


def _get_services(request: Request):
    """Extract shared services from app state."""
    app = request.app
    return {
        "jwt_service": app.state.jwt_service,
        "token_service": app.state.token_service,
        "rbac_service": app.state.rbac_service,
        "password_service": PasswordService(),
        "refresh_service": RefreshTokenService(),
        "mfa_service": MFAService(),
        "session_service": SessionService(),
        "event_service": SecurityEventService(),
    }


def _get_user_or_404(user_id: str) -> Dict[str, Any]:
    user = _users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(req: RegisterRequest, request: Request):
    """Register a new user account."""
    svc = _get_services(request)

    # Check for duplicate email
    for uid, u in _users_db.items():
        if u["email"] == req.email:
            raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid4())
    hashed = svc["password_service"].hash_password(req.password)

    # SECURITY: Never trust user-supplied role - always assign default role
    assigned_role = ROLE_TEACHER

    _users_db[user_id] = {
        "id": user_id,
        "email": req.email,
        "password_hash": hashed,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "role": assigned_role,
        "mfa_enabled": False,
        "mfa_secret": None,
        "organization_id": req.organization_id,
        "school_id": req.school_id,
        "is_active": True,
    }

    # Assign role in RBAC
    svc["rbac_service"].role_engine.assign_role(user_id, assigned_role)

    # Log event
    svc["event_service"].record_event(EVENT_LOGIN_SUCCESS, {"user_id": user_id})

    return RegisterResponse(user_id=user_id, email=req.email)


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request):
    """Authenticate a user and return JWT tokens."""
    svc = _get_services(request)

    # Find user by email
    user = None
    for u in _users_db.values():
        if u["email"] == req.email:
            user = u
            break

    if not user or not svc["password_service"].verify_password(req.password, user["password_hash"]):
        svc["event_service"].record_event(EVENT_LOGIN_FAILED, {"email": req.email})
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Check MFA if enabled
    if user["mfa_enabled"] and not req.mfa_code:
        return LoginResponse(
            access_token="",
            refresh_token="",
            token_type="Bearer",
            expires_in=0,
            user={"id": user["id"], "email": user["email"], "mfa_required": True},
            mfa_required=True,
        )

    if user["mfa_enabled"] and req.mfa_code:
        verified = svc["mfa_service"].verify_totp(user.get("mfa_secret", ""), req.mfa_code)
        if not verified:
            svc["event_service"].record_event(EVENT_MFA_FAILED, {"user_id": user["id"]})
            raise HTTPException(status_code=401, detail="Invalid MFA code")
        svc["event_service"].record_event(EVENT_MFA_VERIFIED, {"user_id": user["id"]})

    # Create session
    session_id = str(uuid4())
    svc["session_service"].create_session(
        user_id=user["id"],
        session_id=session_id,
        device_id=req.device_id or "unknown",
        device_name=req.device_name or "Unknown Device",
    )

    # Generate tokens
    roles = list(svc["rbac_service"].get_user_roles(user["id"]))
    permissions = list(svc["rbac_service"].get_user_permissions(user["id"]))

    access_token = svc["jwt_service"].encode(
        subject=user["id"],
        roles=roles,
        permissions=permissions,
        tenant_id=user.get("organization_id"),
        school_id=user.get("school_id"),
        device_id=req.device_id or "",
        device_name=req.device_name or "",
        mfa_verified=user["mfa_enabled"],
        token_type="access",
    )

    refresh_token = svc["refresh_service"].create_refresh_token(
        user_id=user["id"],
        token_id=str(uuid4()),
        device_id=req.device_id or "",
    )

    svc["event_service"].record_event(EVENT_LOGIN_SUCCESS, {"user_id": user["id"]})
    svc["event_service"].record_event(EVENT_SESSION_CREATED, {"user_id": user["id"], "session_id": session_id})

    from backend.src.core.settings import settings

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"],
            "mfa_enabled": user["mfa_enabled"],
        },
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh(req: TokenRefreshRequest, request: Request):
    """Refresh an expired access token using a refresh token."""
    svc = _get_services(request)

    try:
        result = svc["refresh_service"].rotate_refresh_token(req.refresh_token)
    except TokenReuseDetectedError:
        raise HTTPException(status_code=401, detail="Token reuse detected")
    except (TokenExpiredError, TokenRevokedError, TokenInvalidError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = result["user_id"]
    user = _get_user_or_404(user_id)

    roles = list(svc["rbac_service"].get_user_roles(user_id))
    permissions = list(svc["rbac_service"].get_user_permissions(user_id))

    access_token = svc["jwt_service"].encode(
        subject=user_id,
        roles=roles,
        permissions=permissions,
        tenant_id=user.get("organization_id"),
        school_id=user.get("school_id"),
        mfa_verified=user["mfa_enabled"],
        token_type="access",
    )

    svc["event_service"].record_event(EVENT_TOKEN_REFRESH, {"user_id": user_id})

    from backend.src.core.settings import settings

    return TokenRefreshResponse(
        access_token=access_token,
        refresh_token=result["new_refresh_token"],
        token_type="Bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
def logout(request: Request):
    """Logout and revoke the current session and invalidate the token."""
    svc = _get_services(request)
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        # Revoke the access token by adding it to the blacklist
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = svc["jwt_service"].decode(token, verify_exp=False)
                import datetime as _dt
                jti = payload.get("jti", "")
                expires_at = _dt.datetime.fromtimestamp(
                    payload.get("exp", 0), tz=_dt.timezone.utc
                )
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.submit(
                                asyncio.run,
                                svc["token_service"].blacklist_token(
                                    jti, user_id, expires_at, reason="logout"
                                ),
                            )
                    else:
                        loop.run_until_complete(
                            svc["token_service"].blacklist_token(
                                jti, user_id, expires_at, reason="logout"
                            )
                        )
                except RuntimeError:
                    asyncio.run(
                        svc["token_service"].blacklist_token(
                            jti, user_id, expires_at, reason="logout"
                        )
                    )
            except Exception:
                pass  # Token invalid/expired, proceed with logout

        # Revoke the session
        session_id = getattr(request.state, "session_id", None)
        if session_id:
            svc["session_service"].revoke_session(session_id)

        svc["event_service"].record_event(EVENT_LOGOUT, {"user_id": user_id})

    return {"detail": "Logged out successfully"}


@router.post("/password/change")
def change_password(req: PasswordChangeRequest, request: Request):
    """Change the current user's password."""
    svc = _get_services(request)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = _get_user_or_404(user_id)

    if not svc["password_service"].verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user["password_hash"] = svc["password_service"].hash_password(req.new_password)
    svc["event_service"].record_event(EVENT_PASSWORD_CHANGE, {"user_id": user_id})

    return {"detail": "Password changed successfully"}


@router.post("/password/reset")
def request_password_reset(req: PasswordResetRequest, request: Request):
    """Request a password reset token."""
    svc = _get_services(request)

    # Find user by email (don't reveal if email exists)
    user = None
    for u in _users_db.values():
        if u["email"] == req.email:
            user = u
            break

    if user:
        svc["event_service"].record_event(EVENT_PASSWORD_RESET_REQUEST, {"user_id": user["id"]})

    return {"detail": "If the email exists, a reset link has been sent"}


@router.post("/password/reset/confirm")
def confirm_password_reset(req: PasswordResetConfirm, request: Request):
    """Confirm a password reset with token."""
    svc = _get_services(request)

    # SECURITY: Actually validate the reset token
    user_id = svc["password_service"].verify_reset_token(req.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = _get_user_or_404(user_id)

    # Hash the new password
    user["password_hash"] = svc["password_service"].hash_password(req.new_password)

    # Mark token as used (one-time use)
    svc["password_service"].mark_reset_token_used(req.token)

    svc["event_service"].record_event(EVENT_PASSWORD_RESET, {"user_id": user_id})

    return {"detail": "Password has been reset successfully"}


@router.post("/mfa/enable", response_model=MFAEnableResponse)
def enable_mfa(request: Request):
    """Enable MFA for the current user."""
    svc = _get_services(request)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    svc["rbac_service"].require_permission(user_id, PERM_MFA_ENABLE)

    user = _get_user_or_404(user_id)
    secret, url = svc["mfa_service"].generate_totp_secret(email=user["email"])
    recovery_codes = [str(uuid4()) for _ in range(8)]

    user["mfa_secret"] = secret
    user["mfa_recovery_codes"] = recovery_codes

    svc["event_service"].record_event(EVENT_MFA_ENABLED, {"user_id": user_id})

    return MFAEnableResponse(secret=secret, qr_code_url=url, recovery_codes=recovery_codes)


@router.post("/mfa/disable")
def disable_mfa(request: Request):
    """Disable MFA for the current user."""
    svc = _get_services(request)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    svc["rbac_service"].require_permission(user_id, PERM_MFA_DISABLE)

    user = _get_user_or_404(user_id)
    user["mfa_secret"] = None
    user["mfa_enabled"] = False

    svc["event_service"].record_event(EVENT_MFA_DISABLED, {"user_id": user_id})
    return {"detail": "MFA disabled successfully"}


@router.get("/sessions", response_model=List[SessionInfo])
def list_sessions(request: Request):
    """List all active sessions for the current user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    svc = _get_services(request)
    sessions = svc["session_service"].get_user_sessions(user_id)

    return [
        SessionInfo(
            session_id=s["session_id"],
            device_name=s.get("device_name"),
            created_at=str(s.get("created_at", "")),
            last_activity=str(s.get("last_activity", "")),
            is_current=s.get("is_current", False),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(session_id: str, request: Request):
    """Revoke a specific session."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    svc = _get_services(request)
    svc["rbac_service"].require_permission(user_id, PERM_SESSION_REVOKE)

    svc["session_service"].revoke_session(session_id)
    svc["event_service"].record_event(EVENT_SESSION_REVOKED, {
        "user_id": user_id,
        "session_id": session_id,
    })

    return {"detail": "Session revoked successfully"}


@router.get("/me", response_model=UserInfo)
def get_current_user(request: Request):
    """Get the current authenticated user's profile."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = _get_user_or_404(user_id)
    return UserInfo(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        mfa_enabled=user["mfa_enabled"],
        organization_id=user.get("organization_id"),
        school_id=user.get("school_id"),
    )