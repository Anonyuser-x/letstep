from pydantic import BaseModel, EmailStr

class EmailSchema(BaseModel):
    email: EmailStr

class PasswordResetSchema(BaseModel):
    new_password: str