from sqlalchemy import Column, Integer, String, ForeignKey, Float,Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

class ReadingTextData(Base):
    __tablename__ = "reading_text_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    reading_text_id = Column(Integer, ForeignKey("reading_texts.id"), nullable=False)
    okuma_dogrulugu = Column(Float, nullable=False)
    yanlış_söylenen_kelimeler = Column(String, nullable=False)
    yanlış_kelimelerin_yerine_söylenen_kelimeler = Column(String, nullable=False)
    dogru_kelime_sayısı = Column(Integer, nullable=False)
    is_resolved_data = Column(Boolean, default=False)

    reading_text = relationship("ReadingText", back_populates="reading_text_data")
    user = relationship("User", back_populates="reading_text_data")
