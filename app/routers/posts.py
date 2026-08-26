from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_social_db, get_auth_db
from app.dependencies import get_current_user
from app.models.user import DjangoUser
from app.models.post import Post
from app.models.engagement import Repost, Like
from app.schemas.post import RepostResponse, LikeResponse
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

@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this post")
        
    new_like = Like(post_id=post_id, user_id=current_user.id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    
    return new_like

@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db)
):
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="You have not liked this post")
        
    db.delete(like)
    db.commit()

@router.get("/{post_id}/likes", response_model=List[UserBasicInfo])
async def get_post_likes(
    post_id: int,
    social_db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    post = social_db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    likes = social_db.query(Like).filter(Like.post_id == post_id).all()
    user_ids = [like.user_id for like in likes]
    
    if not user_ids:
        return []
        
    users = auth_db.query(DjangoUser).filter(DjangoUser.id.in_(user_ids)).all()
    return users
