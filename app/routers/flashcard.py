from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.datab import get_async_db
from app.schemas import FlashcardResponse
from app.models import User
from app.utils import get_current_user_id
from app.functions import flashcard_functions

router = APIRouter(
    prefix="/flashcards",
    tags=["Flashcards (Öğrenci)"]
)

# --- Pydantic Modeli: Frontend'den gelecek çözme isteği için ---
class ResolveWordPayload(BaseModel):
    db_row_id: int
    correct_word: str

# --- ROUTER ENDPOINT'LERİ ---

@router.get("/", response_model=List[FlashcardResponse], summary="Öğrencinin Kendi Kartlarını Getir")
async def get_my_flashcards(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_id)
):
    """
    Giriş yapmış öğrencinin tüm çözülmemiş kelimelerini tek tek flashcard olarak getirir.
    """
    flashcards = await flashcard_functions.get_unresolved_flashcards(db, user_id=current_user.id)
    return flashcards

# DEĞİŞTİ: Artık /resolve yerine /{unique_card_id}/resolve kullanıyoruz.
@router.post("/{unique_card_id}/resolve", status_code=status.HTTP_204_NO_CONTENT, summary="Bir Kelimeyi Çözüldü Olarak İşaretle")
async def resolve_a_word(
    unique_card_id: str, # Örnek: '2-0'
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_id)
):
    """
    Giriş yapmış öğrencinin, belirli bir kelimeyi "çözüldü" olarak işaretler.
    ID formatı: '{veritabanı_satır_id}-{kelimenin_listedeki_sırası}'
    """
    try:
        # '2-0' şeklindeki ID'yi ayrıştır
        parts = unique_card_id.split('-')
        db_row_id = int(parts[0])
        word_index = int(parts[1])
    except (ValueError, IndexError):
        # Eğer ID formatı bozuksa (örn: 'abc' veya '2'), 400 Bad Request hatası ver.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz kart ID formatı.")

    success = await flashcard_functions.mark_word_as_resolved(
        db=db,
        db_row_id=db_row_id,
        word_index=word_index,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kelime kaydı bulunamadı veya bu kelimeyi değiştirme yetkiniz yok."
        )

    return None