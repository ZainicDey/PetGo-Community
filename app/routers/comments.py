from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_social_db
from app.models.engagement import Comment
from app.models.post import Post
from app.models.user import DjangoUser
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse, CommentTree
from app.dependencies import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    current_user: DjangoUser = Depends(get_current_user),
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
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.get("/post/{post_id}", response_model=List[CommentTree])
async def get_post_comments(
    post_id: int,
    db: Session = Depends(get_social_db),
):
    """Get all top-level comments for a post, with nested replies."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Fetch only top-level comments; replies are eager-loaded via the 'selectin' relationship
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments


@router.get("/{comment_id}", response_model=CommentTree)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_social_db),
):
    """Get a single comment with all its nested replies."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db),
):
    """Update a comment's content. Only the author can edit."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    comment.content = data.content
    db.commit()
    db.refresh(comment)

    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_social_db),
):
    """Delete a comment and all its nested replies. Only the author can delete."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    db.delete(comment)
    db.commit()
