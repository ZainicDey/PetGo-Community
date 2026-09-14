from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_auth_db
from app.models.user import DjangoUser
from app.schemas.follow import UserBasicInfo

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/users", response_model=List[UserBasicInfo])
async def search_users(q: str, limit: int = 10, db: Session = Depends(get_auth_db)):
    if not q or len(q.strip()) == 0:
        return []
        
    search_query = f"%{q.strip()}%"
    
    users = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(
        DjangoUser.username.ilike(search_query)
    ).limit(limit).all()
    
    return users
