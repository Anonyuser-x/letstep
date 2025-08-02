from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import Base

class ReadingText(Base):
    __tablename__ = "reading_texts"

    id = Column(Integer, primary_key=True, index=True)
    paragraph = Column(Text, nullable=False)

    reading_text_data = relationship("ReadingTextData", back_populates="reading_text")

