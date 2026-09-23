from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, cast
from sqlalchemy import select, literal, union_all, text, Integer
from sqlalchemy.orm import joinedload
import copy

from app.database import get_social_db, get_auth_db
from app.dependencies import require_social_profile
from app.models.user import DjangoUser
from app.models.follow import Follow
from app.models.post import Post
from app.models.engagement import Repost
from app.schemas.post import PostResponse
from app.schemas.follow import UserBasicInfo
from app.utils.user import attach_authors
from app.utils.engagement import attach_user_engagements

router = APIRouter(prefix="/feed", tags=["Feed"])

@router.get("/following", response_model=List[PostResponse])
async def get_following_feed(
    limit: int = 20,
    offset: int = 0,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    """
    Get a feed of posts and reposts from users the current user is following.
    """
    user_id = cast(int, current_user.id)
    
    # 1. Get list of user IDs the current user is following
    follows = auth_db.query(Follow).filter(Follow.follower_id == user_id).all()
    following_ids = [f.following_id for f in follows]
    
    if not following_ids:
        return []
        
    # 2. Get posts authored by followed users
    post_query = select(
        Post.id.label("post_id"),
        Post.created_at.label("created_at"),
        literal(False).label("is_repost"),
        literal(None, type_=Integer).label("reposter_id")
    ).where(Post.author_id.in_(following_ids))
    
    # 3. Get reposts by followed users
    repost_query = select(
        Repost.post_id.label("post_id"),
        Repost.created_at.label("created_at"),
        literal(True).label("is_repost"),
        Repost.user_id.label("reposter_id")
    ).where(Repost.user_id.in_(following_ids))
    
    # Combine and sort
    combined_query = union_all(post_query, repost_query).order_by(text("created_at DESC")).offset(offset).limit(limit)
    feed_items = db.execute(combined_query).fetchall()
    
    if not feed_items:
        return []
        
    # Extract post details
    post_ids = [item.post_id for item in feed_items]
    posts = db.query(Post).options(joinedload(Post.quoted_post)).filter(Post.id.in_(post_ids)).all()
    post_map = {p.id: p for p in posts}
    
    # Extract reposter info
    reposter_ids = [item.reposter_id for item in feed_items if item.is_repost]
    reposters = auth_db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id.in_(reposter_ids)).all()
    reposter_map = {}
    
    for reposter in reposters:
        info = UserBasicInfo.model_validate(reposter)
        info.is_followed = True  # We know they are followed since we queried by following_ids
        reposter_map[reposter.id] = info
        
    # Assemble feed
    final_posts = []
    for item in feed_items:
        if item.post_id in post_map:
            p = copy.copy(post_map[item.post_id])
            if item.is_repost and item.reposter_id in reposter_map:
                p.reposter = reposter_map[item.reposter_id]
            final_posts.append(p)
            
    # Attach engagement and author data
    final_posts = attach_user_engagements(final_posts, user_id, db)
    return attach_authors(final_posts, auth_db, user_id)
