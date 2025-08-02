from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    datetime = Column(DateTime, nullable=False)
    day_of_week = Column(String, nullable=True)
    game_type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    is_resolved = Column(Boolean, default=False)
    selected_answer = Column(String, nullable=True)
    correct_answer = Column(String, nullable=True)
    wrong_type = Column(String, nullable=True)
    student_profile = Column(String, nullable=True)
    question_id = Column(Integer, nullable=True)
    reaction_time = Column(Integer, nullable=True)
    repeat_count = Column(Integer, nullable=True)

    user = relationship("User", back_populates="activities")
