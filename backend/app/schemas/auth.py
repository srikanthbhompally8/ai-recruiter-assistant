"""Authentication Schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    class Config:
        example = {
            "email": "user@example.com",
            "password": "SecurePassword123!",
            "full_name": "John Doe"
        }


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

    class Config:
        example = {
            "email": "user@example.com",
            "password": "SecurePassword123!"
        }


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }


class AuthResponse(BaseModel):
    """Complete authentication response"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str
