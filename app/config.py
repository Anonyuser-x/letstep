from pydantic import Field, validator, EmailStr
from pydantic_settings import BaseSettings
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    APP_NAME: str = "Awesome Auth API"
    DEBUG: bool = False

    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SYNC_DATABASE_URL: str = Field(..., env="SYNC_DATABASE_URL")

    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")

    MAIL_USERNAME: EmailStr = Field(..., alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(..., alias="MAIL_PASSWORD")
    MAIL_FROM: EmailStr = Field(..., alias="MAIL_FROM")
    MAIL_PORT: int = Field(587, alias="MAIL_PORT")
    MAIL_SERVER: str = Field("smtp.gmail.com", alias="MAIL_SERVER")
    MAIL_STARTTLS: bool = Field(True, alias="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(False, alias="MAIL_SSL_TLS")
    USE_CREDENTIALS: bool = Field(True, alias="USE_CREDENTIALS")
    VALIDATE_CERTS: bool = Field(True, alias="VALIDATE_CERTS")

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(15, alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    @validator("JWT_SECRET_KEY")
    def check_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

def get_settings():
    return settings

