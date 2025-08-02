from pydantic import BaseModel

class KelimeSesUyumBase(BaseModel):
    question_text: str
    option_a_image: str
    option_b_image: str
    option_c_image: str
    correct_answer: str
    level: str
    exercise_id: int


class KelimeSesUyumRead(KelimeSesUyumBase):
    id: int

    class Config:
        from_attributes = True
