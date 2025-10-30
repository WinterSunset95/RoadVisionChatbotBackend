from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings
import hashlib

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Pydantic Model for Token Data ---

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Password Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(password_hash, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password_hash)

# --- JWT Token Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """Decodes a JWT token and returns the payload as TokenData."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=str(email))
    except JWTError:
        return None

