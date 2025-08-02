import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import Base

class UserRole(PyEnum):
    student = "student"
    teacher = "teacher"


student_teacher_association = Table('student_teacher_association', Base.metadata,
    Column('teacher_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('student_id', Integer, ForeignKey('users.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    invitation_code = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))


    students = relationship(
        "User",
        secondary=student_teacher_association,
        primaryjoin=id == student_teacher_association.c.teacher_id,
        secondaryjoin=id == student_teacher_association.c.student_id,
        back_populates="teachers"
    )

    teachers = relationship(
        "User",
        secondary=student_teacher_association,
        primaryjoin=id == student_teacher_association.c.student_id,
        secondaryjoin=id == student_teacher_association.c.teacher_id,
        back_populates="students"
    )

    activities = relationship("UserActivity", back_populates="user")
    weekly_plans = relationship("WeeklyPlan", back_populates="user")
    reading_text_data = relationship("ReadingTextData", back_populates="user")
    user_exercises = relationship("UserExercise", back_populates="user", cascade="all, delete-orphan")
    daily_tasks = relationship("DailyTask", back_populates="owner", cascade="all, delete-orphan")

    @property
    def is_teacher(self):
        return self.role == UserRole.teacher

    @property
    def is_student(self):
        return self.role == UserRole.student