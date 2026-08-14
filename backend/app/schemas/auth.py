from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    fullName: str = Field(..., min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirmRequest(BaseModel):
    token: str
    newPassword: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: str
    email: str
    fullName: str
    isActive: bool
    isVerified: bool
    roles: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: str
    deviceInfo: str
    ipAddress: str
    isActive: bool
    expiresAt: str
    createdAt: str
    isCurrentSession: bool = False

    model_config = ConfigDict(from_attributes=True)


class AuthStatusResponse(BaseModel):
    user: UserResponse
    currentSessionId: str
