from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from typing import Optional, List

class ProfileCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    profile_type: str = Field(..., min_length=1, max_length=50) # 'pet' or 'user'
    gender: Optional[str] = Field(None, max_length=20)
    pet_type: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = Field(None, max_length=255)

class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=150)
    profile_type: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    pet_type: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = Field(None, max_length=255)

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    profile_type: str
    gender: Optional[str] = None
    pet_type: Optional[str] = None
    date_of_birth: Optional[date] = None
    username: str
    profile_picture_url: Optional[str] = None
    follower_count: int = 0

    class Config:
        from_attributes = True

class UserMeResponse(BaseModel):
    id: int
    username: str
    email: str
    has_social_profile: bool

    class Config:
        from_attributes = True

class UsernameCheckRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)

class UsernameCheckResponse(BaseModel):
    exists: bool
    available: bool

from typing import Literal
from datetime import datetime
from app.schemas.post import PostResponse

class ActivityItem(BaseModel):
    id: str
    type: Literal["like", "repost"]
    post: PostResponse
    timestamp: datetime

    class Config:
        from_attributes = True

class PetProfileCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    gender: Optional[str] = Field(None, max_length=20)
    pet_type: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = Field(None, max_length=255)

class SwitchableProfile(BaseModel):
    user_id: int
    username: str
    profile_type: str
    profile_picture_url: Optional[str] = None
    is_owner: bool

class SwitchableProfilesResponse(BaseModel):
    active_profile_id: int
    profiles: List[SwitchableProfile]

class SwitchProfileRequest(BaseModel):
    target_user_id: int

class SwitchProfileUser(BaseModel):
    id: int
    username: str
    profile_type: str

class SwitchProfileResponse(BaseModel):
    access_token: str
    token_type: str
    user: SwitchProfileUser
