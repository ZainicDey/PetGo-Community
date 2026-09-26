from sqlalchemy import Integer, Text, DateTime, select, func, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, column_property, relationship
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
    quoted_post_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True)
    visibility: Mapped[str] = mapped_column(String(20), default="public", server_default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    quoted_post: Mapped[Optional["Post"]] = relationship("Post", remote_side=[id])

from app.models.engagement import Like, Comment, Repost

Post.likes_count = column_property(
    select(func.count(Like.id)).where(Like.post_id == Post.id).correlate_except(Like).scalar_subquery()
)
Post.comments_count = column_property(
    select(func.count(Comment.id)).where(Comment.post_id == Post.id).correlate_except(Comment).scalar_subquery()
)
from sqlalchemy.orm import aliased
QuotedPost = aliased(Post)

Post.reposts_count = column_property(
    select(func.count(Repost.id)).where(Repost.post_id == Post.id).correlate_except(Repost).scalar_subquery() +
    select(func.count(QuotedPost.id)).where(QuotedPost.quoted_post_id == Post.id).correlate_except(QuotedPost).scalar_subquery()
)
