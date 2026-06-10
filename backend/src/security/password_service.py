"""Password security service using Argon2id.

Provides:
- Password hashing with Argon2id
- Password complexity validation
- Password history checks
- Password reset workflow
- Forced password reset capability

Argon2id is the recommended password hashing algorithm by OWASP.
It provides resistance against both side-channel and GPU-based attacks.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from backend.src.core.settings import settings
from backend.src.core.exceptions import AuthenticationError


class PasswordService:
    """Password hashing and validation service.

    Uses Argon2id with configurable time cost, memory cost, and parallelism.
    Supports password complexity rules, history tracking, and reset workflows.
    """

    def __init__(self) -> None:
        self._ph = PasswordHasher(
            time_cost=settings.ARGON2_TIME_COST,
            memory_cost=settings.ARGON2_MEMORY_COST,
            parallelism=settings.ARGON2_PARALLELISM,
            hash_len=settings.ARGON2_HASH_LEN,
            salt_len=settings.ARGON2_SALT_LEN,
        )
        self._password_history: Dict[str, List[str]] = {}  # user_id -> [hashed_passwords]
        self._reset_tokens: Dict[str, dict] = {}  # token -> metadata

    # ---------------------------------------------------------------------
    # Hashing
    # ---------------------------------------------------------------------
    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2id.

        Args:
            password: The plaintext password.

        Returns:
            The encoded Argon2id hash string.

        Raises:
            ValueError: If password fails complexity validation.
        """
        self.validate_password_complexity(password)
        return self._ph.hash(password)

    def verify_password(self, hashed: str, password: str) -> bool:
        """Verify a password against its Argon2id hash.

        Args:
            hashed: The stored Argon2id hash.
            password: The plaintext password to verify.

        Returns:
            True if the password matches the hash.
        """
        try:
            return self._ph.verify(hashed, password)
        except VerifyMismatchError:
            return False
        except (VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """Check if a password hash needs to be rehashed.

        Returns True if the hash parameters don't match current settings.
        """
        return self._ph.check_needs_rehash(hashed)

    # ---------------------------------------------------------------------
    # Password Complexity Validation
    # ---------------------------------------------------------------------
    def validate_password_complexity(self, password: str) -> bool:
        """Validate password against complexity requirements.

        Args:
            password: The password to validate.

        Returns:
            True if valid.

        Raises:
            ValueError: With details about which requirements failed.
        """
        errors = []

        # Minimum length
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")

        # Uppercase
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Digit
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # Special character
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
            errors.append("Password must contain at least one special character")

        if errors:
            raise ValueError("; ".join(errors))

        return True

    # ---------------------------------------------------------------------
    # Password History
    # ---------------------------------------------------------------------
    def check_password_history(self, user_id: str, new_password: str) -> bool:
        """Check if a new password has been used before.

        Verifies against the last N passwords in the user's history.

        Args:
            user_id: The user identifier.
            new_password: The proposed new password.

        Returns:
            True if the password hasn't been used recently.

        Raises:
            ValueError: If the password was recently used.
        """
        history = self._password_history.get(user_id, [])
        for old_hash in history[-settings.PASSWORD_HISTORY_COUNT:]:
            if self.verify_password(old_hash, new_password):
                raise ValueError(
                    f"Password has been used recently. "
                    f"Cannot reuse the last {settings.PASSWORD_HISTORY_COUNT} passwords."
                )
        return True

    def add_to_password_history(self, user_id: str, hashed_password: str) -> None:
        """Add a password hash to the user's history.

        Maintains only the last N hashes.
        """
        if user_id not in self._password_history:
            self._password_history[user_id] = []
        self._password_history[user_id].append(hashed_password)

        # Trim to history limit
        if len(self._password_history[user_id]) > settings.PASSWORD_HISTORY_COUNT:
            self._password_history[user_id] = (
                self._password_history[user_id][-settings.PASSWORD_HISTORY_COUNT:]
            )

    # ---------------------------------------------------------------------
    # Password Change
    # ---------------------------------------------------------------------
    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        current_hash: str,
    ) -> str:
        """Change a user's password with current password verification.

        Args:
            user_id: The user identifier.
            current_password: The current password for verification.
            new_password: The new password to set.
            current_hash: The stored hash of the current password.

        Returns:
            The new Argon2id hash.

        Raises:
            AuthenticationError: If current password is incorrect.
            ValueError: If new password fails validation.
        """
        # Verify current password
        if not self.verify_password(current_hash, current_password):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        self.validate_password_complexity(new_password)

        # Check password history
        self.check_password_history(user_id, new_password)

        # Hash new password
        new_hash = self.hash_password(new_password)

        # Add to history
        self.add_to_password_history(user_id, new_hash)

        return new_hash

    def force_change_password(self, user_id: str, new_password: str) -> str:
        """Force a password change (admin/reset flow).

        Skips current password verification.

        Args:
            user_id: The user identifier.
            new_password: The new password to set.

        Returns:
            The new Argon2id hash.
        """
        self.validate_password_complexity(new_password)
        self.check_password_history(user_id, new_password)

        new_hash = self.hash_password(new_password)
        self.add_to_password_history(user_id, new_hash)
        return new_hash

    # ---------------------------------------------------------------------
    # Password Reset Flow
    # ---------------------------------------------------------------------
    def generate_reset_token(self, user_id: str) -> str:
        """Generate a secure password reset token.

        Args:
            user_id: The user to generate a reset token for.

        Returns:
            A cryptographically secure reset token.
        """
        token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        from backend.src.core.constants import PASSWORD_RESET_TOKEN_EXPIRE_HOURS

        self._reset_tokens[token_hash] = {
            "user_id": user_id,
            "expires_at": datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp()
                + PASSWORD_RESET_TOKEN_EXPIRE_HOURS * 3600
            ),
            "used": False,
        }
        return token

    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token.

        Args:
            token: The reset token to verify.

        Returns:
            The user_id if the token is valid, None otherwise.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        data = self._reset_tokens.get(token_hash)

        if not data:
            return None

        if data["used"]:
            return None

        if datetime.now(timezone.utc) > data["expires_at"]:
            del self._reset_tokens[token_hash]
            return None

        return data["user_id"]

    def mark_reset_token_used(self, token: str) -> None:
        """Mark a reset token as used (one-time use)."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self._reset_tokens:
            self._reset_tokens[token_hash]["used"] = True

    # ---------------------------------------------------------------------
    # Password Expiration
    # ---------------------------------------------------------------------
    def is_password_expired(self, password_changed_at: Optional[datetime]) -> bool:
        """Check if a password has exceeded its maximum age.

        Args:
            password_changed_at: The datetime when the password was last changed.

        Returns:
            True if the password has expired.
        """
        if not password_changed_at:
            return True

        age = datetime.now(timezone.utc) - password_changed_at
        return age.days >= settings.PASSWORD_MAX_AGE_DAYS