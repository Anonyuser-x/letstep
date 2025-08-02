from pydantic import BaseModel

class AkılYurutBase(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    correct_answer: str
    level: str
    exercise_id: int

class AkılYurutRead(AkılYurutBase):
    id: int

    class Config:
        from_attributes = True
