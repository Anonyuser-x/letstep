from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.datab import get_async_db
from app.utils.dependencies import get_current_user
from app.functions import security_functions
from app.schemas import UsernameUpdate, EmailUpdate, PasswordUpdate, UserRead, InvitationCodeRead

router = APIRouter(prefix="/api/user", tags=["User Management"])

@router.put("/username", response_model=UserRead)
async def update_username(
    username_data: UsernameUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await security_functions.update_user_username(db, current_user, username_data)

@router.put("/email", response_model=UserRead)
async def update_email(
    email_data: EmailUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await security_functions.update_user_email(db, current_user, email_data)

@router.put("/password")
async def update_password(
    password_data: PasswordUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    await security_functions.update_user_password(db, current_user, password_data)
    return {"message": "Şifreniz başarıyla güncellendi."}

@router.post("/invitation-code/regenerate", response_model=InvitationCodeRead)
async def regenerate_code(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    user = await security_functions.regenerate_invitation_code(db, current_user)
    return user