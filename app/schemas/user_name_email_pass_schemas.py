from pydantic import BaseModel, EmailStr

class UsernameUpdate(BaseModel):
    new_username: str

class EmailUpdate(BaseModel):
    new_email: EmailStr

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class InvitationCodeRead(BaseModel):
    invitation_code: str