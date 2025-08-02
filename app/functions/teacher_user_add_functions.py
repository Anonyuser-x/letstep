from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import User, UserRole


async def associate_student_to_teacher(db: AsyncSession, teacher: User, invitation_code: str) -> User:
    query = select(User).where(User.invitation_code == invitation_code)
    result = await db.execute(query)
    student_to_add = result.scalar_one_or_none()

    if not student_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu davet koduyla bir kullanıcı bulunamadı.")

    if student_to_add.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu kod bir öğrenciye ait değil.")

    await db.refresh(teacher, attribute_names=['students'])

    if student_to_add in teacher.students:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu öğrenci zaten listenizde mevcut.")

    teacher.students.append(student_to_add)
    await db.commit()
    await db.refresh(student_to_add)

    return student_to_add