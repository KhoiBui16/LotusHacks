from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserPublic


class SignUpRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=20)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

