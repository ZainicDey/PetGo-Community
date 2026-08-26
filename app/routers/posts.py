from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_social_db, get_auth_db
from app.dependencies import get_current_user
from app.models.user import DjangoUser
from app.models.post import Post
from app.models.engagement import Repost
from app.schemas.post import RepostResponse
from app.schemas.follow import UserBasicInfo

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("/")
async def get_posts():
    return {"message": "Posts endpoint placeholder"}

@router.post("/{post_id}/repost", response_model=RepostResponse)
async def repost_post(
    post_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    existing_repost = db.query(Repost).filter(
        Repost.post_id == post_id,
        Repost.user_id == current_user.id
    ).first()
    
    if existing_repost:
        raise HTTPException(status_code=400, detail="You have already reposted this post")
        
    new_repost = Repost(post_id=post_id, user_id=current_user.id)
    db.add(new_repost)
    db.commit()
    db.refresh(new_repost)
    
    return new_repost

@router.delete("/{post_id}/repost", status_code=status.HTTP_204_NO_CONTENT)
async def unrepost_post(
    post_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db)
):
    repost = db.query(Repost).filter(
        Repost.post_id == post_id,
        Repost.user_id == current_user.id
    ).first()
    
    if not repost:
        raise HTTPException(status_code=404, detail="You have not reposted this post")
        
    db.delete(repost)
    db.commit()

@router.get("/{post_id}/reposters", response_model=List[UserBasicInfo])
async def get_post_reposters(
    post_id: int,
    social_db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    post = social_db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    reposts = social_db.query(Repost).filter(Repost.post_id == post_id).all()
    user_ids = [repost.user_id for repost in reposts]
    
    if not user_ids:
        return []
        
    users = auth_db.query(DjangoUser).filter(DjangoUser.id.in_(user_ids)).all()
    return users
