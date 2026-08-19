from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ProfileCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    profile_type: str = Field(..., min_length=1, max_length=50) # 'pet' or 'user'
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    profile_type: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    username: str

    class Config:
        from_attributes = True
