from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_social_db, get_auth_db
from app.models.engagement import Comment
from app.models.post import Post
from app.models.user import DjangoUser
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.dependencies import get_current_user, require_social_profile
from app.utils.user import attach_authors
from app.utils.media import delete_cloudinary_media, parse_cloudinary_url

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db),
):
    """Create a top-level comment or a reply to an existing comment."""
    # Verify the post exists
    post = db.query(Post).filter(Post.id == data.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # If replying, verify the parent comment exists and belongs to the same post
    if data.parent_id is not None:
        parent = db.query(Comment).filter(Comment.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent.post_id != data.post_id:
            raise HTTPException(status_code=400, detail="Parent comment does not belong to this post")

    comment = Comment(
        post_id=data.post_id,
        author_id=current_user.id,
        parent_id=data.parent_id,
        content=data.content,
        image_url=data.image_url,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.get("/post/{post_id}", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    """Get all top-level comments for a post, with pagination."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return attach_authors(comments, auth_db)


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    """Get a single comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return attach_authors([comment], auth_db)[0]

@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    comment_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_social_db),
    auth_db: Session = Depends(get_auth_db)
):
    """Get direct replies to a comment, with pagination."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    replies = (
        db.query(Comment)
        .filter(Comment.parent_id == comment_id)
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return attach_authors(replies, auth_db)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db),
):
    """Update a comment's content. Only the author can edit."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted comment")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    # If the image was removed or changed, delete the old one from Cloudinary
    if comment.image_url and comment.image_url != data.image_url:
        parsed = parse_cloudinary_url(comment.image_url)
        if parsed["public_id"]:
            delete_cloudinary_media(parsed["public_id"], parsed["media_type"] or "image")

    comment.content = data.content
    comment.image_url = data.image_url
    comment.is_edited = True
    db.commit()
    db.refresh(comment)

    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: DjangoUser = Depends(require_social_profile),
    db: Session = Depends(get_social_db),
):
    """Soft delete a comment. Only the author can delete."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Comment is already deleted")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    # Delete media from Cloudinary if exists
    if comment.image_url:
        parsed = parse_cloudinary_url(comment.image_url)
        if parsed["public_id"]:
            delete_cloudinary_media(parsed["public_id"], parsed["media_type"] or "image")

    comment.is_deleted = True
    comment.content = "[This comment has been deleted]"
    comment.image_url = None
    db.commit()
