from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1)
    media_url: Optional[str] = None
    media_type: Optional[Literal["image", "video"]] = None

class PostResponse(BaseModel):
    id: int
    author_id: int
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RepostResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

