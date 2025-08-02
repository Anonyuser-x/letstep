from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.datab import get_async_db
from app.models import User
from app.functions import take_all_data_functions
from app.utils import get_teacher_and_check_student_access

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)
@router.get("/{student_id}/activity-data")
async def get_activity_data_endpoint(
    db: AsyncSession = Depends(get_async_db),
    student: User = Depends(get_teacher_and_check_student_access)
):

    df = await take_all_data_functions.get_user_activity_dataframe(db=db, user_id=student.id)

    if df is None:
        raise HTTPException(status_code=404, detail=f"User ID {student.id} için aktivite verisi bulunamadı.")

    return df.to_json(orient="split", date_format='iso')

@router.get("/{student_id}/exercise-summary")
async def get_exercise_summary_endpoint(
    db: AsyncSession = Depends(get_async_db),
    student: User = Depends(get_teacher_and_check_student_access)
):

    df = await take_all_data_functions.get_user_exercise_summary_dataframe(db=db, user_id=student.id)

    if df is None:
        raise HTTPException(status_code=404, detail=f"User ID {student.id} için egzersiz özeti verisi bulunamadı.")
    return df.to_json(orient="split")

