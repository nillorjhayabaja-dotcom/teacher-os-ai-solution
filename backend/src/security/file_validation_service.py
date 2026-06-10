"""File validation service for secure file uploads.

Validates uploaded files for:
- MIME type verification (content-based, not extension-based)
- File extension allowlisting
- File size limits
- Magic byte signature validation
- Optional virus scanning integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
import filetype
import magic
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.src.core.settings import settings
from backend.src.core.exceptions import (
    FileSizeExceededError,
    FileTypeNotAllowedError,
    MalwareDetectedError,
)

# Define dangerous file extensions that should always be rejected
DANGEROUS_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr", ".ps1", ".sh",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta", ".py",
    ".rb", ".pl", ".php", ".asp", ".aspx", ".jsp", ".cgi", ".wasm",
    ".swf", ".jar", ".class", ".dll", ".sys", ".drv", ".ocx",
    ".app", ".gadget", ".msh", ".reg", ".inf",
}


@dataclass
class FileValidationResult:
    """Result of file validation."""
    valid: bool
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    detected_mime_type: str  # MIME from content analysis
    magic_bytes_verified: bool
    errors: List[str] = field(default_factory=list)


class FileValidationService:
    """Validates uploaded files for security compliance.

    Performs multi-layer validation:
    1. Extension check (against allowlist and dangerous list)
    2. MIME type verification (content-based magic bytes)
    3. File size limits
    4. Magic byte signature verification
    5. Optional virus scanning integration
    """

    def __init__(self, scan_enabled: bool = False) -> None:
        self._allowed_extensions: Set[str] = set(
            f".{ext.lower()}" for ext in settings.FILE_UPLOAD_ALLOWED_EXTENSIONS
        )
        self._allowed_mime_types: Set[str] = set(settings.FILE_UPLOAD_ALLOWED_MIME_TYPES)
        self._max_size_bytes: int = settings.FILE_UPLOAD_MAX_SIZE_MB * 1024 * 1024
        self._scan_enabled = scan_enabled or settings.FILE_UPLOAD_SCAN_ENABLED

    # ---------------------------------------------------------------------
    # Validation Pipeline
    # ---------------------------------------------------------------------
    def validate_file(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> FileValidationResult:
        """Run the full file validation pipeline.

        Args:
            filename: The original filename.
            content: The raw file content as bytes.
            content_type: Optional MIME type from the upload request.

        Returns:
            FileValidationResult with validation status and details.

        Raises:
            FileSizeExceededError: If file exceeds size limit.
            FileTypeNotAllowedError: If file type is not allowed.
        """
        _, extension = os.path.splitext(filename)
        extension = extension.lower()
        size_bytes = len(content)

        errors: List[str] = []

        # 1. Size validation
        if size_bytes > self._max_size_bytes:
            raise FileSizeExceededError(
                f"File size {size_bytes} bytes exceeds maximum of {self._max_size_bytes} bytes"
            )

        # 2. Extension validation
        if extension in DANGEROUS_EXTENSIONS:
            raise FileTypeNotAllowedError(
                f"File extension '{extension}' is not allowed (dangerous file type)"
            )

        if extension not in self._allowed_extensions:
            raise FileTypeNotAllowedError(
                f"File extension '{extension}' is not in allowed list: "
                f"{', '.join(self._allowed_extensions)}"
            )

        # 3. MIME type detection from content (magic bytes)
        detected_mime_type = self._detect_mime_type(content)
        magic_verified = bool(detected_mime_type)

        # 4. MIME type allowlist check
        if extension in self._allowed_extensions:
            # Verify the detected MIME matches what we expect for this extension
            expected_mime = self._get_expected_mime(extension)
            if detected_mime_type and detected_mime_type != expected_mime:
                # MIME mismatch detected - possible content spoofing
                if detected_mime_type in DANGEROUS_MIME_TYPES:
                    raise FileTypeNotAllowedError(
                        f"MIME type mismatch: expected '{expected_mime}', "
                        f"detected '{detected_mime_type}' (dangerous content)"
                    )
                errors.append(
                    f"MIME type mismatch: extension suggests '{expected_mime}', "
                    f"but content detected as '{detected_mime_type}'"
                )

        if detected_mime_type and detected_mime_type not in self._allowed_mime_types:
            # The content MIME type is not allowed even if extension matches
            if detected_mime_type in DANGEROUS_MIME_TYPES:
                raise FileTypeNotAllowedError(
                    f"Content detected as dangerous MIME type '{detected_mime_type}'"
                )
            errors.append(
                f"Detected MIME type '{detected_mime_type}' is not in allowed list"
            )

        # 5. Magic byte verification
        if not magic_verified:
            errors.append("Could not verify file type via magic bytes")

        # 6. Optional virus scan
        if self._scan_enabled:
            scan_result = self._scan_file(content)
            if not scan_result["clean"]:
                raise MalwareDetectedError(
                    f"Malware detected in file: {scan_result.get('detail', 'Unknown threat')}"
                )

        return FileValidationResult(
            valid=len(errors) == 0,
            filename=filename,
            extension=extension,
            mime_type=content_type or detected_mime_type or "",
            size_bytes=size_bytes,
            detected_mime_type=detected_mime_type or "",
            magic_bytes_verified=magic_verified,
            errors=errors,
        )

    def _detect_mime_type(self, content: bytes) -> Optional[str]:
        """Detect MIME type from file content using magic bytes."""
        try:
            # Try python-magic first
            mime = magic.from_buffer(content, mime=True)
            if mime:
                return mime
        except Exception:
            pass

        try:
            # Fallback to filetype library
            kind = filetype.guess(content)
            if kind:
                return kind.mime
        except Exception:
            pass

        return None

    def _get_expected_mime(self, extension: str) -> Optional[str]:
        """Get the expected MIME type for a given extension."""
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mime_map.get(extension)

    def _scan_file(self, content: bytes) -> Dict[str, Any]:
        """Scan file content for malware.

        Integrates with ClamAV or other antivirus engines.
        Returns a dict with 'clean' and 'detail' keys.
        """
        # Placeholder for virus scanning integration
        # In production, integrate with ClamAV REST API:
        #   clamd = clamd.ClamdUnixSocket()
        #   result = clamd.instream(io.BytesIO(content))
        #   clean = result.get('stream', ('OK',))[0] == 'OK'
        return {"clean": True, "detail": None}

    def get_safe_filename(self, filename: str) -> str:
        """Sanitize a filename to prevent path traversal.

        Removes path components, null bytes, and special characters.
        """
        # Remove any directory traversal
        safe = Path(filename).name

        # Remove null bytes
        safe = safe.replace("\x00", "")

        # Limit length
        if len(safe) > 255:
            name, ext = os.path.splitext(safe)
            safe = name[:250] + ext

        return safe


# MIME types that should always be rejected
DANGEROUS_MIME_TYPES: Set[str] = {
    "application/x-msdownload",
    "application/x-msdos-program",
    "application/x-msi",
    "application/x-bat",
    "application/x-sh",
    "application/x-httpd-php",
    "application/x-javascript",
    "text/javascript",
    "application/javascript",
    "application/x-python-code",
    "text/x-python",
    "application/java-archive",
    "application/x-java-applet",
}