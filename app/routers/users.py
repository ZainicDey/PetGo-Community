from fastapi import APIRouter, Depends, HTTPException, status
from typing import cast, Optional, List
from sqlalchemy.orm import Session, joinedload

from app.database import get_auth_db, get_social_db
from app.models.user import DjangoUser, SocialProfile, ProfileLink
from app.models.post import Post
from app.models.engagement import Repost, Like, Comment, SavedPost
from app.schemas.user import (
    ProfileCreate, ProfileUpdate, ProfileResponse, UserMeResponse, 
    UsernameCheckRequest, UsernameCheckResponse, ActivityItem,
    PetProfileCreate, SwitchableProfile, SwitchableProfilesResponse, 
    SwitchProfileRequest, SwitchProfileResponse, SwitchProfileUser
)
from app.schemas.post import PostResponse
from app.dependencies import get_current_user, require_social_profile, get_optional_current_user, SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta
from jose import jwt
from app.utils.user import attach_authors
from app.utils.engagement import attach_user_engagements
from app.utils.media import delete_post_media_files, delete_cloudinary_media, parse_cloudinary_url
from app.models.follow import Follow

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: DjangoUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "has_social_profile": current_user.social_profile is not None
    }

@router.post("/check-username", response_model=UsernameCheckResponse)
async def check_username(
    request: UsernameCheckRequest,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    exists = db.query(DjangoUser).filter(DjangoUser.username == request.username).first() is not None
    return {"exists": exists, "available": not exists}

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
        date_of_birth=profile_data.date_of_birth,
        profile_picture_url=profile_data.profile_picture_url
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    follower_count = db.query(Follow).filter(Follow.following_id == current_user.id).count()
    
    return {
        "id": new_profile.id,
        "user_id": new_profile.user_id,
        "profile_type": new_profile.profile_type,
        "gender": new_profile.gender,
        "date_of_birth": new_profile.date_of_birth,
        "username": current_user.username,
        "profile_picture_url": new_profile.profile_picture_url,
        "follower_count": follower_count
    }

@router.delete("/pet-profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet_profile(
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db)
):
    if not current_user.social_profile or current_user.social_profile.profile_type != "pet":
        raise HTTPException(status_code=403, detail="Only a pet profile can delete itself")
        
    pet_user = db.query(DjangoUser).filter(DjangoUser.id == current_user.id).first()
    if pet_user:
        # Fetch user's posts to delete their media from Cloudinary
        user_posts = social_db.query(Post).filter(Post.author_id == current_user.id).all()
        for post in user_posts:
            if post.media:
                delete_post_media_files(cast(List[dict], post.media))
                
        # Fetch user's comments to delete their media from Cloudinary
        user_comments = social_db.query(Comment).filter(Comment.author_id == current_user.id).all()
        for comment in user_comments:
            if comment.image_url:
                parsed = parse_cloudinary_url(comment.image_url)
                if parsed and parsed.get("public_id"):
                    delete_cloudinary_media(parsed["public_id"], parsed.get("media_type") or "image")

        # Delete social data from social_db
        # We delete from Like, Repost, Comment, and Post where the user is the author.
        # Note: Deleting Post will cascade-delete its Comments, Likes, and Reposts in social_db,
        # but we also need to delete the user's engagement on other people's posts.
        social_db.query(Like).filter(Like.user_id == current_user.id).delete(synchronize_session=False)
        social_db.query(Repost).filter(Repost.user_id == current_user.id).delete(synchronize_session=False)
        social_db.query(SavedPost).filter(SavedPost.user_id == current_user.id).delete(synchronize_session=False)
        social_db.query(Comment).filter(Comment.author_id == current_user.id).delete(synchronize_session=False)
        social_db.query(Post).filter(Post.author_id == current_user.id).delete(synchronize_session=False)
        social_db.commit()

        # Delete auth user (cascades to profile, links, and follows)
        db.query(DjangoUser).filter(DjangoUser.id == current_user.id).delete(synchronize_session=False)
        db.commit()

