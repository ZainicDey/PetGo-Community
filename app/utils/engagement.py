from typing import List, Any, Optional
from sqlalchemy.orm import Session
from app.models.engagement import Like, Repost

def attach_user_engagements(items: List[Any], user_id: Optional[int] = None, db: Optional[Session] = None) -> List[Any]:
    if not items or not user_id or not db:
        # Default to false for all
        for item in items:
            item.is_liked = False
            item.is_reposted = False
        return items
        
    def get_all_items_eng(items_list):
        all_i = []
        for i in items_list:
            all_i.append(i)
            if hasattr(i, 'quoted_post') and i.quoted_post:
                all_i.extend(get_all_items_eng([i.quoted_post]))
        return all_i

    all_items = get_all_items_eng(items)
    item_ids = [item.id for item in all_items if hasattr(item, 'id')]
    
    # Find which of these posts the user liked
    user_likes = db.query(Like.post_id).filter(Like.user_id == user_id, Like.post_id.in_(item_ids)).all()
    liked_post_ids = {row[0] for row in user_likes}
    
    # Find which of these posts the user reposted
    user_reposts = db.query(Repost.post_id).filter(Repost.user_id == user_id, Repost.post_id.in_(item_ids)).all()
    reposted_post_ids = {row[0] for row in user_reposts}
    
    for item in all_items:
        if hasattr(item, 'id'):
            item.is_liked = item.id in liked_post_ids
            item.is_reposted = item.id in reposted_post_ids
            
    return items
