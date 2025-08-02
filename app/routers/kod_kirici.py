from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.functions import kod_kirici_functions as functions
from app.datab import get_async_db

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.get("/kod-kirici")
async def get_questions(level: str, db: AsyncSession = Depends(get_async_db)):
    result = await functions.get_questions_by_level(db, level)
    return result

@router.post("/kod-kirici/submit")
async def submit_answer(user_id: int, payload: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    result = await functions.submit_answer(db, user_id, payload)
    return result

@router.post("/kod-kirici/complete")
async def complete_exercise(payload: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    result = await functions.save_user_exercise_summary(db, payload)
    return result