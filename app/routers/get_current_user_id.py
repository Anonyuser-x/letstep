from fastapi import APIRouter, Depends
from app.models import User
from app.utils import get_current_user_id

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/get")
async def get_user_id(current_user: User = Depends(get_current_user_id)):
    return {"user_id": current_user.id}