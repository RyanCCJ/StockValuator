"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.api.deps import CurrentUser, DbSession
from src.schemas.auth import (
    EmailLoginRequest,
    EmailSignupRequest,
    TokenResponse,
    UserResponse,
)
from src.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=TokenResponse)
async def signup(request: EmailSignupRequest, db: DbSession):
    """Register a new user with email and password."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = await create_user(db, request.email, request.password)
    await db.commit()

    # Generate token
    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(request: EmailLoginRequest, db: DbSession):
    """Authenticate user with email and password."""
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get the current authenticated user's information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        theme_preference=current_user.theme_preference.value,
        base_currency=current_user.base_currency,
    )


class GoogleAuthRequest(BaseModel):
    """Google OAuth token exchange request."""

    email: str
    google_id: str


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: DbSession):
    """Authenticate or register user via Google OAuth."""
    from src.services.auth_service import get_user_by_google_id, get_user_by_email

    # Try to find user by Google ID first
    user = await get_user_by_google_id(db, request.google_id)

    if not user:
        # Try to find by email
        user = await get_user_by_email(db, request.email)
        if user:
            # Link Google ID to existing user
            user.google_id = request.google_id
            await db.flush()
        else:
            # Create new user
            from src.models.user import User
            user = User(
                email=request.email,
                google_id=request.google_id,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)

    await db.commit()

    # Generate token
    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)
