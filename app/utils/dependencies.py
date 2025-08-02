from fastapi import Depends, HTTPException, status, Request,Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from typing import Optional
from app.datab import get_async_db
from app.models import User,UserRole
from sqlalchemy import select,exists
from app.models.auth_model import student_teacher_association
from app.utils import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Optional[User]:
    token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        return None

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()
    return user



async def get_current_teacher_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.role != UserRole.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu sayfaya erişim yetkiniz yok."
        )
    return current_user


async def get_teacher_and_check_student_access(
        student_id: int = Path(..., title="The ID of the student to retrieve"),
        current_teacher: User = Depends(get_current_teacher_user),
        db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Güvenlik öncelikli yetki kontrolü yapar.

    1. ÖNCELİKLE, giriş yapmış öğretmenin istenen öğrenci ID'sine erişim
       hakkı olup olmadığını kontrol eder.
    2. Eğer yetkisi yoksa, başka hiçbir kontrol yapmadan DERHAL 403 hatası döndürür.
    3. Eğer yetkisi varsa, öğrenci verisini getirir ve döndürür.
    """
    # 1. Adım: ÖNCE YETKİYİ KONTROL ET
    # Giriş yapmış öğretmen ile talep edilen öğrenci arasında bir ilişki var mı?
    association_query = (
        exists()
        .where(student_teacher_association.c.teacher_id == current_teacher.id)
        .where(student_teacher_association.c.student_id == student_id)
    ).select()

    has_access = (await db.execute(association_query)).scalar()

    # 2. Adım: YETKİ YOKSA, DERHAL ENGELLE
    if not has_access:
        # Bu en önemli güvenlik adımıdır. Öğrencinin var olup olmadığını
        # veya verisi olup olmadığını kontrol etmeden önce yetkisiz
        # erişimi engelliyoruz.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu öğrencinin verilerini görüntüleme yetkiniz bulunmamaktadır."
        )

    # 3. Adım: YETKİ VARSA, ÖĞRENCİ BİLGİSİNİ GETİR
    # Bu koda sadece yetki kontrolü başarılı olursa ulaşılabilir.
    student_query = select(User).where(User.id == student_id, User.role == UserRole.student)
    result = await db.execute(student_query)
    target_student = result.scalar_one_or_none()

    # (Veri Bütünlüğü Kontrolü) Yetki var ama öğrenci silinmişse ne olur?
    if not target_student:
        # Bu durum normalde olmamalıdır (ilişki var ama kullanıcı yok).
        # Ama olursa, 404 hatası vermek mantıklıdır.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Yetkiniz olan ID'si {student_id} olan öğrenci sistemde bulunamadı. Lütfen yönetici ile iletişime geçin."
        )

    return target_student

async def get_current_user_id(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user