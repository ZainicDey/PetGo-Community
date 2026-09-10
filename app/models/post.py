from sqlalchemy import Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.database import SocialBase

class Post(SocialBase):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False) # References auth_user.id
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Store list of media dicts: [{"url": "...", "media_type": "image"|"video", "public_id": "..."}]
    media: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

