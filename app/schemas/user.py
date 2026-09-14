from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ProfileCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    profile_type: str = Field(..., min_length=1, max_length=50) # 'pet' or 'user'
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = Field(None, max_length=255)

class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=150)
    profile_type: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = Field(None, max_length=255)

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    profile_type: str
    gender: Optional[str] = None
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
