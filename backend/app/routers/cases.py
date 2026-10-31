import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.session import (
    AttachmentResponse,
    TestCaseResponse,
    TestCaseUpdate,
)
from app.services import session_service

router = APIRouter()


@router.put(
    "/{id}",
    response_model=TestCaseResponse,
    summary="Update test case",
)
async def update_case(
    id: uuid.UUID,
    payload: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update test case fields. If steps is sent, replaces the whole ordered step list."""
    return await session_service.update_test_case(db, id, current_user, payload)


@router.delete(
    "/{id}",
    summary="Delete test case",
)
async def delete_case(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hard delete a test case, its steps, attachments, and files from disk."""
    await session_service.delete_test_case(db, id, current_user)
    return {"message": "Test case deleted successfully"}


@router.post(
    "/{id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image attachment for test case",
)
async def upload_attachment(
    id: uuid.UUID,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and validate an image attachment (PNG, JPEG, WEBP, GIF), recomputing figure numbers."""
    return await session_service.add_attachment(db, id, current_user, file, caption)
