from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import uuid
from app.models import User
from app.utils.security import hash_password, verify_password
from app.schemas import UsernameUpdate, EmailUpdate, PasswordUpdate  # Bunları schemas.py'de oluşturacağız


# --- Kullanıcı Adı Güncelleme ---
async def update_user_username(db: AsyncSession, user: User, new_username_data: UsernameUpdate) -> User:
    # Yeni kullanıcı adının başkası tarafından kullanılıp kullanılmadığını kontrol et
    existing_user = await db.execute(select(User).where(User.username == new_username_data.new_username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu kullanıcı adı zaten alınmış.")

    user.username = new_username_data.new_username
    await db.commit()
    await db.refresh(user)
    return user


# --- E-posta Güncelleme ---
async def update_user_email(db: AsyncSession, user: User, new_email_data: EmailUpdate) -> User:
    # Yeni e-postanın başkası tarafından kullanılıp kullanılmadığını kontrol et
    existing_user = await db.execute(select(User).where(User.email == new_email_data.new_email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu e-posta adresi zaten kullanılıyor.")

    user.email = new_email_data.new_email
    await db.commit()
    await db.refresh(user)
    return user


# --- Şifre Güncelleme ---
async def update_user_password(db: AsyncSession, user: User, password_data: PasswordUpdate) -> None:
    # Önce mevcut şifrenin doğru olup olmadığını doğrula
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mevcut şifreniz yanlış.")

    # Yeni şifreyi hash'leyerek kaydet
    user.hashed_password = hash_password(password_data.new_password)
    await db.commit()
    # Şifre değiştirildiğinde kullanıcıya bir şey döndürmeye gerek yok, sadece başarı mesajı yeterli.


# --- Davet Kodu Yenileme ---
async def regenerate_invitation_code(db: AsyncSession, user: User) -> User:
    user.invitation_code = str(uuid.uuid4())
    await db.commit()
    await db.refresh(user)
    return user