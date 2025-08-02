from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from app.models.reading_text_data import ReadingTextData


def get_edit_distance(s1: str, s2: str) -> int:
    """Levenshtein mesafesini hesaplar."""
    if len(s1) < len(s2):
        return get_edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def calculate_similarity(s1: str, s2: str) -> float:
    """İki kelime arasındaki benzerlik oranını % olarak hesaplar."""
    if not s1 or not s2:
        return 0.0
    longer_len = max(len(s1), len(s2))
    if longer_len == 0:
        return 1.0
    return (longer_len - get_edit_distance(s1, s2)) / longer_len


def calculate_difficulty_for_word(correct_word: str, user_word: str) -> str:
    """Tek bir kelime çifti için zorluk seviyesi belirler."""
    similarity = calculate_similarity(correct_word, user_word)
    if similarity >= 0.7: return "easy"
    if similarity >= 0.3: return "medium"
    if similarity < 0.3: return "very_hard"
    return "hard"


async def get_unresolved_flashcards(db: AsyncSession, user_id: int) -> list:
    """
    Kullanıcının çözülmemiş kelimelerini flashcard'a dönüştürür.
    Eğer 'doğru kelimeler' listesi boşsa, 'yanlış kelimeleri' pratik ettirir.
    """
    query = (
        select(ReadingTextData)
        .where(
            ReadingTextData.user_id == user_id,
            ReadingTextData.is_resolved_data == False
        )
    )
    result = await db.execute(query)
    db_rows = result.scalars().all()

    all_flashcards = []

    for row in db_rows:
        if not row.yanlış_söylenen_kelimeler:
            logging.warning(f"DB Satır ID {row.id} atlanıyor: 'yanlış_söylenen_kelimeler' alanı boş.")
            continue

        incorrect_words = [word.strip() for word in row.yanlış_söylenen_kelimeler.split(',') if word.strip()]

        dogru_kelimeler_str = row.yanlış_kelimelerin_yerine_söylenen_kelimeler

        if not dogru_kelimeler_str:
            logging.info(f"DB Satır ID {row.id}: Doğru kelime listesi boş. Yanlış kelimeler pratik edilecek.")
            correct_words = incorrect_words
        else:
            correct_words = [w.strip() for w in dogru_kelimeler_str.split(',') if w.strip()]
            if len(incorrect_words) != len(correct_words):
                logging.error(f"DB Satır ID {row.id} atlanıyor: Kelime sayıları eşleşmiyor.")
                continue

        for index, (user_word, correct_word) in enumerate(zip(incorrect_words, correct_words)):
            unique_card_id = f"{row.id}-{index}"

            difficulty = calculate_difficulty_for_word(correct_word, user_word)
            similarity = round(calculate_similarity(correct_word, user_word) * 100)

            flashcard = {
                "id": unique_card_id,
                "db_row_id": row.id,
                "correct_word": correct_word,
                "user_pronunciation": user_word,
                "difficulty_level": difficulty,
                "similarity_score": similarity,
                "word_type": "Kelime",
                "description": "Bu kelimeyi doğru telaffuz etmeye çalışın.",
                "error_type": "Telaffuz Hatası"
            }
            all_flashcards.append(flashcard)

    logging.info(f"User {user_id} için toplam {len(all_flashcards)} adet flashcard oluşturuldu.")
    return all_flashcards


async def mark_word_as_resolved(db: AsyncSession, db_row_id: int, word_index: int, user_id: int) -> bool:
    """
    Belirli bir veritabanı satırındaki, belirli bir indeksteki kelimeyi "çözüldü" olarak işaretler.
    Bunu, kelimeyi virgüllü listeden çıkartarak yapar.
    Eğer listede başka kelime kalmazsa, ana kaydın 'is_resolved_data' bayrağını True yapar.
    """
    query = select(ReadingTextData).where(
        ReadingTextData.id == db_row_id,
        ReadingTextData.user_id == user_id
    )
    result = await db.execute(query)
    card_row = result.scalar_one_or_none()

    if not card_row:
        logging.error(f"Kayıt bulunamadı: db_row_id={db_row_id}, user_id={user_id}")
        return False

    incorrect_list = [word.strip() for word in card_row.yanlış_söylenen_kelimeler.split(',') if word.strip()]

    correct_list_str = card_row.yanlış_kelimelerin_yerine_söylenen_kelimeler
    correct_list = [w.strip() for w in correct_list_str.split(',') if w.strip()] if correct_list_str else []

    if not (0 <= word_index < len(incorrect_list)):
        logging.error(f"Geçersiz index: Kayıtta {len(incorrect_list)} kelime var, ama index {word_index} istendi.")
        return False

    removed_incorrect_word = incorrect_list.pop(word_index)

    if 0 <= word_index < len(correct_list):
        correct_list.pop(word_index)

    logging.info(f"'{removed_incorrect_word}' kelimesi kayıttan kaldırıldı. Kalan kelime sayısı: {len(incorrect_list)}")

    if not incorrect_list:
        logging.info(f"DB Satır ID {db_row_id} için tüm kelimeler çözüldü. Kayıt kapatılıyor.")
        card_row.is_resolved_data = True
        card_row.yanlış_söylenen_kelimeler = ""
        card_row.yanlış_kelimelerin_yerine_söylenen_kelimeler = ""
    else:
        card_row.yanlış_söylenen_kelimeler = ", ".join(incorrect_list)
        card_row.yanlış_kelimelerin_yerine_söylenen_kelimeler = ", ".join(correct_list)

    await db.commit()
    return True
