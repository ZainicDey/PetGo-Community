from fastapi import APIRouter

router = APIRouter(prefix="/feed", tags=["Feed"])

@router.get("/")
async def get_feed():
    return {"message": "Feed endpoint placeholder"}
