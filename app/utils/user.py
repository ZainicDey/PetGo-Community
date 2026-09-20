from typing import List, Any, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.user import DjangoUser
from app.schemas.follow import UserBasicInfo
from app.models.follow import Follow

def get_all_items(items):
    all_items = []
    for item in items:
        all_items.append(item)
        if hasattr(item, 'quoted_post') and item.quoted_post:
            all_items.extend(get_all_items([item.quoted_post]))
    return all_items

def attach_authors(items: List[Any], auth_db: Session, current_user_id: Optional[int] = None) -> List[Any]:
    if not items:
        return items
    
    # Also attach authors to nested replies if they exist
    all_items = get_all_items(items)
    
    author_ids = list(set([item.author_id for item in all_items if hasattr(item, 'author_id')]))
    if not author_ids:
        return items
        
    authors = auth_db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id.in_(author_ids)).all()
    
    followed_user_ids = set()
    if current_user_id:
        follows = auth_db.query(Follow).filter(
            Follow.follower_id == current_user_id,
            Follow.following_id.in_(author_ids)
        ).all()
        followed_user_ids = {f.following_id for f in follows}

    author_map = {}
    for author in authors:
        info = UserBasicInfo.model_validate(author)
        if author.id in followed_user_ids:
            info.is_followed = True
        author_map[author.id] = info
    
    for item in all_items:
        if hasattr(item, 'author_id'):
            # Dynamically attach the Pydantic object so that from_attributes=True picks it up
            item.author = author_map.get(item.author_id)
            
    return items
