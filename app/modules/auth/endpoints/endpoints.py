from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.core.security import create_access_token
from app.config import settings
from .. import services
from ..db.repository import AuthRepository
from ..models.pydantic_models import User, UserCreate, Token

router = APIRouter()

@router.post("/token", response_model=Token, tags=["Authentication"])
def login_for_access_token(
    db: Session = Depends(get_db_session),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticates a user and returns a JWT token.
    Corresponds to /api/auth/login from PRD.
    """
    user = services.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password, or inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db_session)):
    """
    Creates a new user.
    Corresponds to /api/auth/register from PRD.
    """
    auth_repo = AuthRepository(db)
    db_user = auth_repo.get_by_email(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        return services.create_user(db=db, user=user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
