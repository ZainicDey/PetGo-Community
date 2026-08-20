from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_auth_db
from app.models.user import DjangoUser, SocialProfile
from app.schemas.user import ProfileCreate, ProfileResponse
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
