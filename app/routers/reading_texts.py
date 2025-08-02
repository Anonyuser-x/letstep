from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.datab import get_async_db
from app.models import ReadingText
from app.schemas import ReadingTextOut

router = APIRouter(
    prefix="/reading-text",
    tags=["Reading Texts"]
)

@router.get("/max-id", response_model=dict)
async def get_max_id(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(func.max(ReadingText.id)))
    max_id = result.scalar_one_or_none()
    if max_id is None:
        return {"max_id": 0}
    return {"max_id": max_id}

@router.get("/{text_id}", response_model=ReadingTextOut)
async def get_reading_text(text_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.get(ReadingText, text_id)
    if not result:
        raise HTTPException(status_code=404, detail="Metin bulunamadı")
    return result