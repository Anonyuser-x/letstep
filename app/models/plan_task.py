from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False)
    day_of_week = Column(String, nullable=False)
    activity = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    plan = relationship("WeeklyPlan", back_populates="tasks")
