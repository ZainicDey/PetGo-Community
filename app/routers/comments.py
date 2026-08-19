from fastapi import APIRouter

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/")
async def get_comments():
    return {"message": "Comments endpoint placeholder"}
