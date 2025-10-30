from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

# --- User Schemas ---

class UserBase(BaseModel):
    """Base Pydantic model for User."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None

class UserCreate(UserBase):
    """Pydantic model for creating a new user."""
    password: str

class User(UserBase):
    """Pydantic model for returning a user (response)."""
    id: uuid.UUID
    role: str
    is_active: bool

    class Config:
        from_attributes = True # Replaces orm_mode = True

# --- Token Schemas ---

class Token(BaseModel):
    """Pydantic model for the JWT token response."""
    access_token: str
    token_type: str = "bearer"
