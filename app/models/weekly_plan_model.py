from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.models.base import Base

class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    goal = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


    user = relationship("User", back_populates="weekly_plans")
    tasks = relationship("PlanTask", back_populates="plan", cascade="all, delete-orphan")