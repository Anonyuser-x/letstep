from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas import UserRead,StudentAssociationRequest
from app.datab import get_async_db
from app.functions import teacher_functions
from app.utils import get_current_teacher_user
from app.functions import teacher_user_add_functions

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"],
)


@router.get("/my-students")
async def get_my_students_for_teacher(
    db: AsyncSession = Depends(get_async_db),
    current_teacher: User = Depends(get_current_teacher_user)
):


    await db.refresh(current_teacher, attribute_names=['students'])
    students = current_teacher.students

    return [{"id": student.id, "username": student.username, "email": student.email} for student in students]


@router.post("/associate-student", response_model=UserRead)
async def associate_student(
        association_data: StudentAssociationRequest,
        db: AsyncSession = Depends(get_async_db),
        current_teacher: User = Depends(get_current_teacher_user)
):

    student = await teacher_user_add_functions.associate_student_to_teacher(
        db=db,
        teacher=current_teacher,
        invitation_code=association_data.invitation_code
    )

    return student

@router.get("/dashboard-stats", tags=["Öğretmen Paneli"])
async def get_dashboard_stats_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_teacher: User = Depends(get_current_teacher_user)
):
    stats = await teacher_functions.get_teacher_dashboard_stats(db, teacher=current_teacher)
    return stats

@router.get("/exercise-summary", tags=["Öğretmen Paneli"])
async def get_exercise_summary_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_teacher: User = Depends(get_current_teacher_user)
):
    summary = await teacher_functions.get_exercise_summary_by_student(db, teacher=current_teacher)
    return summary


@router.delete("/my-students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Öğretmen Paneli"])
async def delete_student_association(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_teacher: User = Depends(get_current_teacher_user)
):
    """
    Bir öğrenciyi öğretmenin listesinden kaldırır.
    """
    await teacher_functions.remove_student_from_teacher_list(
        db=db,
        teacher=current_teacher,
        student_id=student_id
    )
    return