@router.post("/pet-profile", response_model=ProfileResponse)
async def create_pet_profile(
    profile_data: PetProfileCreate,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_auth_db)
):
    # Determine the actual owner
    owner_id = current_user.id
    if current_user.social_profile and current_user.social_profile.profile_type == "pet":
        # Current user is a pet, find the owner
        link = db.query(ProfileLink).filter(ProfileLink.pet_user_id == current_user.id).first()
        if not link:
            raise HTTPException(status_code=500, detail="Pet profile is not linked to an owner")
        owner_id = link.owner_user_id

    # Check if username is taken
    existing_user = db.query(DjangoUser).filter(DjangoUser.username == profile_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create shadow DjangoUser
    new_user = DjangoUser(
        username=profile_data.username,
        password="!", # Unusable password
        first_name="",
        last_name="",
        email=f"{profile_data.username}@pet.local",
        is_superuser=False,
        is_staff=False,
        is_active=True,
        date_joined=datetime.utcnow()
    )
    db.add(new_user)
    db.flush()

    # Create SocialProfile
    new_profile = SocialProfile(
        user_id=new_user.id,
        profile_type="pet",
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        profile_picture_url=profile_data.profile_picture_url
    )
    db.add(new_profile)

    # Create ProfileLink
    new_link = ProfileLink(
        owner_user_id=owner_id,
        pet_user_id=new_user.id
    )
    db.add(new_link)
    
    db.commit()
    db.refresh(new_profile)

    return {
        "id": new_profile.id,
        "user_id": new_profile.user_id,
        "profile_type": new_profile.profile_type,
        "gender": new_profile.gender,
        "date_of_birth": new_profile.date_of_birth,
        "username": new_user.username,
        "profile_picture_url": new_profile.profile_picture_url,
        "follower_count": 0
    }

@router.get("/switchable-profiles", response_model=SwitchableProfilesResponse)
async def get_switchable_profiles(
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_auth_db)
):
    # Determine the actual owner
    owner_id = cast(int, current_user.id)
    if current_user.social_profile and current_user.social_profile.profile_type == "pet":
        link = db.query(ProfileLink).filter(ProfileLink.pet_user_id == current_user.id).first()
        if link:
            owner_id = cast(int, link.owner_user_id)

    # Fetch owner
    owner = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id == owner_id).first()
    if not owner or not owner.social_profile:
        raise HTTPException(status_code=404, detail="Owner profile not found")

    # Fetch pets
    links = db.query(ProfileLink).filter(ProfileLink.owner_user_id == owner_id).all()
    pet_ids = [l.pet_user_id for l in links]
    pets = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id.in_(pet_ids)).all() if pet_ids else []

    profiles = []
    # Add owner
    profiles.append(SwitchableProfile(
        user_id=cast(int, owner.id),
        username=cast(str, owner.username),
        profile_type=cast(str, owner.social_profile.profile_type),
        profile_picture_url=owner.social_profile.profile_picture_url,
        is_owner=True
    ))

    # Add pets
    for pet in pets:
        if pet.social_profile:
            profiles.append(SwitchableProfile(
                user_id=cast(int, pet.id),
                username=cast(str, pet.username),
                profile_type=cast(str, pet.social_profile.profile_type),
                profile_picture_url=pet.social_profile.profile_picture_url,
                is_owner=False
            ))

    return SwitchableProfilesResponse(
        active_profile_id=cast(int, current_user.id),
        profiles=profiles
    )

