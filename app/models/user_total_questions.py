from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class UserExercise(Base):
    __tablename__ = "user_exercises"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    game_type = Column(String, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answer = Column(Integer, nullable=False)
    wrong_answer = Column(Integer, nullable=False)

    user = relationship("User", back_populates="user_exercises")
    exercise = relationship("Exercise", back_populates="user_exercises")
