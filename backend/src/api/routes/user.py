"""User API routes - alias for auth signup to avoid NextAuth conflict."""

from fastapi import APIRouter

from src.api.deps import DbSession
from src.schemas.auth import EmailSignupRequest, TokenResponse
from src.api.routes.auth import signup as auth_signup

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/signup", response_model=TokenResponse)
async def signup(request: EmailSignupRequest, db: DbSession):
    """Register a new user with email and password.
    
    This is an alias for /auth/signup to avoid NextAuth route conflicts
    on the frontend (/api/auth/* is reserved by NextAuth).
    """
    return await auth_signup(request, db)
