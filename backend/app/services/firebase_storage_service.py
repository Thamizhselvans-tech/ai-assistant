"""Firebase Cloud Storage REST service for AI Knowledge Assistant (ai-agent-7fab4)."""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """Manages document uploads to Firebase Cloud Storage via REST API."""

    def __init__(self):
        self.project_id = getattr(settings, "FIREBASE_PROJECT_ID", "ai-agent-7fab4")
        self.bucket = getattr(settings, "FIREBASE_STORAGE_BUCKET", "ai-agent-7fab4.firebasestorage.app")
        self.base_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket}/o"

    def is_configured(self) -> bool:
        """Check if Firebase storage bucket is configured."""
        return bool(self.bucket and "firebasestorage.app" in self.bucket)

    def upload_file_bytes(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/octet-stream"
    ) -> Optional[Dict[str, Any]]:
        """Upload document bytes to Firebase Storage bucket.

        Returns upload metadata or None on failure (non-blocking fallback).
        """
        if not self.is_configured():
            return None

        clean_path = destination_path.lstrip("/").replace("/", "%2F")
        url = f"{self.base_url}?uploadType=media&name={clean_path}"

        headers = {
            "Content-Type": content_type
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, content=file_bytes, headers=headers)
                if res.status_code in [200, 201]:
                    data = res.json()
                    name = data.get("name", destination_path)
                    token = data.get("downloadTokens", "")
                    download_url = f"{self.base_url}/{clean_path}?alt=media"
                    if token:
                        download_url += f"&token={token}"
                    logger.info(f"Firebase Storage upload successful: {destination_path}")
                    return {
                        "success": True,
                        "name": name,
                        "bucket": self.bucket,
                        "download_url": download_url,
                        "size": data.get("size")
                    }
                else:
                    logger.warning(
                        f"Firebase Storage upload returned HTTP {res.status_code}: {res.text[:200]}"
                    )
                    return None
        except Exception as e:
            logger.warning(f"Firebase Storage upload skipped: {e}")
            return None


firebase_storage = FirebaseStorageService()
