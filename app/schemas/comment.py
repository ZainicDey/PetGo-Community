from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.follow import UserBasicInfo


class CommentCreate(BaseModel):
    post_id: int
    parent_id: Optional[int] = None  # None = top-level comment, set = reply
    content: str = Field(..., min_length=1)


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    author: Optional[UserBasicInfo] = None
    parent_id: Optional[int] = None
    content: str
    created_at: datetime
    replies_count: int = 0

    class Config:
        from_attributes = True
