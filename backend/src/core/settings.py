"""Application settings module.

This module consolidates configuration values for the TeacherOS backend platform.
It uses **pydantic**'s ``BaseSettings`` to allow loading values from environment
variables, a ``.env`` file or any other settings source supported by ``pydantic``.

Only a subset of settings required for the foundational platform is defined
here. Additional settings can be added later without breaking existing code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pydantic v2 moved ``BaseSettings`` to the ``pydantic_settings`` package.
# Import it with a fallback to maintain compatibility with both versions.
try:
    from pydantic import BaseSettings, Field, PostgresDsn, RedisDsn
except Exception:  # pragma: no cover
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import Field  # type: ignore
    # ``PostgresDsn`` and ``RedisDsn`` were also moved; they are simple subclasses of ``str``.
    class PostgresDsn(str):
        pass

    class RedisDsn(str):
        pass


class Settings(BaseSettings):
    """Global application settings.

    The values are primarily loaded from environment variables. Defaults are
    provided for local development. All values are type‑checked by *pydantic*.
    """

    # ---------------------------------------------------------------------
    # General configuration
    # ---------------------------------------------------------------------
    APP_NAME: str = "TeacherOS"
    DEBUG: bool = Field(False, env="APP_DEBUG")
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field("development", env="APP_ENVIRONMENT")

    # ---------------------------------------------------------------------
    # Database configuration (PostgreSQL)
    # ---------------------------------------------------------------------
    # Provide a sensible default to allow module import without external env vars.
    DATABASE_URL: PostgresDsn = Field(PostgresDsn("postgresql://localhost/teacheros"), env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(40, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_PRE_PING: bool = Field(True, env="DATABASE_POOL_PRE_PING")

    # ---------------------------------------------------------------------
    # Redis configuration (used for Celery broker/cache and other pub/sub)
    # ---------------------------------------------------------------------
    REDIS_URL: RedisDsn = Field(RedisDsn("redis://localhost:6379"), env="REDIS_URL")
    REDIS_TOKEN_BLACKLIST_DB: int = Field(1, env="REDIS_TOKEN_BLACKLIST_DB")
    REDIS_RATE_LIMIT_DB: int = Field(2, env="REDIS_RATE_LIMIT_DB")
    REDIS_SESSION_DB: int = Field(3, env="REDIS_SESSION_DB")
    REDIS_OTP_DB: int = Field(4, env="REDIS_OTP_DB")

    # ---------------------------------------------------------------------
    # JWT configuration
    # ---------------------------------------------------------------------
    JWT_PRIVATE_KEY_PATH: Path = Path(os.getenv("JWT_PRIVATE_KEY_PATH", "./keys/private.pem"))
    JWT_PUBLIC_KEY_PATH: Path = Path(os.getenv("JWT_PUBLIC_KEY_PATH", "./keys/public.pem"))
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ISSUER: str = Field("teacher-os", env="JWT_ISSUER")
    JWT_AUDIENCE: Optional[str] = Field(None, env="JWT_AUDIENCE")
    JWT_LEEWAY_SECONDS: int = Field(30, env="JWT_LEEWAY_SECONDS")

    # ---------------------------------------------------------------------
    # Security configuration
    # ---------------------------------------------------------------------
    # Argon2id password hashing
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 102400
    ARGON2_PARALLELISM: int = 8
    ARGON2_HASH_LEN: int = 32
    ARGON2_SALT_LEN: int = 16

    # Password policy
    PASSWORD_MIN_LENGTH: int = Field(12, env="PASSWORD_MIN_LENGTH")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(True, env="PASSWORD_REQUIRE_UPPERCASE")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(True, env="PASSWORD_REQUIRE_LOWERCASE")
    PASSWORD_REQUIRE_DIGIT: bool = Field(True, env="PASSWORD_REQUIRE_DIGIT")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(True, env="PASSWORD_REQUIRE_SPECIAL")
    PASSWORD_HISTORY_COUNT: int = Field(5, env="PASSWORD_HISTORY_COUNT")
    PASSWORD_MAX_AGE_DAYS: int = Field(90, env="PASSWORD_MAX_AGE_DAYS")

    # MFA
    MFA_EMAIL_OTP_EXPIRE_SECONDS: int = Field(300, env="MFA_EMAIL_OTP_EXPIRE_SECONDS")
    MFA_TOTP_ISSUER: str = Field("TeacherOS", env="MFA_TOTP_ISSUER")
    MFA_TOTP_VALIDITY_WINDOW: int = Field(1, env="MFA_TOTP_VALIDITY_WINDOW")

    # Encryption
    ENCRYPTION_KEY: Optional[str] = Field(None, env="ENCRYPTION_KEY")
    ENCRYPTION_ALGORITHM: str = Field("AES-256-GCM", env="ENCRYPTION_ALGORITHM")

    # ---------------------------------------------------------------------
    # CORS configuration
    # ---------------------------------------------------------------------
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:5173", "http://localhost:8000"],
        env="CORS_ALLOWED_ORIGINS",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: List[str] = Field(
        ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS",
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        ["Authorization", "Content-Type", "X-Tenant-Id", "X-Request-Id", "X-CSRF-Token"],
        env="CORS_ALLOW_HEADERS",
    )
    CORS_EXPOSE_HEADERS: List[str] = Field(
        ["X-Request-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        env="CORS_EXPOSE_HEADERS",
    )

    # ---------------------------------------------------------------------
    # Rate Limiting (SlowAPI)
    # ---------------------------------------------------------------------
    RATE_LIMIT_PUBLIC_REQUESTS: int = Field(10, env="RATE_LIMIT_PUBLIC_REQUESTS")
    RATE_LIMIT_PUBLIC_WINDOW_SECONDS: int = Field(60, env="RATE_LIMIT_PUBLIC_WINDOW_SECONDS")
    RATE_LIMIT_AUTH_REQUESTS: int = Field(100, env="RATE_LIMIT_AUTH_REQUESTS")
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = Field(60, env="RATE_LIMIT_AUTH_WINDOW_SECONDS")
    RATE_LIMIT_AI_REQUESTS: int = Field(20, env="RATE_LIMIT_AI_REQUESTS")
    RATE_LIMIT_AI_WINDOW_SECONDS: int = Field(60, env="RATE_LIMIT_AI_WINDOW_SECONDS")
    RATE_LIMIT_LOGIN_REQUESTS: int = Field(5, env="RATE_LIMIT_LOGIN_REQUESTS")
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(300, env="RATE_LIMIT_LOGIN_WINDOW_SECONDS")

    # ---------------------------------------------------------------------
    # File Upload Security
    # ---------------------------------------------------------------------
    FILE_UPLOAD_MAX_SIZE_MB: int = Field(10, env="FILE_UPLOAD_MAX_SIZE_MB")
    FILE_UPLOAD_ALLOWED_EXTENSIONS: List[str] = Field(
        ["pdf", "docx", "xlsx", "png", "jpeg", "jpg"],
        env="FILE_UPLOAD_ALLOWED_EXTENSIONS",
    )
    FILE_UPLOAD_ALLOWED_MIME_TYPES: List[str] = Field(
        [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/png",
            "image/jpeg",
        ],
        env="FILE_UPLOAD_ALLOWED_MIME_TYPES",
    )
    FILE_UPLOAD_SCAN_ENABLED: bool = Field(False, env="FILE_UPLOAD_SCAN_ENABLED")

    # ---------------------------------------------------------------------
    # Tenant configuration
    # ---------------------------------------------------------------------
    TENANT_HEADER_NAME: str = Field("X-Tenant-Id", env="TENANT_HEADER_NAME")
    TENANT_DEFAULT: str = Field("default", env="TENANT_DEFAULT")
    TENANT_ORGANIZATION_HEADER: str = Field("X-Organization-Id", env="TENANT_ORGANIZATION_HEADER")
    TENANT_SCHOOL_HEADER: str = Field("X-School-Id", env="TENANT_SCHOOL_HEADER")

    # ---------------------------------------------------------------------
    # Audit Logging
    # ---------------------------------------------------------------------
    AUDIT_LOG_RETENTION_DAYS: int = Field(365, env="AUDIT_LOG_RETENTION_DAYS")
    AUDIT_LOG_APPEND_ONLY: bool = Field(True, env="AUDIT_LOG_APPEND_ONLY")
    AUDIT_LOG_TABLE: str = Field("audit_logs", env="AUDIT_LOG_TABLE")

    # ---------------------------------------------------------------------
    # AI Security
    # ---------------------------------------------------------------------
    AI_MAX_INPUT_LENGTH: int = Field(100000, env="AI_MAX_INPUT_LENGTH")
    AI_OUTPUT_FILTER_ENABLED: bool = Field(True, env="AI_OUTPUT_FILTER_ENABLED")
    AI_PROMPT_INJECTION_DETECTION_ENABLED: bool = Field(True, env="AI_PROMPT_INJECTION_DETECTION_ENABLED")
    AI_CROSS_TENANT_CONTEXT_CHECK: bool = Field(True, env="AI_CROSS_TENANT_CONTEXT_CHECK")
    AI_MAX_TOOL_CALLS_PER_RUN: int = Field(50, env="AI_MAX_TOOL_CALLS_PER_RUN")

    # ---------------------------------------------------------------------
    # Data Retention / Compliance
    # ---------------------------------------------------------------------
    DATA_RETENTION_STUDENT_RECORDS_YEARS: int = Field(5, env="DATA_RETENTION_STUDENT_RECORDS_YEARS")
    DATA_RETENTION_AUDIT_LOGS_YEARS: int = Field(3, env="DATA_RETENTION_AUDIT_LOGS_YEARS")
    DATA_RETENTION_SESSION_LOGS_DAYS: int = Field(90, env="DATA_RETENTION_SESSION_LOGS_DAYS")
    DATA_RETENTION_AI_INTERACTION_LOGS_DAYS: int = Field(180, env="DATA_RETENTION_AI_INTERACTION_LOGS_DAYS")

    # ---------------------------------------------------------------------
    # Observability configuration
    # ---------------------------------------------------------------------
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field("http://localhost:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    PROMETHEUS_METRICS_PORT: int = Field(8000, env="PROMETHEUS_METRICS_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            """Add a JSON file source if it exists.

            This allows providing a ``settings.json`` for local development
            while still keeping the primary source as environment variables.
            """

            def json_config_settings(settings: BaseSettings) -> Dict[str, Any]:
                cfg_path = Path("settings.json")
                if cfg_path.is_file():
                    import json

                    with cfg_path.open() as f:
                        return json.load(f)
                return {}

            return init_settings, env_settings, json_config_settings, file_secret_settings


# A singleton instance that can be imported throughout the project.
settings = Settings()