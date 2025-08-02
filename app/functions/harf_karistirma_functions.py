from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Exercise,UserActivity,HarfKaristirmaQuestion,UserExercise
import random
import string
from sqlalchemy.future import select

async def get_questions_by_level(db: AsyncSession, level: str):
    result = await db.execute(select(HarfKaristirmaQuestion).where(HarfKaristirmaQuestion.level == level))
    questions = result.scalars().all()

    if not questions:
        return {"error": "Soru bulunamadı"}

    sampled_questions = random.sample(questions, min(10, len(questions)))

    exercise_id = sampled_questions[0].exercise_id
    ex_result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = ex_result.scalar()

    return {
        "exercise": {
            "id": exercise.id,
            "game_type": exercise.game_type,
            "category": exercise.category
        },
        "questions": [q.__dict__ for q in sampled_questions]
    }

def normalize_answer(text: str) -> str:
    if not isinstance(text, str):
        return ""

    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))

    text = text.lower()
    text = text.translate(translator)
    text = " ".join(text.split())

    return text

async def submit_answer(db: AsyncSession, user_id: int, payload: dict):
    result = await db.execute(
        select(HarfKaristirmaQuestion).where(HarfKaristirmaQuestion.id == payload["question_id"]))
    question = result.scalar()

    ex_result = await db.execute(select(Exercise).where(Exercise.id == payload["exercise_id"]))
    exercise = ex_result.scalar()

    if not question or not exercise:
        return {"error": "Soru ya da egzersiz bulunamadı."}

    selected_normalized = normalize_answer(payload["selected_answer"])
    correct_normalized = normalize_answer(question.correct_answer)

    is_correct = selected_normalized == correct_normalized

    if not is_correct:
        existing_activity_result = await db.execute(
            select(UserActivity).where(
                UserActivity.user_id == user_id,
                UserActivity.question_id == question.id,
                UserActivity.is_resolved == False
            )
        )
        existing_activity = existing_activity_result.scalars().first()

        if existing_activity:

            existing_activity.repeat_count += 1
            existing_activity.datetime = datetime.utcnow()
            existing_activity.day_of_week = datetime.utcnow().strftime('%A')

        else:
            new_activity = UserActivity(
                user_id=user_id,
                datetime=datetime.utcnow(),
                day_of_week=datetime.utcnow().strftime('%A'),
                game_type=exercise.game_type,
                category=exercise.category,
                is_resolved=False,
                selected_answer=payload["selected_answer"],
                correct_answer=question.correct_answer,
                wrong_type=exercise.category,
                student_profile=payload["level"],
                question_id=question.id,
                reaction_time=payload["reaction_time"],
                repeat_count=1
            )

            db.add(new_activity)

        await db.flush()

        await db.commit()

    return {
        "correct": is_correct,
        "correct_answer": question.correct_answer,
        "question_id": question.id
    }

async def save_user_exercise_summary(db: AsyncSession, summary_data: dict):

    ex_result = await db.execute(select(Exercise).where(Exercise.id == summary_data["exercise_id"]))
    exercise = ex_result.scalar()

    if not exercise:
        return {"error": "İlgili egzersiz bulunamadı."}

    new_user_exercise = UserExercise(
        user_id=summary_data["user_id"],
        exercise_id=summary_data["exercise_id"],
        game_type=exercise.game_type,
        total_questions=summary_data["total_questions"],
        correct_answer=summary_data["correct_answers"],
        wrong_answer=summary_data["wrong_answers"]
    )
    db.add(new_user_exercise)
    await db.commit()
    await db.refresh(new_user_exercise)

    return {"message": "Egzersiz özeti başarıyla kaydedildi.", "summary_id": new_user_exercise.id}