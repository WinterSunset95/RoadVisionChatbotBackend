from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.database import get_db_session
from .db.schema import User
from .db.repository import AuthRepository, TokenBlocklistRepository
from app.core.security import decode_token

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- FastAPI Dependency Injection ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    db: Session = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str | None = payload.get("sub")
    jti: str | None = payload.get("jti")
    if email is None or jti is None:
        raise credentials_exception

    blocklist_repo = TokenBlocklistRepository(db)
    if blocklist_repo.is_token_blocklisted(jti):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    auth_repo = AuthRepository(db)
    user = auth_repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
