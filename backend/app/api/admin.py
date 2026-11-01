"""Admin API router for system monitoring, user directory, and document oversight."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_admin_user
from backend.app.schemas.admin import (
    AdminDashboardResponse,
    AdminUserListResponse,
    AdminDocumentListResponse,
    AdminSystemHealthResponse,
)
from backend.app.services.admin_service import admin_service

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Retrieve operational dashboard statistics and recent activity."""
    return admin_service.get_dashboard(db)


@router.get("/users", response_model=AdminUserListResponse)
def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List system users with activity metrics without exposing credentials."""
    users, total = admin_service.get_users(db, skip=skip, limit=limit)
    return AdminUserListResponse(users=users, total=total)


@router.get("/documents", response_model=AdminDocumentListResponse)
def get_admin_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all documents indexed across the entire system."""
    docs, total = admin_service.get_documents(db, skip=skip, limit=limit)
    return AdminDocumentListResponse(documents=docs, total=total)


@router.get("/system-health", response_model=AdminSystemHealthResponse)
def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Audit health and readiness for database, vector store, embeddings, and LLM."""
    return admin_service.get_system_health(db)
