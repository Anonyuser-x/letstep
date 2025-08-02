from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from app.config import conf
# --- GÜNCELLENDİ ---
# Modelimizden UserRole Enum'ını da import ediyoruz.
from app.models import User, UserRole
from app.schemas import UserCreate, LoginRequest, EmailSchema, PasswordResetSchema
from app.utils import (
    is_strong_password, is_valid_email, BadRequestException,
    authenticate_user, create_access_token,
    create_password_reset_token, verify_password_reset_token)
from fastapi_mail import FastMail, MessageSchema

# --- YENİDEN ADLANDIRILDI ---
# Bu fonksiyon artık spesifik olarak öğrenci kaydı için kullanılacak.
# Kodun okunabilirliği için adını değiştirmek iyi bir pratiktir.
async def register_student(db: AsyncSession, user_data: UserCreate) -> User:
    if not is_valid_email(user_data.email):
        raise BadRequestException("Geçersiz email adresi.")
    if not is_strong_password(user_data.password):
        raise BadRequestException("Şifre yeterince güçlü değil.")

    query = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise BadRequestException("Kullanıcı adı veya email zaten kayıtlı.")

    from app.utils.security import hash_password
    hashed_pwd = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        age=user_data.age
        # role alanı modeldeki default='student' sayesinde otomatik atanacak.
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# --- YENİ EKLENDİ ---
# Öğretmen kaydı için yeni fonksiyonumuz.
async def register_teacher(db: AsyncSession, user_data: UserCreate) -> User:
    # Bütün doğrulamalar öğrenci kaydı ile aynı.
    if not is_valid_email(user_data.email):
        raise BadRequestException("Geçersiz email adresi.")
    if not is_strong_password(user_data.password):
        raise BadRequestException("Şifre yeterince güçlü değil.")

    query = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise BadRequestException("Kullanıcı adı veya email zaten kayıtlı.")

    from app.utils.security import hash_password
    hashed_pwd = hash_password(user_data.password)

    # TEK FARK BURADA! Rolü manuel olarak 'teacher' olarak belirliyoruz.
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        age=user_data.age, # Öğretmen için yaş zorunlu olmayabilir, şemada opsiyonel bırakılabilir.
        role=UserRole.teacher # Rolü açıkça belirtiyoruz.
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def process_user_login(db: AsyncSession, login_data: LoginRequest) -> dict:
    user = await authenticate_user(
        db=db,
        username_or_email=login_data.username_or_email,
        plain_password=login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı"
        )

    # --- KRİTİK GÜNCELLEME ---
    # Token oluştururken payload'a (içeriğe) kullanıcının rolünü de ekliyoruz.
    # user.role bir Enum nesnesi olduğu için .value ile string değerini ("student", "teacher") alıyoruz.
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value
    }
    token = create_access_token(data=token_data)

    response = JSONResponse(content={"message": "Giriş başarılı"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=1800, # 30 dakika
        samesite="lax",
        secure=False # Production'da True olmalı (HTTPS için)
    )

    return response

# --- Şifre sıfırlama fonksiyonları aynı kalabilir, onlarda değişiklik gerekmiyor. ---

async def send_password_reset_email(email: str, token: str):
    # Bu fonksiyon içeriği aynı kalabilir
    reset_url = f"http://localhost:8000/reset-password?token={token}"
    html = html = f"""
<!DOCTYPE html>
<html lang="tr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Şifre Sıfırlama</title>
  </head>
  <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
    <table width="100%" bgcolor="#f4f4f4" cellpadding="0" cellspacing="0" style="padding: 50px 0;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 40px;">
            <tr>
              <td align="center" style="padding-bottom: 30px;">
                <img src="https://letstep.com/logo.png" alt="LetStep Logo" width="120" />
              </td>
            </tr>
            <tr>
              <td style="color: #333333; font-size: 20px; font-weight: bold; text-align: center;">
                Şifre Sıfırlama Talebiniz Alındı
              </td>
            </tr>
            <tr>
              <td style="padding-top: 20px; color: #555555; font-size: 16px; text-align: center;">
                Merhaba,<br/><br/>
                LetStep hesabınız için bir şifre sıfırlama talebinde bulundunuz. Şifrenizi sıfırlamak için aşağıdaki butona tıklayın:
              </td>
            </tr>
            <tr>
              <td align="center" style="padding: 30px 0;">
                <a href="{reset_url}" style="background-color: #4a90e2; color: white; text-decoration: none; padding: 15px 30px; border-radius: 5px; font-size: 16px; display: inline-block;">
                  Şifremi Sıfırla
                </a>
              </td>
            </tr>
            <tr>
              <td style="color: #999999; font-size: 14px; text-align: center;">
                Eğer bu işlemi siz başlatmadıysanız, bu e-postayı görmezden gelebilirsiniz. Hesabınız güvende.
              </td>
            </tr>
            <tr>
              <td style="padding-top: 30px; color: #aaaaaa; font-size: 13px; text-align: center;">
                Bu e-posta LetStep tarafından otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.
              </td>
            </tr>
            <tr>
              <td align="center" style="padding-top: 20px;">
                <a href="https://letstep.com" style="color: #4a90e2; text-decoration: none; font-size: 14px;">www.letstep.com</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
 # HTML içeriğiniz aynı
    message = MessageSchema(subject="LetStep Şifre Sıfırlama", recipients=[email], body=html, subtype="html")
    fm = FastMail(conf)
    await fm.send_message(message)

async def process_forgot_password(db: AsyncSession, email_data: EmailSchema):
    # Bu fonksiyon içeriği aynı kalabilir
    user = await db.execute(select(User).where(User.email == email_data.email))
    user = user.scalar_one_or_none()
    if not user:
        return {"message": "Eğer bu email adresi sistemde kayıtlıysa, şifre sıfırlama linki gönderildi."}
    token = create_password_reset_token(email=user.email)
    await send_password_reset_email(email=user.email, token=token)
    return {"message": "Eğer bu email adresi sistemde kayıtlıysa, şifre sıfırlama linki gönderildi."}

async def process_password_reset(db: AsyncSession, token: str, new_password_data: PasswordResetSchema):
    # Bu fonksiyon içeriği aynı kalabilir
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş token.")
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if not is_strong_password(new_password_data.new_password):
        raise BadRequestException("Yeni şifre yeterince güçlü değil.")
    from app.utils.security import hash_password
    user.hashed_password = hash_password(new_password_data.new_password)
    await db.commit()
    return {"message": "Şifreniz başarıyla güncellendi."}