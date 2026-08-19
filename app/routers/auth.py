from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt

from app.dependencies import get_current_user, SECRET_KEY, ALGORITHM
from app.models.user import DjangoUser

router = APIRouter(prefix="/auth", tags=["Auth"])

class TokenVerifyRequest(BaseModel):
    token: str

class TokenVerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    detail: Optional[str] = None

@router.get("/verify")
async def verify_user_token(current_user: DjangoUser = Depends(get_current_user)):
    """
    Verifies the JWT Bearer token passed in the Authorization header.
    Returns the authenticated user details if the token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_active": current_user.is_active
    }

@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_raw_token(payload_data: TokenVerifyRequest):
    """
    Verifies a raw JWT token string passed in a JSON body.
    """
    try:
        payload = jwt.decode(payload_data.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("user_id")
        if user_id is None:
            return TokenVerifyResponse(valid=False, detail="Token payload missing user_id")
        return TokenVerifyResponse(
            valid=True,
            user_id=user_id,
            detail="Token signature and payload valid"
        )
    except JWTError as e:
        return TokenVerifyResponse(valid=False, detail=str(e))
