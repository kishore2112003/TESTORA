import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.session import (
    AttachmentResponse,
    AttachmentUpdateCaption,
)
from app.services import session_service

router = APIRouter()


@router.put(
    "/{id}",
    response_model=AttachmentResponse,
    summary="Update attachment caption",
)
async def update_attachment(
    id: uuid.UUID,
    payload: AttachmentUpdateCaption,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update caption for an attachment."""
    return await session_service.update_attachment_caption(
        db, id, current_user, payload.caption
    )


@router.delete(
    "/{id}",
    summary="Delete attachment",
)
async def delete_attachment(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an attachment record and remove the file from disk."""
    await session_service.delete_attachment(db, id, current_user)
    return {"message": "Attachment deleted successfully"}


@router.get(
    "/{id}/file",
    summary="Download attachment image file",
)
async def get_attachment_file(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download attachment file with security headers and validated Content-Type."""
    file_path, media_type = await session_service.get_attachment_file_path(
        db, id, current_user
    )

    headers = {
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private",
    }

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers=headers,
    )
