import re
import uuid
from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_str(value: str) -> str:
    """Validate and normalize email string to lowercase, supporting both public and local domains."""
    if not isinstance(value, str):
        raise ValueError("Email must be a string")
    v = value.strip().lower()
    if not EMAIL_REGEX.match(v):
        raise ValueError("Invalid email address format")
    return v


EmailStrType = Annotated[str, BeforeValidator(validate_email_str)]


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    email: EmailStrType = Field(..., description="Unique email address")
    role: str = Field("user", description="User role: 'admin' or 'user'")


class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    email: EmailStrType = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    role: Optional[str] = Field(None, description="Optional role (defaults to 'user' for subsequent users)")


class UserLogin(BaseModel):
    email: EmailStrType = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStrType] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)
