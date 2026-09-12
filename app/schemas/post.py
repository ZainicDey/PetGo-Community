from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Union
from datetime import datetime

class MediaItem(BaseModel):
    url: str
    media_type: Optional[Literal["image", "video"]] = "image"
    public_id: Optional[str] = None

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1)
    media: Optional[List[Union[MediaItem, str]]] = Field(default_factory=list)

class PostResponse(BaseModel):
    id: int
    author_id: int
    content: str
    media: Optional[List[MediaItem]] = Field(default_factory=list)
    created_at: datetime
    likes_count: int = 0
    reposts_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True


class RepostResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
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

