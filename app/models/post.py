from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional

from app.database import SocialBase

class Post(SocialBase):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False) # References auth_user.id
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)   # URL/path to image or video
    media_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # "image" or "video"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
