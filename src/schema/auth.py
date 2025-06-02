from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})


class TokenPayload(BaseModel):
    sub: UUID
    exp: datetime


class UserLogin(BaseModel):
    username: EmailStr | str
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class EmailVerification(BaseModel):
    token: str
