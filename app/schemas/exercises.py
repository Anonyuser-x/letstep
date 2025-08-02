from pydantic import BaseModel

class ExerciseBase(BaseModel):
    game_type: str
    category: str

class ExerciseRead(ExerciseBase):
    id: int

    class Config:
        from_attributes = True