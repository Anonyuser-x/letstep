from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)
    age: Optional[int] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    age: int | None = None
    role: str
    invitation_code:str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[constr(min_length=3, max_length=50)] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None

class LoginRequest(BaseModel):
    username_or_email: str
    password: constr(min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageResponse(BaseModel):
    message: str
