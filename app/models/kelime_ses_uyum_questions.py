from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class KelimeSesUyumQuestion(Base):
    __tablename__ = "kelime_ses_uyum_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)
    option_a_image = Column(String, nullable=False)
    option_b_image = Column(String, nullable=False)
    option_c_image = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    level = Column(String, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    exercise = relationship("Exercise", back_populates="kelime_ses_uyum_questions")