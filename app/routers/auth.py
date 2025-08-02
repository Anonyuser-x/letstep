from fastapi import APIRouter, Depends, status
from fastapi.responses import  JSONResponse # JSONResponse'u da import edebiliriz
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserRead, LoginRequest, TokenResponse, EmailSchema, PasswordResetSchema
from app.models import User
from app.datab import get_async_db

# --- GÜNCELLENDİ: Fonksiyon importları ---
# register_user yerine yeni fonksiyonlarımızı import ediyoruz.
from app.functions.auth_functions import (
    register_student,
    register_teacher,
    process_user_login,
    process_forgot_password,
    process_password_reset
)
from app.utils import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# --- ESKİ ENDPOINT (ARTIK KULLANILMAYACAK) ---
# @router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
# async def register(user_create: UserCreate, db: AsyncSession = Depends(get_async_db)):
#     return await register_user(db, user_create)


# --- YENİ: Öğrenci Kayıt Endpoint'i ---
@router.post("/register/student", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_student(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Yeni bir öğrenci kullanıcısı kaydeder.
    Kullanıcı verileri (username, email, password, age) gönderilir.
    Başarılı olursa 201 Created döner ve yeni kullanıcı bilgilerini döndürür.
    """
    return await register_student(db, user_data)


# --- YENİ: Öğretmen Kayıt Endpoint'i ---
@router.post("/register/teacher", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_teacher(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Yeni bir öğretmen kullanıcısı kaydeder.
    Kullanıcı verileri (username, email, password, age) gönderilir.
    Başarılı olursa 201 Created döner ve yeni kullanıcı bilgilerini döndürür.
    """
    # Gelen veriler UserCreate şeması ile doğrulanır ve register_teacher fonksiyonuna gönderilir.
    return await register_teacher(db, user_data)


@router.post("/login") # response_model'i kaldırdık çünkü process_user_login zaten bir JSONResponse döndürüyor.
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Kullanıcı girişi yapar. Başarılı girişte access_token'ı httpOnly cookie olarak set eder.
    """
    # Bu fonksiyonu önceden güncellemiştik, artık role bilgisini token'a ekliyor.
    return await process_user_login(db, login_data)


@router.get("/logout")
async def logout():
    # Frontend'in yönlendirmeyi daha iyi yönetebilmesi için RedirectResponse yerine JSONResponse dönebiliriz.
    response = JSONResponse(content={"message": "Çıkış başarılı"})
    response.delete_cookie("access_token")
    return response


@router.post("/forgot-password")
async def forgot_password(email_data: EmailSchema, db: AsyncSession = Depends(get_async_db)):
    return await process_forgot_password(db, email_data)


@router.post("/reset-password")
async def reset_password(token: str, new_password_data: PasswordResetSchema, db: AsyncSession = Depends(get_async_db)):
    return await process_password_reset(db, token, new_password_data)


@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Giriş yapmış olan kullanıcının bilgilerini döndürür.
    Token'dan kullanıcıyı çözer ve döndürür. Bu sayede frontend kullanıcının rolünü de görebilir.
    """
    return current_user