import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.user_setting import UserSetting


async def count_users(db: AsyncSession) -> int:
    """Return total number of users in the database."""
    result = await db.execute(select(func.count(User.id)))
    return result.scalar_one() or 0


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Retrieve a user by their UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their lowercase email address."""
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower().strip()))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
    role: str = "user",
) -> User:
    """Create a new user with Argon2 password hash and initialized user settings."""
    password_hash = get_password_hash(password)
    user = User(
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=password_hash,
        role=role,
    )
    db.add(user)
    await db.flush()

    # Initialize default user settings
    user_setting = UserSetting(
        user_id=user.id,
        default_environment="development",
        ai_style_prompt=None,
    )
    db.add(user_setting)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """Authenticate user with email and password. Returns User if valid, None otherwise."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
