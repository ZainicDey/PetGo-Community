from sqlalchemy import Integer, Text, DateTime, select, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, column_property
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

from app.models.engagement import Like, Comment, Repost

Post.likes_count = column_property(
    select(func.count(Like.id)).where(Like.post_id == Post.id).correlate_except(Like).scalar_subquery()
)
Post.comments_count = column_property(
    select(func.count(Comment.id)).where(Comment.post_id == Post.id).correlate_except(Comment).scalar_subquery()
)
Post.reposts_count = column_property(
    select(func.count(Repost.id)).where(Repost.post_id == Post.id).correlate_except(Repost).scalar_subquery()
)
