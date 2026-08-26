from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_auth_db, get_social_db
from app.models.user import DjangoUser, SocialProfile
from app.models.post import Post
from app.models.engagement import Repost, Like
from app.schemas.user import ProfileCreate, ProfileResponse
from app.schemas.post import PostResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/profile", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    # Check if username is taken by someone else
    existing_user = db.query(DjangoUser).filter(
        DjangoUser.username == profile_data.username,
        DjangoUser.id != current_user.id
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check if user already has a profile
    if current_user.social_profile:
        raise HTTPException(status_code=400, detail="User already has a profile")
    
    # Update Django User username
    current_user.username = profile_data.username
    
    # Create the SocialProfile
    new_profile = SocialProfile(
        user_id=current_user.id,
        profile_type=profile_data.profile_type,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return {
        "id": new_profile.id,
        "user_id": new_profile.user_id,
        "profile_type": new_profile.profile_type,
        "gender": new_profile.gender,
        "date_of_birth": new_profile.date_of_birth,
        "username": current_user.username
    }

@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    if not current_user.social_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile = current_user.social_profile
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "profile_type": profile.profile_type,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "username": current_user.username
    }

from typing import List
from app.models.follow import Follow
from app.schemas.follow import FollowResponse, UserBasicInfo

@router.post("/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
        
    target_user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="You are already following this user")
        
    new_follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)
    
    return new_follow

@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if not follow:
        raise HTTPException(status_code=404, detail="You are not following this user")
        
    db.delete(follow)
    db.commit()

@router.get("/{user_id}/followers", response_model=List[UserBasicInfo])
async def get_followers(
    user_id: int,
    db: Session = Depends(get_auth_db)
):
    user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    followers = db.query(DjangoUser).join(
        Follow, Follow.follower_id == DjangoUser.id
    ).filter(
        Follow.following_id == user_id
    ).all()
    
    return followers

@router.get("/{user_id}/following", response_model=List[UserBasicInfo])
async def get_following(
    user_id: int,
    db: Session = Depends(get_auth_db)
):
    user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    following = db.query(DjangoUser).join(
        Follow, Follow.following_id == DjangoUser.id
    ).filter(
        Follow.follower_id == user_id
    ).all()
    
    return following

@router.get("/{user_id}/reposts", response_model=List[PostResponse])
async def get_user_reposts(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    reposts = social_db.query(Repost).filter(Repost.user_id == user_id).all()
    post_ids = [repost.post_id for repost in reposts]
    
    if not post_ids:
        return []
        
    posts = social_db.query(Post).filter(Post.id.in_(post_ids)).all()
    return posts

@router.get("/{user_id}/likes", response_model=List[PostResponse])
async def get_user_likes(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    likes = social_db.query(Like).filter(Like.user_id == user_id).all()
    post_ids = [like.post_id for like in likes]
    
    if not post_ids:
        return []
        
    posts = social_db.query(Post).filter(Post.id.in_(post_ids)).all()
    return posts
