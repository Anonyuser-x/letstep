from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
import datetime


class UserTrophy(Base):
    __tablename__ = "user_trophies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trophy_id = Column(String, nullable=False, index=True)
    date_earned = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")