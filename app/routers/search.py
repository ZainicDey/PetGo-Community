from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, cast

from app.database import get_auth_db, get_social_db
from app.models.user import DjangoUser
from app.schemas.follow import UserBasicInfo
from app.schemas.post import PostResponse
from app.models.post import Post
from app.dependencies import get_optional_current_user
from app.utils.user import attach_authors
from app.utils.engagement import attach_user_engagements

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/users", response_model=List[UserBasicInfo])
async def search_users(
    q: str, 
    limit: int = 10, 
    offset: int = 0, 
    db: Session = Depends(get_auth_db)
):
    if not q or len(q.strip()) == 0:
        return []
        
    search_query = f"%{q.strip()}%"
    
    users = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(
        DjangoUser.username.ilike(search_query)
    ).limit(limit).offset(offset).all()
    
    return users

@router.get("/posts", response_model=List[PostResponse])
async def search_posts(
    q: str,
    limit: int = 20,
    offset: int = 0,
    social_db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    if not q or len(q.strip()) == 0:
        return []
        
    search_query = f"%{q.strip()}%"
    
    posts = social_db.query(Post).options(joinedload(Post.quoted_post)).filter(
        Post.content.ilike(search_query)
    ).order_by(Post.created_at.desc()).limit(limit).offset(offset).all()
    
    if not posts:
        return []
        
    user_id = cast(int, optional_user.id) if optional_user else None
    
    posts = attach_user_engagements(posts, user_id, social_db)
    return attach_authors(posts, auth_db, user_id)
