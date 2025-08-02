from pydantic import BaseModel

class KodKiriciBase(BaseModel):
    question_text: str
    correct_answer: str
    level: str
    exercise_id: int

class KodKiriciRead(KodKiriciBase):
    id: int

    class Config:
        from_attributes = True
