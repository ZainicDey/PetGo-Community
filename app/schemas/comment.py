from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from app.schemas.follow import UserBasicInfo


class CommentCreate(BaseModel):
    post_id: int
    parent_id: Optional[int] = None  # None = top-level comment, set = reply
    content: str = ""
    image_url: Optional[str] = None

    @model_validator(mode='after')
    def validate_content_or_image(self):
        if not self.content.strip() and not self.image_url:
            raise ValueError("String should have at least 1 character")
        return self


class CommentUpdate(BaseModel):
    content: str = ""
    image_url: Optional[str] = None

    @model_validator(mode='after')
    def validate_content_or_image(self):
        if not self.content.strip() and not self.image_url:
            raise ValueError("String should have at least 1 character")
        return self


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    author: Optional[UserBasicInfo] = None
    parent_id: Optional[int] = None
    content: str
    image_url: Optional[str] = None
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime
    replies_count: int = 0

    class Config:
        from_attributes = True
