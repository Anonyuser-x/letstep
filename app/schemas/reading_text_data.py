from pydantic import BaseModel
from typing import Optional


class ReadingTextDataCreate(BaseModel):
    user_id: int
    reading_text_id: int
    okuma_dogrulugu: str
    yanlış_söylenen_kelimeler: str
    yanlış_kelimelerin_yerine_söylenen_kelimeler: str
    dogru_kelime_sayısı: str


class ReadingTextDataUpdate(BaseModel):
    okuma_dogrulugu: Optional[str] = None
    yanlış_söylenen_kelimeler: Optional[str] = None
    yanlış_kelimelerin_yerine_söylenen_kelimeler: Optional[str] = None
    dogru_kelime_sayısı: Optional[str] = None


class ReadingTextDataOut(BaseModel):
    id: int
    user_id: int
    reading_text_id: int
    okuma_dogrulugu: str
    yanlış_söylenen_kelimeler: str
    yanlış_kelimelerin_yerine_söylenen_kelimeler: str
    dogru_kelime_sayısı: str

    class Config:
        from_attributes = True

