from sqlalchemy.orm import Session
from typing import Optional

from ..db.schema import User
from ..db.repository import AuthRepository
from ..security import verify_password
from ..models.pydantic_models import UserCreate

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticates a user by email and password."""
    auth_repo = AuthRepository(db)
    user = auth_repo.get_by_email(email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user

def create_user(db: Session, user: UserCreate) -> User:
    """Creates a new user in the database."""
    auth_repo = AuthRepository(db)
    if not user.email.endswith("@ceigall.com"):
        raise ValueError("Registration is restricted to @ceigall.com email domain only.")
    
    return auth_repo.create(user)