@router.post("/switch-profile", response_model=SwitchProfileResponse)
async def switch_profile(
    request: SwitchProfileRequest,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_auth_db)
):
    # Verify the target user belongs to the same owner group
    target_user_id = request.target_user_id
    
    # Determine current owner
    owner_id = cast(int, current_user.id)
    if current_user.social_profile and current_user.social_profile.profile_type == "pet":
        link = db.query(ProfileLink).filter(ProfileLink.pet_user_id == current_user.id).first()
        if link:
            owner_id = cast(int, link.owner_user_id)

    # Check if target is owner or a pet belonging to owner
    is_valid_target = False
    if target_user_id == owner_id:
        is_valid_target = True
    else:
        # Check if target is a pet of the owner
        target_link = db.query(ProfileLink).filter(
            ProfileLink.owner_user_id == owner_id,
            ProfileLink.pet_user_id == target_user_id
        ).first()
        if target_link:
            is_valid_target = True

    if not is_valid_target:
        raise HTTPException(status_code=403, detail="Not authorized to switch to this profile")

    target_user = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id == target_user_id).first()
    if not target_user or not target_user.social_profile:
        raise HTTPException(status_code=404, detail="Target profile not found")

    # Generate JWT token
    access_token_expires = timedelta(days=1)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"exp": expire, "user_id": str(target_user_id), "token_type": "access"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return SwitchProfileResponse(
        access_token=encoded_jwt,
        token_type="bearer",
        user=SwitchProfileUser(
            id=cast(int, target_user.id),
            username=cast(str, target_user.username),
            profile_type=cast(str, target_user.social_profile.profile_type)
        )
    )

@router.get("/{user_id}/profile", response_model=ProfileResponse)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_auth_db)
):
    user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.social_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile = cast(SocialProfile, user.social_profile)
    
    follower_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "profile_type": profile.profile_type,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "username": user.username,
        "profile_picture_url": profile.profile_picture_url,
        "follower_count": follower_count
    }



@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    if not current_user.social_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile = cast(SocialProfile, current_user.social_profile)
    
    follower_count = db.query(Follow).filter(Follow.following_id == current_user.id).count()
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "profile_type": profile.profile_type,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "username": current_user.username,
        "profile_picture_url": profile.profile_picture_url,
        "follower_count": follower_count
    }

@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_auth_db)
):
    if not current_user.social_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile = cast(SocialProfile, current_user.social_profile)
    
    if profile_data.username is not None:
        existing_user = db.query(DjangoUser).filter(
            DjangoUser.username == profile_data.username,
            DjangoUser.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
            
        current_user.username = profile_data.username
        
    if profile_data.profile_type is not None:
        profile.profile_type = profile_data.profile_type
    if profile_data.gender is not None:
        profile.gender = profile_data.gender
    if profile_data.date_of_birth is not None:
        profile.date_of_birth = profile_data.date_of_birth
    if profile_data.profile_picture_url is not None:
        profile.profile_picture_url = profile_data.profile_picture_url
        
    db.commit()
    db.refresh(profile)
    db.refresh(current_user)
    
    follower_count = db.query(Follow).filter(Follow.following_id == current_user.id).count()
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "profile_type": profile.profile_type,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "username": current_user.username,
        "profile_picture_url": profile.profile_picture_url,
        "follower_count": follower_count
    }

from typing import List
from app.schemas.follow import FollowResponse, UserBasicInfo

@router.post("/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
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
    current_user: DjangoUser = Depends(require_social_profile),
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
        
    followers = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).join(
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
        
    following = db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).join(
        Follow, Follow.following_id == DjangoUser.id
    ).filter(
        Follow.follower_id == user_id
    ).all()
    
    return following

