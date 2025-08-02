from pydantic import BaseModel


class FlashcardResponse(BaseModel):
    id: str
    db_row_id: int
    correct_word: str
    user_pronunciation: str
    difficulty_level: str
    similarity_score: int
    word_type: str
    description: str
    error_type: str

    class Config:
        from_attributes = True