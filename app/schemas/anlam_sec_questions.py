from pydantic import BaseModel

class AnlamSecBase(BaseModel):
    question_text: str
    question_image:str
    option_a: str
    option_b: str
    option_c: str
    correct_answer: str
    level: str
    exercise_id: int


class AnlamSecRead(AnlamSecBase):
    id: int

    class Config:
        from_attributes = True
