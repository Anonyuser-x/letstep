from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas import UserReport, UserJourneyReport, Trophy
from app.utils.dependencies import get_current_user_id, get_async_db
from app.models import User
from app.functions.user_data_rapor_functions import get_user_development_report, get_user_journey_report, get_and_update_trophies

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/me", response_model=UserReport)
async def get_current_user_report(current_user: User = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_db)):
    report = await get_user_development_report(current_user=current_user, db=db)
    return report

@router.get("/me/journey", response_model=UserJourneyReport)
async def get_current_user_journey_report(current_user: User = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_db)):
    report = await get_user_journey_report(current_user=current_user, db=db)
    return report

@router.get("/me/trophies", response_model=List[Trophy])
async def get_user_trophies_endpoint(current_user: User = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_db)):
    journey_report = await get_user_journey_report(current_user=current_user, db=db)
    trophies = await get_and_update_trophies(current_user=current_user, report_data=journey_report, db=db)
    return trophies