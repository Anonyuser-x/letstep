from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserActivityRead(BaseModel):
    datetime: datetime
    day_of_week: Optional[str]
    game_type: Optional[str]
    category: Optional[str]
    is_resolved: Optional[bool]
    selected_answer: Optional[str]
    correct_answer: Optional[str]
    wrong_type: Optional[str]
    student_profile: Optional[str]
    question_id: Optional[int]
    reaction_time: Optional[int]
    repeat_count: Optional[int]

    class Config:
        from_attributes = True
