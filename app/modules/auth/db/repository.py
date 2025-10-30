from sqlalchemy.orm import Session
from typing import Optional

from .schema import User
from ..models.pydantic_models import UserCreate
from app.core.security import get_password_hash

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user: UserCreate) -> User:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            employee_id=user.employee_id,
            mobile_number=user.mobile_number,
            designation=user.designation,
            department=user.department,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
