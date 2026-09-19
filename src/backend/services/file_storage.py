"""
File Storage Service for Threat Intelligence Alert Uploads.

Handles secure disk persistence, directory management, and file validation.
Does NOT parse CSV data or read rows.
"""

import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Configure base uploads directory relative to backend root
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"


class StorageValidationError(Exception):
    """Custom exception raised when file fails validation criteria."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FileStorageService:
    """Service responsible for validating and persisting alert CSV files."""

    def __init__(self, upload_dir: Path = UPLOADS_DIR):
        self.upload_dir = upload_dir
        self._ensure_upload_dir_exists()

    def _ensure_upload_dir_exists(self) -> None:
        """Ensure the uploads storage directory exists on disk."""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.critical(f"Failed to create uploads directory at {self.upload_dir}: {exc}")
            raise

    def generate_filename(self, extension: str = ".csv") -> str:
        """
        Generates a unique timestamp-based filename.
        Format: alerts_YYYYMMDD_HHMMSS.csv (with microsecond/hex suffix if conflict arises).
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        base_name = f"alerts_{timestamp}"
        candidate = f"{base_name}{extension}"

        target_path = self.upload_dir / candidate
        # Prevent collisions if multiple uploads arrive within the same second
        if target_path.exists():
            short_id = uuid.uuid4().hex[:6]
            candidate = f"{base_name}_{short_id}{extension}"

        return candidate

    def validate_file_extension(self, upload_file: UploadFile) -> None:
        """
        Validates that the file has a .csv extension.
        Rejects all non-CSV files (.txt, .pdf, .xlsx, .json, etc.).
        """
        if not upload_file or not upload_file.filename:
            logger.warning("Upload rejected: missing file or filename")
            raise StorageValidationError("File is missing or has no name")

        filename = upload_file.filename.strip()
        _, ext = os.path.splitext(filename)

        if ext.lower() != ".csv":
            logger.warning(
                f"Upload rejected: invalid file extension '{ext}' for file '{filename}'. Only .csv allowed."
            )
            raise StorageValidationError("Only CSV files are allowed")

    async def save_file(self, upload_file: UploadFile) -> Tuple[str, str]:
        """
        Stream-saves the uploaded file into the uploads directory.
        Verifies the file is not empty without parsing its content.

        Returns:
            Tuple[str, str]: (generated_file_name, relative_file_path)
        """
        self.validate_file_extension(upload_file)

        return await self._save_file(upload_file, ".csv")

    async def save_json_file(self, upload_file: UploadFile) -> Tuple[str, str]:
        """Persist a JSON alert feed without changing CSV upload validation."""
        if not upload_file or not upload_file.filename or not upload_file.filename.lower().endswith(".json"):
            raise StorageValidationError("Only JSON files are allowed")
        return await self._save_file(upload_file, ".json")

    async def _save_file(self, upload_file: UploadFile, extension: str) -> Tuple[str, str]:
        """Shared streaming implementation for already validated upload types."""

        generated_filename = self.generate_filename(extension)
        destination_path = self.upload_dir / generated_filename
        relative_path = f"uploads/{generated_filename}"

        logger.info(
            f"Upload started: client_file='{upload_file.filename}', target='{destination_path}'"
        )

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunks for memory-efficient streaming

        try:
            with open(destination_path, "wb") as buffer:
                while True:
                    chunk = await upload_file.read(chunk_size)
                    if not chunk:
                        break
                    buffer.write(chunk)
                    total_bytes += len(chunk)

            # Check if file is empty
            if total_bytes == 0:
                logger.warning(
                    f"Upload failed: file '{upload_file.filename}' is empty (0 bytes). Cleaning up."
                )
                if destination_path.exists():
                    destination_path.unlink()
                raise StorageValidationError("Uploaded file is empty")

            logger.info(
                f"Upload completed successfully: file='{generated_filename}', size={total_bytes} bytes, path='{relative_path}'"
            )
            return generated_filename, relative_path

        except StorageValidationError:
            # Re-raise explicit validation errors
            raise

        except Exception as exc:
            logger.error(
                f"Upload failed due to unexpected error while writing '{generated_filename}': {exc}",
                exc_info=True,
            )
            if destination_path.exists():
                try:
                    destination_path.unlink()
                except Exception:
                    pass
            raise