@router.get("/{user_id}/reposts", response_model=List[PostResponse])
async def get_user_reposts(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Sort reposts new to old
    reposts = social_db.query(Repost).filter(Repost.user_id == user_id).order_by(Repost.created_at.desc()).all()
    post_ids = [repost.post_id for repost in reposts]
    
    if not post_ids:
        return []
        
    posts = social_db.query(Post).filter(Post.id.in_(post_ids)).all()
    post_dict = {post.id: post for post in posts}
    ordered_posts = [post_dict[pid] for pid in post_ids if pid in post_dict]
    
    current_user_id = cast(int, optional_user.id) if optional_user else None
    ordered_posts = attach_user_engagements(ordered_posts, current_user_id, social_db)
    return attach_authors(ordered_posts, auth_db, current_user_id)

@router.get("/{user_id}/saved", response_model=List[PostResponse])
@router.get("/{user_id}/saved-posts", response_model=List[PostResponse])
async def get_user_saved_posts(
    user_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only view your own saved posts"
        )
        
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Sort saved posts new to old
    saved_records = social_db.query(SavedPost).filter(SavedPost.user_id == user_id).order_by(SavedPost.created_at.desc()).all()
    post_ids = [s.post_id for s in saved_records]
    
    if not post_ids:
        return []
        
    posts = social_db.query(Post).options(joinedload(Post.quoted_post)).filter(Post.id.in_(post_ids)).all()
    post_dict = {post.id: post for post in posts}
    ordered_posts = [post_dict[pid] for pid in post_ids if pid in post_dict]
    
    current_user_id = cast(int, current_user.id)
    ordered_posts = attach_user_engagements(ordered_posts, current_user_id, social_db)
    return attach_authors(ordered_posts, auth_db, current_user_id)

@router.get("/{user_id}/likes", response_model=List[PostResponse])
async def get_user_likes(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Sort likes new to old
    likes = social_db.query(Like).filter(Like.user_id == user_id).order_by(Like.created_at.desc()).all()
    post_ids = [like.post_id for like in likes]
    
    if not post_ids:
        return []
        
    posts = social_db.query(Post).filter(Post.id.in_(post_ids)).all()
    post_dict = {post.id: post for post in posts}
    ordered_posts = [post_dict[pid] for pid in post_ids if pid in post_dict]
    
    current_user_id = cast(int, optional_user.id) if optional_user else None
    ordered_posts = attach_user_engagements(ordered_posts, current_user_id, social_db)
    return attach_authors(ordered_posts, auth_db, current_user_id)

@router.get("/{user_id}/posts", response_model=List[PostResponse])
async def get_user_posts(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    posts = social_db.query(Post).filter(Post.author_id == user_id).order_by(Post.created_at.desc()).all()
    
    current_user_id = cast(int, optional_user.id) if optional_user else None
    posts = attach_user_engagements(posts, current_user_id, social_db)
    return attach_authors(posts, auth_db, current_user_id)

@router.get("/{user_id}/activity", response_model=List[ActivityItem])
async def get_user_activity(
    user_id: int,
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    user = auth_db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    likes = social_db.query(Like).filter(Like.user_id == user_id).all()
    reposts = social_db.query(Repost).filter(Repost.user_id == user_id).all()
    
    activities = []
    for like in likes:
        activities.append({
            "id": f"like_{like.id}",
            "type": "like",
            "post_id": like.post_id,
            "timestamp": like.created_at
        })
        
    for repost in reposts:
        activities.append({
            "id": f"repost_{repost.id}",
            "type": "repost",
            "post_id": repost.post_id,
            "timestamp": repost.created_at
        })
        
    # Sort activities by timestamp descending (latest to oldest)
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    post_ids = list(set([a["post_id"] for a in activities]))
    if not post_ids:
        return []
        
    posts = social_db.query(Post).filter(Post.id.in_(post_ids)).all()
    current_user_id = cast(int, optional_user.id) if optional_user else None
    posts = attach_user_engagements(posts, current_user_id, social_db)
    posts = attach_authors(posts, auth_db, current_user_id)
    
    post_dict = {post.id: post for post in posts}
    
    result = []
    for a in activities:
        if a["post_id"] in post_dict:
            result.append({
                "id": a["id"],
                "type": a["type"],
                "post": post_dict[a["post_id"]],
                "timestamp": a["timestamp"]
            })
            
    return result
