from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class IlkHarfiYakalaQuestion(Base):
    __tablename__ = "ilk_harfi_yakala_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    level = Column(String, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    question_image = Column(String,nullable=True)


    exercise = relationship("Exercise", back_populates="ilk_harfi_yakala_questions")
