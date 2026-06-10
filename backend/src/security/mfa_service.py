"""Multi-Factor Authentication Service.

Supports:
- Email OTP (One-Time Password) via time-based codes
- TOTP (Time-based One-Time Password) authenticator apps
- MFA enrollment and verification workflows
"""

from __future__ import annotations

import io
import math
import random
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pyotp
import qrcode

from backend.src.core.settings import settings
from backend.src.core.exceptions import MFANotEnabledError, MFAVerificationFailedError


@dataclass
class MFAStatus:
    """Current MFA configuration status for a user."""
    enabled: bool = False
    email_otp_enabled: bool = False
    totp_enabled: bool = False
    totp_verified: bool = False
    method: Optional[str] = None  # "email_otp" or "totp"


class MFAService:
    """Multi-Factor Authentication service.

    Supports both email OTP and TOTP authenticator apps.
    TOTP follows the RFC 6238 standard with SHA-1 and 30-second intervals.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self._redis = redis_client
        self._otp_store: Dict[str, Dict[str, Any]] = {}  # In-memory fallback
        self._totp_secrets: Dict[str, str] = {}  # In-memory fallback

    # ---------------------------------------------------------------------
    # TOTP (Authenticator App)
    # ---------------------------------------------------------------------

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret key.

        Returns:
            Base32-encoded secret for use with authenticator apps.
        """
        return pyotp.random_base32()

    def get_totp_provisioning_uri(
        self,
        secret: str,
        email: str,
        issuer: Optional[str] = None,
    ) -> str:
        """Generate the otpauth:// URI for QR code generation.

        Args:
            secret: The TOTP secret key.
            email: User's email for the account name.
            issuer: Display name for the authenticator app.

        Returns:
            otpauth:// URI string for QR code generation.
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer or settings.MFA_TOTP_ISSUER,
        )

    def generate_totp_qr_code(self, provisioning_uri: str) -> str:
        """Generate a QR code image as a base64-encoded PNG.

        Args:
            provisioning_uri: The otpauth:// URI.

        Returns:
            Base64-encoded PNG image data.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        import base64
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify a TOTP token.

        Args:
            secret: The TOTP secret key.
            token: The 6-digit token from the authenticator app.

        Returns:
            True if the token is valid within the validity window.
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(
            token,
            valid_window=settings.MFA_TOTP_VALIDITY_WINDOW,
        )

    # ---------------------------------------------------------------------
    # Email OTP
    # ---------------------------------------------------------------------

    def generate_email_otp(self, email: str) -> str:
        """Generate a time-based OTP and send to email.

        Args:
            email: The email address to send the OTP to.

        Returns:
            The generated OTP code (6 digits).
        """
        otp = f"{random.randint(100000, 999999)}"
        expires_at = time.time() + settings.MFA_EMAIL_OTP_EXPIRE_SECONDS

        otp_data = {
            "otp": otp,
            "email": email,
            "expires_at": expires_at,
            "verified": False,
            "attempts": 0,
        }

        if self._redis:
            self._redis.setex(
                f"otp:email:{email}",
                settings.MFA_EMAIL_OTP_EXPIRE_SECONDS,
                str(otp_data),
            )
        else:
            self._otp_store[f"email:{email}"] = otp_data

        # In production, send email via email service
        # email_service.send_otp_email(email, otp)

        return otp

    def verify_email_otp(self, email: str, otp: str) -> bool:
        """Verify an email OTP.

        Args:
            email: The email address.
            otp: The OTP code to verify.

        Returns:
            True if the OTP is valid and not expired.
        """
        otp_data = None

        if self._redis:
            data = self._redis.get(f"otp:email:{email}")
            if data:
                import ast
                otp_data = ast.literal_eval(data) if isinstance(data, str) else data
        else:
            otp_data = self._otp_store.get(f"email:{email}")

        if not otp_data:
            return False

        # Check expiration
        if time.time() > otp_data["expires_at"]:
            return False

        # Check max attempts
        if otp_data["attempts"] >= 5:
            return False

        # Update attempts
        otp_data["attempts"] += 1

        # Verify OTP
        if otp_data["otp"] == otp:
            otp_data["verified"] = True
            return True

        return False

    # ---------------------------------------------------------------------
    # MFA Management
    # ---------------------------------------------------------------------

    def enable_email_otp(self, user_id: str, email: str) -> MFAStatus:
        """Enable email OTP MFA for a user."""
        # In production, persist to database
        status = MFAStatus(
            enabled=True,
            email_otp_enabled=True,
            method="email_otp",
        )
        return status

    def enable_totp(self, user_id: str, secret: str) -> MFAStatus:
        """Enable TOTP MFA for a user after verifying the setup token."""
        status = MFAStatus(
            enabled=True,
            totp_enabled=True,
            totp_verified=True,
            method="totp",
        )
        return status

    def disable_mfa(self, user_id: str) -> MFAStatus:
        """Disable all MFA methods for a user."""
        status = MFAStatus(enabled=False)
        return status

    def get_mfa_status(self, user_id: str) -> MFAStatus:
        """Get the current MFA configuration for a user."""
        # In production, read from database
        return MFAStatus(enabled=False)

    def requires_mfa(self, user_id: str) -> bool:
        """Check if a user is required to use MFA."""
        status = self.get_mfa_status(user_id)
        return status.enabled

    def verify_mfa(self, user_id: str, method: str, code: str, email: Optional[str] = None) -> bool:
        """Verify an MFA code regardless of method.

        Args:
            user_id: The user identifier.
            method: "email_otp" or "totp".
            code: The verification code.
            email: Required for email_otp method.

        Returns:
            True if verification succeeds.

        Raises:
            MFAVerificationFailedError: If verification fails.
        """
        status = self.get_mfa_status(user_id)
        if not status.enabled:
            raise MFANotEnabledError("MFA is not enabled for this user")

        is_valid = False
        if method == "email_otp" and email:
            is_valid = self.verify_email_otp(email, code)
        elif method == "totp":
            # In production, look up the user's TOTP secret
            secret = self._totp_secrets.get(user_id, "")
            if secret:
                is_valid = self.verify_totp(secret, code)
        else:
            raise MFAVerificationFailedError(f"Unsupported MFA method: {method}")

        if not is_valid:
            raise MFAVerificationFailedError("MFA verification failed")

        return True