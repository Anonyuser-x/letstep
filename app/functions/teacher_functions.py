from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from app.models import User, UserActivity,UserExercise
from fastapi import HTTPException

async def get_teacher_dashboard_stats(db: AsyncSession, teacher: User) -> dict:

    await db.refresh(teacher, attribute_names=['students'])
    total_students_count = len(teacher.students)

    if total_students_count == 0:
        return {
            "total_students": 0,
            "today_exercise_count": 0,
            "assigned_homeworks": 0
        }

    student_ids = [student.id for student in teacher.students]

    today_start = datetime.combine(date.today(), datetime.min.time())

    query_today_activity = select(func.count(UserActivity.id)).where(
        UserActivity.user_id.in_(student_ids),
        UserActivity.datetime >= today_start
    )
    today_activity_count = await db.scalar(query_today_activity)
    assigned_homeworks_count = 0

    return {
        "total_students": total_students_count,
        "today_exercise_count": today_activity_count,
        "assigned_homeworks": assigned_homeworks_count
    }


async def get_exercise_summary_by_student(db: AsyncSession, teacher: User) -> list:
    await db.refresh(teacher, attribute_names=['students'])
    if not teacher.students:
        return []

    student_ids = [student.id for student in teacher.students]

    query = (
        select(
            User.username,
            UserExercise.game_type,
            func.count(UserExercise.id).label("exercise_count")
        )
        .join(User, UserExercise.user_id == User.id)
        .where(UserExercise.user_id.in_(student_ids))
        .group_by(User.username, UserExercise.game_type)
        .order_by(User.username)
    )

    result = await db.execute(query)
    summaries = result.all()

    summary_list = [
        {
            "student_name": summary.username,
            "exercise_name": summary.game_type,
            "count": summary.exercise_count,
        }
        for summary in summaries
    ]

    return summary_list


async def remove_student_from_teacher_list(db: AsyncSession, teacher: User, student_id: int):
    """
    Belirtilen öğrenciyi, öğretmenin öğrenci listesinden kaldırır.
    """
    # Önce öğrencinin var olup olmadığını ve bu öğretmene ait olup olmadığını kontrol et
    await db.refresh(teacher, attribute_names=['students'])

    student_to_remove = None
    for student in teacher.students:
        if student.id == student_id:
            student_to_remove = student
            break

    if not student_to_remove:
        # Eğer öğrenci bulunamazsa veya öğretmene ait değilse, hata döndür.
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı veya size atanmamış.")

    # Öğrenciyi öğretmenin listesinden kaldır
    teacher.students.remove(student_to_remove)

    # Değişiklikleri veritabanına işle
    await db.commit()

    return  # Başarılı olunca bir şey döndürmeye gerek yok