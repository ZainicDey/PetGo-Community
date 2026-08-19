from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("/")
async def get_posts():
    return {"message": "Posts endpoint placeholder"}
