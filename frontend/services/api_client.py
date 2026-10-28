"""API Client for interacting with the FastAPI backend."""

import os
import requests
from typing import Any, Dict, List, Optional, Tuple

BACKEND_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")


class APIClient:
    """Handles all HTTP communication between Streamlit frontend and FastAPI backend."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def health_check(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/api/health", timeout=5)
            return {"success": res.status_code == 200, "data": res.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Authentication ---
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        try:
            res = requests.post(
                f"{self.base_url}/api/auth/register",
                json={"username": username, "email": email, "password": password},
                timeout=10
            )
            if res.status_code == 201:
                return {"success": True, "data": res.json()}
            detail = res.json().get("detail", "Registration failed.")
            return {"success": False, "error": detail}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        try:
            res = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username_or_email": username_or_email, "password": password},
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            detail = res.json().get("detail", "Invalid username or password.")
            return {"success": False, "error": detail}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def get_me(self, token: str) -> Dict[str, Any]:
        try:
            res = requests.get(
                f"{self.base_url}/api/auth/me",
                headers=self._get_headers(token),
                timeout=5
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": "Failed to authenticate session."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Documents ---
    def upload_document(self, file_bytes: bytes, filename: str, token: str) -> Dict[str, Any]:
        try:
            files = {"file": (filename, file_bytes)}
            res = requests.post(
                f"{self.base_url}/api/documents/upload",
                headers=self._get_headers(token),
                files=files,
                timeout=60
            )
            if res.status_code == 201:
                return {"success": True, "data": res.json()}
            detail = res.json().get("detail", "Document upload failed.")
            return {"success": False, "error": detail}
        except Exception as e:
            return {"success": False, "error": f"Upload error: {str(e)}"}

    def list_documents(self, token: str) -> Dict[str, Any]:
        try:
            res = requests.get(
                f"{self.base_url}/api/documents",
                headers=self._get_headers(token),
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Error listing documents")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_document(self, document_id: str, token: str) -> Dict[str, Any]:
        try:
            res = requests.delete(
                f"{self.base_url}/api/documents/{document_id}",
                headers=self._get_headers(token),
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Error deleting document")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Chat & RAG ---
    def ask_question(
        self,
        question: str,
        token: str,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            payload = {
                "question": question,
                "conversation_id": conversation_id,
                "document_ids": document_ids,
                "top_k": top_k
            }
            res = requests.post(
                f"{self.base_url}/api/chat/ask",
                headers=self._get_headers(token),
                json=payload,
                timeout=60
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Failed to retrieve answer.")}
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}

    def list_conversations(self, token: str) -> Dict[str, Any]:
        try:
            res = requests.get(
                f"{self.base_url}/api/chat/history",
                headers=self._get_headers(token),
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Error fetching conversations")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_conversation_history(self, conversation_id: str, token: str) -> Dict[str, Any]:
        try:
            res = requests.get(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self._get_headers(token),
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Error fetching chat history")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_conversation(self, conversation_id: str, token: str) -> Dict[str, Any]:
        try:
            res = requests.delete(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self._get_headers(token),
                timeout=10
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Error deleting conversation")}
        except Exception as e:
            return {"success": False, "error": str(e)}


api_client = APIClient()
