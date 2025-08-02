from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class AnlamBagdastirQuestion(Base):
    __tablename__ = "anlam_bagdastir_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_image = Column(String,nullable=True)
    question_text = Column(String, nullable=False)
    option_a = Column(String, nullable=True)
    option_b = Column(String, nullable=True)
    option_c = Column(String, nullable=True)
    correct_answer = Column(String, nullable=False)
    level = Column(String, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    exercise = relationship("Exercise", back_populates="anlam_bagdastir_questions")
