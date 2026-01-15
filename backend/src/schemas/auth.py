"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class GoogleAuthRequest(BaseModel):
    """Google OAuth token verification request."""

    id_token: str


class EmailLoginRequest(BaseModel):
    """Email/password login request."""

    email: EmailStr
    password: str


class EmailSignupRequest(BaseModel):
    """Email/password signup request."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    theme_preference: str
    base_currency: str

    model_config = {"from_attributes": True}
