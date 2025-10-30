from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
import uuid

# --- User Schemas ---

class UserBase(BaseModel):
    """Base Pydantic model for User."""
    email: EmailStr
    full_name: str
    employee_id: str
    mobile_number: str
    designation: str
    department: str

class UserCreate(UserBase):
    """Pydantic model for creating a new user."""
    password: str

class User(UserBase):
    """Pydantic model for returning a user (response)."""
    id: uuid.UUID
    role: str
    account_status: str
    model_config = ConfigDict(from_attributes=True)
    is_active: bool

# --- Token Schemas ---

class Token(BaseModel):
    """Pydantic model for the JWT token response."""
    access_token: str
    token_type: str = "bearer"

