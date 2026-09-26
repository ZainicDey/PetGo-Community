from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, cast

from app.database import get_social_db, get_auth_db
from app.dependencies import get_current_user, require_social_profile, get_optional_current_user
from app.models.user import DjangoUser
from app.models.post import Post
from app.models.engagement import Repost, Like, SavedPost
from app.schemas.post import PostCreate, PostResponse, RepostResponse, LikeResponse, SaveResponse, SavePostRequest, RepostCreate
from app.schemas.follow import UserBasicInfo
from app.utils.media import process_media_list, delete_post_media_files
from app.utils.user import attach_authors
from app.utils.engagement import attach_user_engagements

router = APIRouter(prefix="/posts", tags=["Posts"])

from sqlalchemy import select, literal, union_all, text, Integer, or_, and_
from sqlalchemy.orm import joinedload

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    user_id = cast(int, optional_user.id) if optional_user else None
    following_ids = []
    if user_id:
        from app.models.follow import Follow
        follows = auth_db.query(Follow).filter(Follow.follower_id == user_id).all()
        following_ids = [f.following_id for f in follows]

    post_conditions = [Post.visibility == 'public']
    if user_id:
        post_conditions.append(Post.author_id == user_id)
        if following_ids:
            post_conditions.append(and_(Post.visibility == 'followers', Post.author_id.in_(following_ids)))

    post_query = select(
        Post.id.label("post_id"),
        Post.created_at.label("created_at"),
        literal(False).label("is_repost"),
        literal(None, type_=Integer).label("reposter_id")
    ).where(or_(*post_conditions))
    
    repost_conditions = [Repost.visibility == 'public']
    if user_id:
        repost_conditions.append(Repost.user_id == user_id)
        if following_ids:
            repost_conditions.append(and_(Repost.visibility == 'followers', Repost.user_id.in_(following_ids)))

    repost_query = select(
        Repost.post_id.label("post_id"),
        Repost.created_at.label("created_at"),
        literal(True).label("is_repost"),
        Repost.user_id.label("reposter_id")
    ).where(or_(*repost_conditions))
    
    combined_query = union_all(post_query, repost_query).order_by(text("created_at DESC")).offset(offset).limit(limit)
    feed_items = db.execute(combined_query).fetchall()
    
    if not feed_items:
        return []
        
    post_ids = [item.post_id for item in feed_items]
    posts = db.query(Post).options(joinedload(Post.quoted_post)).filter(Post.id.in_(post_ids)).all()
    post_map = {p.id: p for p in posts}
    
    user_id = cast(int, optional_user.id) if optional_user else None
    
    # Extract reposter_ids to fetch them
    reposter_ids = [item.reposter_id for item in feed_items if item.is_repost]
    reposters = auth_db.query(DjangoUser).options(joinedload(DjangoUser.social_profile)).filter(DjangoUser.id.in_(reposter_ids)).all()
    reposter_map = {}
    
    # We can also attach is_followed for reposters if needed
    followed_user_ids = set(following_ids) if following_ids else set()
        
    for reposter in reposters:
        info = UserBasicInfo.model_validate(reposter)
        if reposter.id in followed_user_ids:
            info.is_followed = True
        reposter_map[reposter.id] = info

    final_posts = []
    for item in feed_items:
        if item.post_id in post_map:
            # We must make a copy if the same post is reposted multiple times in the feed
            import copy
            p = copy.copy(post_map[item.post_id])
            if item.is_repost and item.reposter_id in reposter_map:
                p.reposter = reposter_map[item.reposter_id]
            final_posts.append(p)
            
    final_posts = attach_user_engagements(final_posts, user_id, db)
    return attach_authors(final_posts, auth_db, user_id)

@router.get("/saved", response_model=List[PostResponse])
async def get_saved_posts(
    current_user: DjangoUser = Depends(require_social_profile),
    auth_db: Session = Depends(get_auth_db),
    social_db: Session = Depends(get_social_db)
):
    user_id = cast(int, current_user.id)
    saved_records = social_db.query(SavedPost).filter(
        SavedPost.user_id == user_id
    ).order_by(SavedPost.created_at.desc()).all()
    
    post_ids = [s.post_id for s in saved_records]
    if not post_ids:
        return []
        
    posts = social_db.query(Post).options(joinedload(Post.quoted_post)).filter(Post.id.in_(post_ids)).all()
    post_dict = {post.id: post for post in posts}
    ordered_posts = [post_dict[pid] for pid in post_ids if pid in post_dict]
    
    ordered_posts = attach_user_engagements(ordered_posts, user_id, social_db)
    return attach_authors(ordered_posts, auth_db, user_id)

