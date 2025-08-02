from fastapi import APIRouter, Depends, status,HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from app.datab import get_async_db
from app.utils import get_current_user_id,get_current_user
from app.models import User, WeeklyPlan,DailyTask
from app.functions.ai_functions import generate_weekly_plan_service, get_or_create_daily_tasks_service

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/get-weekly-plan", summary="Mevcut Haftalık Planı Getir")
async def get_current_weekly_plan(db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user_id)):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    query = (
        select(WeeklyPlan)
        .where(WeeklyPlan.user_id == current_user.id, WeeklyPlan.created_at >= seven_days_ago)
        .order_by(WeeklyPlan.created_at.desc())
        .options(selectinload(WeeklyPlan.tasks))
    )
    result = await db.execute(query)
    existing_plan = result.scalars().first()
    if not existing_plan:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Bu hafta için oluşturulmuş bir plan bulunamadı."})
    return existing_plan

@router.post("/generate-weekly-plan", summary="Yeni Haftalık Çalışma Planı Oluştur")
async def generate_weekly_plan_endpoint(db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user_id)):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(select(WeeklyPlan).filter(WeeklyPlan.user_id == current_user.id, WeeklyPlan.created_at >= seven_days_ago))
    if result.scalars().first():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Son bir hafta içinde zaten bir haftalık plan oluşturdunuz."})
    plan = await generate_weekly_plan_service(user=current_user, db=db)
    return plan


@router.get("/get-daily-tasks", summary="Günlük Görevleri Getir veya Oluştur")
async def get_daily_tasks_endpoint(db: AsyncSession = Depends(get_async_db),
                                   current_user: User = Depends(get_current_user)):

    tasks = await get_or_create_daily_tasks_service(user=current_user, db=db)
    return tasks


@router.post("/complete-daily-task/{task_id}", summary="Günlük Görevi Tamamlandı Olarak İşaretle")
async def complete_daily_task_endpoint(task_id: int, db: AsyncSession = Depends(get_async_db),
                                       current_user: User = Depends(get_current_user)):

    query = select(DailyTask).where(DailyTask.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı.")

    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlemi yapma yetkiniz yok.")

    task.is_completed = not task.is_completed
    await db.commit()
    await db.refresh(task)

    return {"message": "Görev durumu güncellendi.", "task": task}
