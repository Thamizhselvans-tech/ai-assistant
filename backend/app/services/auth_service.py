"""Authentication and user management business logic."""

from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.security import hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import UserRegisterRequest


class AuthService:
    """Handles user creation, lookup, and credential verification."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username.strip()).first()

    @classmethod
    def register_user(
        cls,
        db: Session,
        req: UserRegisterRequest,
        is_admin: bool = False,
        role: str = "user"
    ) -> User:
        # Check uniqueness
        if cls.get_by_email(db, req.email):
            raise ValueError("A user with this email address already exists.")
        if cls.get_by_username(db, req.username):
            raise ValueError("A user with this username already exists.")

        user = User(
            email=req.email.lower().strip(),
            username=req.username.strip(),
            hashed_password=hash_password(req.password),
            is_active=True,
            is_admin=is_admin,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def authenticate_user(cls, db: Session, username_or_email: str, password: str) -> Optional[User]:
        identifier = username_or_email.strip()
        user = cls.get_by_email(db, identifier) or cls.get_by_username(db, identifier)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


auth_service = AuthService()
