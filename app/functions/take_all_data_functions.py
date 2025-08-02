import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import UserActivity, UserExercise

async def get_user_activity_dataframe(db: AsyncSession, user_id: int) -> pd.DataFrame | None:
    query = select(UserActivity).where(UserActivity.user_id == user_id).order_by(UserActivity.datetime.asc())
    result = await db.execute(query)
    activities = result.scalars().all()

    if not activities:
        return None

    data_list = [
        {
            "user_id": act.user_id,
            "datetime": act.datetime,
            "Yanıt Süresi (sn)": act.reaction_time,
            "Tekrar Sayısı": act.repeat_count,
            "Oyun Tipi": act.game_type,
            "Kategori_kod": act.category,
            "Öğrencinin Cevabı": act.selected_answer,
            "Doğru Cevap": act.correct_answer,
            "day_of_week": act.day_of_week,
            "student_profile": act.student_profile,
            "question_id": act.question_id,
            "Hata_Tipi_kod": act.wrong_type
        }
        for act in activities
    ]

    return pd.DataFrame(data_list)


async def get_user_exercise_summary_dataframe(db: AsyncSession, user_id: int) -> pd.DataFrame | None:
    query = select(UserExercise).where(UserExercise.user_id == user_id)
    result = await db.execute(query)
    exercises = result.scalars().all()

    if not exercises:
        return None

    data_list = [
        {
            "user_id": ex.user_id,
            "exercise_id": ex.exercise_id,
            "game_type": ex.game_type,
            "total_questions": ex.total_questions,
            "correct_answer": ex.correct_answer,
            "wrong_answer": ex.wrong_answer,
        }
        for ex in exercises
    ]

    return pd.DataFrame(data_list)