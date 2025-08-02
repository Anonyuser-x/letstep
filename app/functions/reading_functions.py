import difflib
import tempfile
import os
import whisper
from fastapi import UploadFile
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReadingTextData, User

ffmpeg_bin_path = r"C:\Users\kemal\Desktop\ProjectDisleksi\ffmpeg\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

NORMALIZATION_MAP = {
    "geliyodu": "geliyordu",
    "gidiyodu": "gidiyordu",
    "açıyodu": "açıyordu",
    "yapıyodu": "yapıyordu",
    "ediyodu": "ediyordu",
    "gelcem": "geleceğim",
    "gidicem": "gideceğim",
    "yapcam": "yapacağım",
    "napıyosun": "ne yapıyorsun",
    "napıyon": "ne yapıyorsun",
    "napcam": "ne yapacağım",
    "napıcam": "ne yapacağım",
    "gelirim": "geleceğim",
    "gelirimki": "geleceğim ki",
    "gelirmiyim": "gelecek miyim",
    "gidiyom": "gidiyorum",
    "geliyom": "geliyorum",
    "yapıyom": "yapıyorum",
    "biliyom": "biliyorum",
    "söylüyom": "söylüyorum",
    "açıyom": "açıyorum",
    "okuyom": "okuyorum",
    "görüyo": "görüyor",
    "biyo": "biliyor",
    "diyo": "diyor",
    "diyoki": "diyor ki",
    "dediki": "dedi ki",
    "dediya": "dedi ya",
    "bi": "bir",
    "noldu": "ne oldu",
    "nolcak": "ne olacak",
    "noolcak": "ne olacak",
    "noluyo": "ne oluyor",
    "noluyo ya": "ne oluyor ya",
    "napıyo": "ne yapıyor",
    "gidiyon": "gidiyorsun",
    "baksana": "bakar mısın",
    "resimini": "resmini",
    "naparsın": "ne yaparsın",
    "görücem": "göreceğim",
    "başlıcam": "başlayacağım",
    "çalışıcam": "çalışacağım",
    "çalıyom": "çalıyorum",
    "alcam": "alacağım",
    "vercem": "vereceğim",
    "veriyom": "veriyorum",
    "yiycem": "yiyeceğim",
    "içicem": "içeceğim",
    "düşünüyodu": "düşünüyordu",
    "bekliyodu": "bekliyordu",
    "okuyodu": "okuyordu",
    "şeydi": "şey idi",
    "şeymiş": "şeymiş",
    "bişey": "bir şey",
    "hiçbişey": "hiçbir şey",
    "herşey": "her şey",
    "şeylerdi": "şeyler idi",
    "annesi ile": "annesiyle",
    "vardında": "vardığında",
    "oynuyodu": "oynuyordu",
    "parkda": "parkta",
    "parlıyodu": "parlıyordu"
}


def normalize_word(word: str) -> str:
    return NORMALIZATION_MAP.get(word, word)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


try:
    model = whisper.load_model("base")
except Exception as e:
    print(f"HATA: Whisper modeli yüklenemedi. Hata: {e}")
    model = None


async def _speech_to_text(audio_file: UploadFile) -> str:
    if not model:
        raise RuntimeError("Whisper modeli yüklenemedi, transkripsiyon yapılamıyor.")

    tmp_path = None
    try:
        suffix = os.path.splitext(audio_file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        result = model.transcribe(tmp_path, fp16=False)
        full_text = result["text"].strip()

        print(f"Whisper Tarafından Çevrilen Metin: '{full_text}'")
        return full_text
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _compare_texts(original: str, transcribed: str) -> dict:
    original_clean = normalize_text(original)
    transcribed_clean = normalize_text(transcribed)

    original_words = [normalize_word(w) for w in original_clean.lower().split()]
    transcribed_words = [normalize_word(w) for w in transcribed_clean.lower().split()]
    print(f"Orijinal Kelimeler: {original_words}")
    print(f"Söylenen Kelimeler: {transcribed_words}")
    diff = list(difflib.ndiff(original_words, transcribed_words))

    missing = [word[2:] for word in diff if word.startswith('- ')]
    extra = [word[2:] for word in diff if word.startswith('+ ')]
    matched = [word[2:] for word in diff if word.startswith('  ')]

    accuracy = (len(matched) / len(original_words)) * 100 if len(original_words) > 0 else 0

    return {
        "original_word_count": len(original_words),
        "spoken_word_count": len(transcribed_words),
        "matched_words": matched,
        "missing_words": missing,
        "extra_words": extra,
        "accuracy_percent": round(accuracy, 2)
    }


async def process_and_compare_reading(
        audio: UploadFile,
        original_text: str,
        text_id: int,
        user: User,
        db: AsyncSession
) -> dict:
    try:
        transcribed_text = await _speech_to_text(audio)

        comparison_result = _compare_texts(original_text, transcribed_text)

        new_reading_data = ReadingTextData(
            user_id=user.id,
            reading_text_id=text_id,
            okuma_dogrulugu=str(comparison_result["accuracy_percent"]),
            yanlış_söylenen_kelimeler=", ".join(comparison_result["missing_words"]),
            yanlış_kelimelerin_yerine_söylenen_kelimeler=", ".join(comparison_result["extra_words"]),
            dogru_kelime_sayısı=f"{len(comparison_result['matched_words'])} / {comparison_result['original_word_count']}"
        )

        db.add(new_reading_data)
        await db.commit()
        await db.refresh(new_reading_data)

        print(f"Kullanıcı {user.id} için okuma verisi ID {new_reading_data.id} ile kaydedildi.")

        return comparison_result

    except Exception as e:
        print(f"Okuma analizi sırasında bir hata oluştu: {e}")
        await db.rollback()
        raise