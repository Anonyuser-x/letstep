from fastapi import APIRouter, Depends, status
from fastapi.responses import  JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserRead, LoginRequest, TokenResponse, EmailSchema, PasswordResetSchema
from app.models import User
from app.datab import get_async_db


from app.functions.auth_functions import (
    register_student,
    register_teacher,
    process_user_login,
    process_forgot_password,
    process_password_reset
)
from app.utils import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register/student", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_student(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    return await register_student(db, user_data)


@router.post("/register/teacher", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_teacher(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    return await register_teacher(db, user_data)


@router.post("/login") 
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    return await process_user_login(db, login_data)


@router.get("/logout")
async def logout():
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
    return current_user
