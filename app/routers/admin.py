from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/")
async def get_admin():
    return {"message": "Admin endpoint placeholder"}
