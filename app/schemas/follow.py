from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBasicInfo(BaseModel):
    id: int
    username: str
    profile_picture_url: Optional[str] = None

    class Config:
        from_attributes = True

class FollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    class Config:
        from_attributes = True
