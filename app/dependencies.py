from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

from app.database import get_auth_db
from app.models.user import DjangoUser

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-1s!i5n_7bcf!*%z99^_aqmi#u(gkeo-tqc)n*1^vy_9c4hy(ir")
ALGORITHM = "HS256"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_auth_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Django SimpleJWT encodes user_id as a string (e.g. "1")
        raw_user_id = payload.get("user_id")
        if raw_user_id is None:
            raise credentials_exception
        user_id = int(raw_user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    
    user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(optional_security), db: Session = Depends(get_auth_db)):
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        raw_user_id = payload.get("user_id")
        if raw_user_id is None:
            return None
        user_id = int(raw_user_id)
        return db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    except (JWTError, ValueError, TypeError):
        return None

def require_social_profile(current_user: DjangoUser = Depends(get_current_user)):
    """
    Ensures the authenticated user has created a SocialProfile before proceeding.
    """
    if not current_user.social_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Social profile required. Please complete your profile first."
        )
    return current_user
