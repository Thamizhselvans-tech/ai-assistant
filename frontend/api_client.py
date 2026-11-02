"""Centralized HTTP API client for communication between Streamlit frontend and FastAPI backend."""

import os
import requests
from typing import Any, Dict, List, Optional
from frontend.config import BACKEND_API_URL


class APIClient:
    """Manages all HTTP communication, token authentication, and error handling with FastAPI."""

    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _handle_response(self, res: requests.Response) -> Dict[str, Any]:
        """Safely decode JSON response and standardize return structure."""
        try:
            data = res.json()
        except Exception:
            data = {"detail": res.text}

        if 200 <= res.status_code < 300:
            return {"success": True, "status_code": res.status_code, "data": data}
        
        detail = data.get("detail", "An unexpected server error occurred.") if isinstance(data, dict) else str(data)
        return {"success": False, "status_code": res.status_code, "error": detail}

    # =========================================================================
    # System Health
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check status of backend server and attached services."""
        try:
            res = requests.get(f"{self.base_url}/api/health", timeout=5)
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"Cannot connect to backend server: {str(e)}"}

    # =========================================================================
    # Authentication APIs
    # =========================================================================

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user account."""
        try:
            res = requests.post(
                f"{self.base_url}/api/auth/register",
                json={"username": username.strip(), "email": email.strip(), "password": password},
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and obtain access and refresh JWT tokens."""
        try:
            res = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username_or_email": username_or_email.strip(), "password": password},
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Exchange refresh token for a newly generated token pair."""
        try:
            res = requests.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": refresh_token},
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def get_me(self, token: str) -> Dict[str, Any]:
        """Retrieve profile of authenticated user."""
        try:
            res = requests.get(
                f"{self.base_url}/api/auth/me",
                headers=self._headers(token),
                timeout=5
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Document Management APIs
    # =========================================================================

    def upload_document(self, file_bytes: bytes, filename: str, token: str) -> Dict[str, Any]:
        """Upload and index a document via multipart form data."""
        try:
            files = {"file": (filename, file_bytes)}
            res = requests.post(
                f"{self.base_url}/api/documents/upload",
                headers=self._headers(token),
                files=files,
                timeout=120
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}

    def list_documents(self, token: str) -> Dict[str, Any]:
        """List all documents owned by current authenticated user."""
        try:
            res = requests.get(
                f"{self.base_url}/api/documents",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_document(self, document_id: str, token: str) -> Dict[str, Any]:
        """Get details for a specific document."""
        try:
            res = requests.get(
                f"{self.base_url}/api/documents/{document_id}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_document(self, document_id: str, token: str) -> Dict[str, Any]:
        """Delete document, ChromaDB vector records, and physical file."""
        try:
            res = requests.delete(
                f"{self.base_url}/api/documents/{document_id}",
                headers=self._headers(token),
                timeout=15
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # AI Chat & RAG APIs
    # =========================================================================

    def ask_question(
        self,
        question: str,
        token: str,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send a natural language question to the RAG QA engine."""
        try:
            payload: Dict[str, Any] = {"question": question.strip()}
            if conversation_id:
                payload["conversation_id"] = conversation_id
            if document_ids:
                payload["document_ids"] = document_ids
            if top_k:
                payload["top_k"] = top_k
            if similarity_threshold is not None:
                payload["similarity_threshold"] = similarity_threshold

            res = requests.post(
                f"{self.base_url}/api/chat/ask",
                headers=self._headers(token),
                json=payload,
                timeout=60
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": f"QA execution failed: {str(e)}"}

    def list_conversations(self, token: str, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List paginated previous chat conversations for authenticated user."""
        try:
            res = requests.get(
                f"{self.base_url}/api/chat/history?skip={skip}&limit={limit}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_conversation_history(self, conversation_id: str, token: str) -> Dict[str, Any]:
        """Retrieve full threaded messages and citations for a conversation."""
        try:
            res = requests.get(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_conversation(self, conversation_id: str, token: str) -> Dict[str, Any]:
        """Delete a conversation and its messages."""
        try:
            res = requests.delete(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Admin APIs
    # =========================================================================

    def get_admin_dashboard(self, token: str) -> Dict[str, Any]:
        """Retrieve aggregated system metrics (Admin only)."""
        try:
            res = requests.get(
                f"{self.base_url}/api/admin/dashboard",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_admin_users(self, token: str, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List system users with activity statistics (Admin only)."""
        try:
            res = requests.get(
                f"{self.base_url}/api/admin/users?skip={skip}&limit={limit}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_admin_documents(self, token: str, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List all indexed documents across the system (Admin only)."""
        try:
            res = requests.get(
                f"{self.base_url}/api/admin/documents?skip={skip}&limit={limit}",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_admin_system_health(self, token: str) -> Dict[str, Any]:
        """Audit health of database, vector store, embedding model, and LLM (Admin only)."""
        try:
            res = requests.get(
                f"{self.base_url}/api/admin/system-health",
                headers=self._headers(token),
                timeout=10
            )
            return self._handle_response(res)
        except Exception as e:
            return {"success": False, "error": str(e)}


api_client = APIClient()

__all__ = ["APIClient", "api_client"]
