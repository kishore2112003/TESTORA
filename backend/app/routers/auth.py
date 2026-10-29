from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.routers.deps import get_current_user, get_current_user_optional
from app.schemas.user import (
    ChangePasswordRequest,
    LoginResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services import user_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description=(
        "Registers the initial admin if no users exist. Once at least one user exists, "
        "only authenticated administrators can register subsequent users."
    ),
)
async def register(
    user_in: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Check if this email is already registered
    existing_user = await user_service.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_count = await user_service.count_users(db)

    if user_count == 0:
        # First registered user becomes admin automatically
        assigned_role = "admin"
    else:
        # Subsequent registrations require an authenticated admin
        current_user = await get_current_user_optional(request, db)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to register new users",
            )
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration requires admin privileges",
            )
        assigned_role = user_in.role if user_in.role in ["admin", "user"] else "user"

    created_user = await user_service.create_user(
        db=db,
        name=user_in.name,
        email=user_in.email,
        password=user_in.password,
        role=assigned_role,
    )
    return created_user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in user",
    description="Authenticates credentials and sets an httpOnly session cookie with JWT token.",
)
async def login(
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Generate JWT
    token = create_access_token(subject=str(user.id))

    # Set httpOnly cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE.lower(),
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return LoginResponse(
        message="Login successful",
        user=UserResponse.model_validate(user),
        access_token=token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    summary="Log out user",
    description="Clears the authentication session cookie.",
)
async def logout(response: Response):
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE.lower(),
        secure=settings.COOKIE_SECURE,
        httponly=True,
    )
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns profile information for the currently authenticated user.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/change-password",
    summary="Change user password",
    description="Changes password for currently authenticated user after verifying current password.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await user_service.change_user_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {"message": "Password changed successfully"}

