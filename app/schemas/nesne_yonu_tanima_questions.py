from pydantic import BaseModel

class NesneYonuTanimaBase(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    correct_answer: str
    level: str
    exercise_id: int
    question_image:str

class NesneYonuTanimaRead(NesneYonuTanimaBase):
    id: int

    class Config:
        from_attributes = True
