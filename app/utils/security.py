from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    print(f"[DEBUG-HASH] Hash'lenecek Düz Şifre: '{plain_password}'")
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[ERROR] verify_password() içinde hata: {e}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "sub": str(data.get("sub"))
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        print(f"[ERROR] JWT decode başarısız: {e}")
        raise ValueError("Geçersiz veya süresi dolmuş token")


async def authenticate_user(db: AsyncSession, username_or_email: str, plain_password: str) -> Optional[User]:
    query = select(User).where(
        or_(User.username == username_or_email, User.email == username_or_email)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(plain_password, user.hashed_password):
        if not user:
            print(f"[DEBUG-AUTH] Kullanıcı bulunamadı: '{username_or_email}'")
        else:
            print(f"[DEBUG-AUTH] '{user.username}' için şifre eşleşmedi.")
            print(f"    -> Gelen Şifre: '{plain_password}'")
            print(f"    -> DB Hash:     '{user.hashed_password}'")

        return None

    print(f"[DEBUG-AUTH] Kullanıcı '{user.username}' başarıyla doğrulandı.")
    return user


def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": email,
        "scope": "password_reset"
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        if payload.get("scope") != "password_reset":
            return None

        email: Optional[str] = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None