from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WeeklyPlanCreate(BaseModel):
    user_id: int
    subject: str
    goal: str
    allocated_minutes: int
    completion_ratio: Optional[float] = 0.0

class WeeklyPlanRead(BaseModel):
    id: int
    user_id: int
    subject: str
    goal: str
    allocated_minutes: int
    completion_ratio: float
    created_at: datetime

    class Config:
        from_attributes = True

class WeeklyPlanUpdate(BaseModel):
    subject: Optional[str] = None
    goal: Optional[str] = None
    allocated_minutes: Optional[int] = None
    completion_ratio: Optional[float] = None
