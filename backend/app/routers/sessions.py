import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.session import (
    CaseReorderRequest,
    SessionCounts,
    SessionCreate,
    SessionDetailResponse,
    SessionResponse,
    SessionUpdate,
    TestCaseCreate,
    TestCaseResponse,
)
from app.services import session_service

router = APIRouter()


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test session",
)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new session in draft status with specified ticket information."""
    return await session_service.create_session(db, current_user, payload)


@router.get(
    "/{id}",
    response_model=SessionDetailResponse,
    summary="Get session details and test cases",
)
async def get_session(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full session header, ordered cases, steps, attachments, and execution status counts."""
    session, counts = await session_service.get_session_detail(db, id, current_user)
    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        ticket_no=session.ticket_no,
        ticket_title=session.ticket_title,
        environment=session.environment,
        test_date=session.test_date,
        testing_types=session.testing_types,
        tc_prefix=session.tc_prefix,
        tc_counter=session.tc_counter,
        status=session.status,
        deleted_at=session.deleted_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        cases=session.test_cases,
        counts=counts,
    )


@router.put(
    "/{id}",
    response_model=SessionResponse,
    summary="Update session header",
)
async def update_session(
    id: uuid.UUID,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partial update of session header fields."""
    return await session_service.update_session_header(db, id, current_user, payload)


@router.post(
    "/{id}/complete",
    response_model=SessionCounts,
    summary="Mark session as completed",
)
async def complete_session(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark session as completed and return test execution counts."""
    return await session_service.complete_session(db, id, current_user)


@router.post(
    "/{id}/cases",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a test case in session",
)
async def create_case(
    id: uuid.UUID,
    payload: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Append a new test case to the session with the next sequential TC ID."""
    return await session_service.create_test_case(db, id, current_user, payload)


@router.put(
    "/{id}/cases/reorder",
    response_model=List[TestCaseResponse],
    summary="Reorder test cases in session",
)
async def reorder_cases(
    id: uuid.UUID,
    payload: CaseReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder test cases by updating their positions and recomputing attachment figure numbers."""
    return await session_service.reorder_test_cases(db, id, current_user, payload)
