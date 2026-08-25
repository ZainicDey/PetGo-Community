from pydantic import BaseModel, Field
from datetime import datetime

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1)

class PostResponse(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
