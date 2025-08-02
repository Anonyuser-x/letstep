from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.functions.reading_functions import process_and_compare_reading
from app.datab import get_async_db
from app.utils.dependencies import get_current_user_id
from app.models import User

router = APIRouter(
    prefix="/reading",
    tags=["Reading Assistant"]
)

@router.post("", summary="Analyze a user's reading audio and save the data")
async def analyze_reading(
    audio: UploadFile = File(..., description="Kullanıcının okuduğu ses dosyası (.webm, .mp3, vb.)"),
    original_text: str = Form(..., description="Karşılaştırılacak orijinal metin"),
    text_id: int = Form(..., description="Okunan metnin veritabanındaki ID'si"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_id)
):
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Geçersiz dosya türü. Lütfen bir ses dosyası yükleyin."
        )

    try:
        result = await process_and_compare_reading(
            audio=audio,
            original_text=original_text,
            text_id=text_id,
            user=current_user,
            db=db
        )
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        print(f"Endpoint hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ses işlenirken beklenmedik bir sunucu hatası oluştu."
        )