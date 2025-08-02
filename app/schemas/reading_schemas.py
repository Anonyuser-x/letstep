from pydantic import BaseModel

class ReadingTextOut(BaseModel):
    id: int
    paragraph: str

    class Config:
        from_attributes = True
