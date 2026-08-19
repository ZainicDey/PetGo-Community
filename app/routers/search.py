from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
async def get_search():
    return {"message": "Search endpoint placeholder"}