@router.post("/save", response_model=SaveResponse)
async def save_post_body(
    data: SavePostRequest,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    target_post_id = data.post_id if data.post_id is not None else data.id
    if target_post_id is None:
        raise HTTPException(status_code=400, detail="Missing post id")
    return await save_post(target_post_id, current_user, db)

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    """
    Create a new post.
    Accepts content and an array of media (images/videos).
    Automatically extracts public_id and media_type from Cloudinary URLs if not provided.
    """
    processed_media = process_media_list(data.media)

    new_post = Post(
        author_id=current_user.id,
        content=data.content,
        media=processed_media,
        quoted_post_id=data.quoted_post_id,
        visibility=data.visibility,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db),
    optional_user: Optional[DjangoUser] = Depends(get_optional_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.visibility == 'followers':
        if not optional_user:
            raise HTTPException(status_code=401, detail="You must be logged in to view this post")
        if post.author_id != optional_user.id:
            from app.models.follow import Follow
            is_following = auth_db.query(Follow).filter(
                Follow.follower_id == optional_user.id,
                Follow.following_id == post.author_id
            ).first()
            if not is_following:
                raise HTTPException(status_code=403, detail="This post is for followers only")
        
    user_id = cast(int, optional_user.id) if optional_user else None
    post = attach_user_engagements([post], user_id, db)[0]
    return attach_authors([post], auth_db, user_id)[0]

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    """
    Delete a post and its associated media files on Cloudinary.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    # Send deletion requests to Cloudinary for all attached media items
    if post.media:
        delete_post_media_files(post.media)  # type: ignore

    db.delete(post)
    db.commit()


@router.post("/{post_id}/repost", response_model=RepostResponse)
async def repost_post(
    post_id: int,
    data: RepostCreate = Body(default_factory=RepostCreate),
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.visibility == 'followers':
        raise HTTPException(status_code=403, detail="You cannot repost a followers-only post")
        
    existing_repost = db.query(Repost).filter(
        Repost.post_id == post_id,
        Repost.user_id == current_user.id
    ).first()
    
    if existing_repost:
        raise HTTPException(status_code=400, detail="You have already reposted this post")
        
    new_repost = Repost(post_id=post_id, user_id=current_user.id, visibility=data.visibility)
    db.add(new_repost)
    db.commit()
    db.refresh(new_repost)
    
    return new_repost

@router.delete("/{post_id}/repost", status_code=status.HTTP_204_NO_CONTENT)
async def unrepost_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    repost = db.query(Repost).filter(
        Repost.post_id == post_id,
        Repost.user_id == current_user.id
    ).first()
    
    if not repost:
        raise HTTPException(status_code=404, detail="You have not reposted this post")
        
    db.delete(repost)
    db.commit()

@router.get("/{post_id}/reposters", response_model=List[UserBasicInfo])
async def get_post_reposters(
    post_id: int,
    social_db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    post = social_db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    reposts = social_db.query(Repost).filter(Repost.post_id == post_id).all()
    user_ids = [repost.user_id for repost in reposts]
    
    if not user_ids:
        return []
        
    users = auth_db.query(DjangoUser).filter(DjangoUser.id.in_(user_ids)).all()
    return users

@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this post")
        
    new_like = Like(post_id=post_id, user_id=current_user.id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    
    return new_like

@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="You have not liked this post")
        
    db.delete(like)
    db.commit()

@router.get("/{post_id}/likes", response_model=List[UserBasicInfo])
async def get_post_likes(
    post_id: int,
    social_db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    post = social_db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    likes = social_db.query(Like).filter(Like.post_id == post_id).all()
    user_ids = [like.user_id for like in likes]
    
    if not user_ids:
        return []
        
    users = auth_db.query(DjangoUser).filter(DjangoUser.id.in_(user_ids)).all()
    return users

@router.post("/{post_id}/save", response_model=SaveResponse)
async def save_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    user_id = cast(int, current_user.id)
    existing_save = db.query(SavedPost).filter(
        SavedPost.post_id == post_id,
        SavedPost.user_id == user_id
    ).first()
    
    if existing_save:
        raise HTTPException(status_code=400, detail="You have already saved this post")
        
    new_save = SavedPost(post_id=post_id, user_id=user_id)
    db.add(new_save)
    db.commit()
    db.refresh(new_save)
    
    return new_save

@router.delete("/{post_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_post(
    post_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db)
):
    user_id = cast(int, current_user.id)
    saved = db.query(SavedPost).filter(
        SavedPost.post_id == post_id,
        SavedPost.user_id == user_id
    ).first()
    
    if not saved:
        raise HTTPException(status_code=404, detail="You have not saved this post")
        
    db.delete(saved)
    db.commit()

