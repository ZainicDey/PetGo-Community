from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, List, Union
from datetime import datetime
from app.schemas.follow import UserBasicInfo

class MediaItem(BaseModel):
    url: str
    media_type: Optional[Literal["image", "video"]] = "image"
    public_id: Optional[str] = None

class PostCreate(BaseModel):
    content: str = ""
    media: Optional[List[Union[MediaItem, str]]] = Field(default_factory=list)
    quoted_post_id: Optional[int] = None
    visibility: Literal["public", "followers"] = "public"

    @model_validator(mode='after')
    def validate_content_or_media(self):
        if not self.content.strip() and not self.media:
            raise ValueError("String should have at least 1 character")
        return self

class PostResponse(BaseModel):
    id: int
    author_id: int
    author: Optional[UserBasicInfo] = None
    content: str
    media: Optional[List[MediaItem]] = Field(default_factory=list)
    visibility: str = "public"
    created_at: datetime
    likes_count: int = 0
    reposts_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_reposted: bool = False
    is_saved: bool = False
    quoted_post_id: Optional[int] = None
    quoted_post: Optional["PostResponse"] = None
    reposter: Optional[UserBasicInfo] = None

    class Config:
        from_attributes = True


class RepostResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    visibility: str = "public"
    created_at: datetime

    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SaveResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SavePostRequest(BaseModel):
    id: Optional[int] = None
    post_id: Optional[int] = None

class RepostCreate(BaseModel):
    visibility: Literal["public", "followers"] = "public"

