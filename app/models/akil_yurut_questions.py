from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class AkilYurutQuestion(Base):
    __tablename__ = "akil_yurut_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    level = Column(String, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    exercise = relationship("Exercise", back_populates="akil_yurut_questions")
