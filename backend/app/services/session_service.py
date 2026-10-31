import asyncio
import io
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.attachment import Attachment
from app.models.session import Session
from app.models.test_case import TestCase
from app.models.test_step import TestStep
from app.models.user import User
from app.schemas.session import (
    CaseReorderRequest,
    CaseStatusEnum,
    SessionCounts,
    SessionCreate,
    SessionUpdate,
    TestCaseCreate,
    TestCaseUpdate,
)

logger = logging.getLogger(__name__)

# Max allowed pixels to guard against decompression bombs
MAX_IMAGE_PIXELS = 100_000_000

IMAGE_FORMAT_MAP = {
    "PNG": ("png", "image/png"),
    "JPEG": ("jpg", "image/jpeg"),
    "WEBP": ("webp", "image/webp"),
    "GIF": ("gif", "image/gif"),
}


# ---------------------------------------------------------------------------
# Access Control / Retrieval Helpers (Ownership & Soft-Delete)
# ---------------------------------------------------------------------------
async def get_session_or_404(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
) -> Session:
    """Fetch session ensuring non-deleted and owned by user or admin; raises 404 otherwise."""
    stmt = select(Session).where(
        Session.id == session_id,
        Session.deleted_at.is_(None),
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if user.role != "admin" and session.user_id != user.id:
        # Return 404 instead of 403 as required by ownership rules
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return session


async def get_case_or_404(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User,
) -> Tuple[TestCase, Session]:
    """Fetch test case and its parent session verifying ownership and soft-delete; raises 404 otherwise."""
    stmt = (
        select(TestCase, Session)
        .join(Session, TestCase.session_id == Session.id)
        .where(
            TestCase.id == case_id,
            Session.deleted_at.is_(None),
        )
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    case, session = row[0], row[1]
    if user.role != "admin" and session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    return case, session


async def get_attachment_or_404(
    db: AsyncSession,
    attachment_id: uuid.UUID,
    user: User,
) -> Tuple[Attachment, TestCase, Session]:
    """Fetch attachment, case, and session verifying ownership and soft-delete; raises 404 otherwise."""
    stmt = (
        select(Attachment, TestCase, Session)
        .join(TestCase, Attachment.test_case_id == TestCase.id)
        .join(Session, TestCase.session_id == Session.id)
        .where(
            Attachment.id == attachment_id,
            Session.deleted_at.is_(None),
        )
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    attachment, case, session = row[0], row[1], row[2]
    if user.role != "admin" and session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    return attachment, case, session


# ---------------------------------------------------------------------------
# Figure Number Recomputation
# ---------------------------------------------------------------------------
async def recompute_session_figure_numbers(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> None:
    """Recomputes figure_no sequentially (1, 2, ...) ordered by case position then attachment created_at."""
    stmt = (
        select(Attachment)
        .join(TestCase, Attachment.test_case_id == TestCase.id)
        .where(TestCase.session_id == session_id)
        .order_by(
            TestCase.position.asc(),
            Attachment.created_at.asc(),
            Attachment.id.asc(),
        )
    )
    res = await db.execute(stmt)
    attachments = res.scalars().all()
    for idx, att in enumerate(attachments, start=1):
        if att.figure_no != idx:
            att.figure_no = idx


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------
async def create_session(
    db: AsyncSession,
    user: User,
    data: SessionCreate,
) -> Session:
    """Create a new session in draft status."""
    session = Session(
        user_id=user.id,
        ticket_no=data.ticket_no.strip(),
        ticket_title=data.ticket_title.strip(),
        environment=data.environment.value if data.environment else None,
        test_date=data.test_date,
        testing_types=data.testing_types,
        tc_prefix=data.tc_prefix or "TC",
        tc_counter=0,
        status="draft",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session_detail(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
) -> Tuple[Session, SessionCounts]:
    """Get session detail with eager loaded ordered cases, steps, attachments, and execution counts."""
    # Verify access first
    await get_session_or_404(db, session_id, user)

    # Use selectinload to prevent N+1 queries
    stmt = (
        select(Session)
        .options(
            selectinload(Session.test_cases).selectinload(TestCase.test_steps),
            selectinload(Session.test_cases).selectinload(TestCase.attachments),
        )
        .where(
            Session.id == session_id,
            Session.deleted_at.is_(None),
        )
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Order cases by position, steps by step_no, attachments by figure_no
    session.test_cases.sort(key=lambda c: c.position)
    for c in session.test_cases:
        c.test_steps.sort(key=lambda s: s.step_no)
        c.attachments.sort(key=lambda a: a.figure_no)

    # Compute execution counts
    counts_map = {
        "pass": 0,
        "fail": 0,
        "blocked": 0,
        "skipped": 0,
        "not_run": 0,
    }
    for c in session.test_cases:
        st = c.status if c.status in counts_map else "not_run"
        counts_map[st] += 1

    counts = SessionCounts(
        pass_count=counts_map["pass"],
        fail=counts_map["fail"],
        blocked=counts_map["blocked"],
        skipped=counts_map["skipped"],
        not_run=counts_map["not_run"],
        total=len(session.test_cases),
    )

    return session, counts


async def update_session_header(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
    data: SessionUpdate,
) -> Session:
    """Update session header fields."""
    session = await get_session_or_404(db, session_id, user)

    if data.ticket_no is not None:
        session.ticket_no = data.ticket_no.strip()
    if data.ticket_title is not None:
        session.ticket_title = data.ticket_title.strip()
    if data.environment is not None:
        session.environment = data.environment.value
    if data.test_date is not None:
        session.test_date = data.test_date
    if data.testing_types is not None:
        session.testing_types = data.testing_types
    if data.tc_prefix is not None:
        session.tc_prefix = data.tc_prefix

    await db.commit()
    await db.refresh(session)
    return session


async def complete_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
) -> SessionCounts:
    """Mark session as completed and return execution counts."""
    session = await get_session_or_404(db, session_id, user)
    session.status = "completed"
    await db.commit()

    # Calculate counts
    count_stmt = select(TestCase.status, func.count(TestCase.id)).where(
        TestCase.session_id == session_id
    ).group_by(TestCase.status)
    res = await db.execute(count_stmt)
    status_counts = dict(res.all())

    return SessionCounts(
        pass_count=status_counts.get("pass", 0),
        fail=status_counts.get("fail", 0),
        blocked=status_counts.get("blocked", 0),
        skipped=status_counts.get("skipped", 0),
        not_run=status_counts.get("not_run", 0),
        total=sum(status_counts.values()),
    )


# ---------------------------------------------------------------------------
# Test Case Operations
# ---------------------------------------------------------------------------
async def create_test_case(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
    data: TestCaseCreate,
) -> TestCase:
    """Create a case atomically incrementing sessions.tc_counter and assigning position."""
    session = await get_session_or_404(db, session_id, user)

    # 1. Enforce max 500 cases per session
    count_stmt = select(func.count(TestCase.id)).where(TestCase.session_id == session_id)
    curr_count = (await db.execute(count_stmt)).scalar() or 0
    if curr_count >= 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Session has reached the maximum limit of 500 test cases.",
        )

    # 2. Atomic TC counter increment in the same transaction using RETURNING
    update_stmt = (
        update(Session)
        .where(Session.id == session_id)
        .values(tc_counter=Session.tc_counter + 1)
        .returning(Session.tc_counter, Session.tc_prefix)
    )
    res = await db.execute(update_stmt)
    counter_row = res.fetchone()
    if not counter_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    next_counter, prefix = counter_row[0], counter_row[1]
    tc_id = f"{prefix}-{next_counter:02d}"

    # 3. Position at the end
    max_pos_stmt = select(func.max(TestCase.position)).where(TestCase.session_id == session_id)
    max_pos = (await db.execute(max_pos_stmt)).scalar()
    position = 0 if max_pos is None else max_pos + 1

    # Status & executed_at
    case_status = data.status.value if data.status else "not_run"
    executed_at = datetime.now(timezone.utc) if case_status != "not_run" else None

    # Update session status if first non-not_run case is created
    if case_status != "not_run":
        if session.status == "draft":
            session.status = "in_progress"
        elif session.status == "completed":
            session.status = "in_progress"

    test_case = TestCase(
        session_id=session_id,
        tc_id=tc_id,
        position=position,
        scenario=data.scenario,
        precondition=data.precondition,
        test_data=data.test_data,
        expected_result=data.expected_result,
        actual_result=data.actual_result,
        status=case_status,
        executed_at=executed_at,
    )
    db.add(test_case)
    await db.flush()

    # Steps
    if data.steps:
        for idx, s in enumerate(data.steps, start=1):
            step = TestStep(
                test_case_id=test_case.id,
                step_no=idx,
                description=s.description,
            )
            db.add(step)

    await db.commit()

    # Reload with relationships
    return await get_loaded_test_case(db, test_case.id)


async def get_loaded_test_case(db: AsyncSession, case_id: uuid.UUID) -> TestCase:
    """Fetch test case with steps and attachments eager loaded."""
    stmt = (
        select(TestCase)
        .options(
            selectinload(TestCase.test_steps),
            selectinload(TestCase.attachments),
        )
        .where(TestCase.id == case_id)
    )
    res = await db.execute(stmt)
    case = res.scalar_one()
    case.test_steps.sort(key=lambda s: s.step_no)
    case.attachments.sort(key=lambda a: a.figure_no)
    return case


async def update_test_case(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User,
    data: TestCaseUpdate,
) -> TestCase:
    """Partial update of a test case, including whole step list replacement and status transition logic."""
    case, session = await get_case_or_404(db, case_id, user)

    status_changed = False
    actual_result_changed = False

    # Check fields provided
    fields_set = data.model_fields_set

    if "scenario" in fields_set:
        case.scenario = data.scenario
    if "precondition" in fields_set:
        case.precondition = data.precondition
    if "test_data" in fields_set:
        case.test_data = data.test_data
    if "expected_result" in fields_set:
        case.expected_result = data.expected_result
    if "actual_result" in fields_set:
        if case.actual_result != data.actual_result:
            actual_result_changed = True
        case.actual_result = data.actual_result

    if "status" in fields_set and data.status is not None:
        new_status = data.status.value
        if case.status != new_status:
            status_changed = True
            case.status = new_status
            if new_status != "not_run":
                case.executed_at = datetime.now(timezone.utc)
            else:
                case.executed_at = None

    # Handle session status transitions:
    # 1. draft becomes in_progress if any case is not not_run
    if session.status == "draft" and case.status != "not_run":
        session.status = "in_progress"
    # 2. completed reverts to in_progress if status OR actual_result changes
    elif session.status == "completed" and (status_changed or actual_result_changed):
        session.status = "in_progress"

    # Replace whole steps list if "steps" was provided
    if "steps" in fields_set and data.steps is not None:
        # Delete existing steps
        existing_steps_stmt = select(TestStep).where(TestStep.test_case_id == case.id)
        existing_steps = (await db.execute(existing_steps_stmt)).scalars().all()
        for es in existing_steps:
            await db.delete(es)
        await db.flush()

        # Add new ordered steps
        for idx, s in enumerate(data.steps, start=1):
            step = TestStep(
                test_case_id=case.id,
                step_no=idx,
                description=s.description,
            )
            db.add(step)

    await db.commit()
    return await get_loaded_test_case(db, case.id)


async def delete_test_case(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User,
) -> None:
    """Hard delete case, steps, attachments, then delete files from disk (best effort)."""
    case, session = await get_case_or_404(db, case_id, user)

    # 1. Collect all attachment disk file paths before DB deletion
    att_stmt = select(Attachment).where(Attachment.test_case_id == case.id)
    attachments = (await db.execute(att_stmt)).scalars().all()
    file_paths_to_delete = [att.file_path for att in attachments]

    # 2. Delete test case (cascades to test_steps and attachments)
    await db.delete(case)
    await db.flush()

    # 3. Recompute figure numbers for remaining session attachments
    await recompute_session_figure_numbers(db, session.id)

    # 4. Commit database transaction FIRST
    await db.commit()

    # 5. Delete files from disk (best effort, log failure, never fail request)
    for fp in file_paths_to_delete:
        try:
            full_path = settings.upload_dir_path / fp
            if full_path.exists():
                full_path.unlink()
        except Exception as e:
            logger.warning("Failed to delete attachment file %s: %s", fp, e)


async def reorder_test_cases(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
    data: CaseReorderRequest,
) -> List[TestCase]:
    """Reorder test cases in a session according to ordered_case_ids."""
    session = await get_session_or_404(db, session_id, user)

    # Fetch all existing cases for this session
    stmt = select(TestCase).where(TestCase.session_id == session.id)
    cases = (await db.execute(stmt)).scalars().all()
    case_map = {c.id: c for c in cases}

    # Must match the session's active case ids exactly (same set and length)
    if set(data.ordered_case_ids) != set(case_map.keys()) or len(data.ordered_case_ids) != len(case_map):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ordered_case_ids must match the session's active test case IDs exactly.",
        )

    # Update positions (0, 1, 2, ...)
    for pos, cid in enumerate(data.ordered_case_ids):
        case_map[cid].position = pos

    await db.flush()

    # Recompute figure numbers for the session
    await recompute_session_figure_numbers(db, session.id)
    await db.commit()

    # Return reordered cases with relationships loaded
    stmt_ordered = (
        select(TestCase)
        .options(
            selectinload(TestCase.test_steps),
            selectinload(TestCase.attachments),
        )
        .where(TestCase.session_id == session.id)
        .order_by(TestCase.position.asc())
    )
    res_ordered = await db.execute(stmt_ordered)
    ordered = res_ordered.scalars().all()
    for c in ordered:
        c.test_steps.sort(key=lambda s: s.step_no)
        c.attachments.sort(key=lambda a: a.figure_no)
    return list(ordered)


# ---------------------------------------------------------------------------
# Attachment Operations
# ---------------------------------------------------------------------------
def _validate_and_save_image_sync(
    file_bytes: bytes,
    dest_path: Path,
) -> Tuple[str, str]:
    """Synchronous CPU/disk bound image validation and saving to run in threadpool."""
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    # 1. Verify integrity
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
            detected_format = img.format
    except Image.DecompressionBombError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image pixel dimensions exceed allowed limit.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupted or invalid image file.",
        )

    if not detected_format:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format.",
        )

    fmt_upper = detected_format.upper()
    if fmt_upper not in IMAGE_FORMAT_MAP:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {fmt_upper}. Allowed types: PNG, JPEG, WEBP, GIF",
        )

    ext, content_type = IMAGE_FORMAT_MAP[fmt_upper]

    # 2. Re-open image after verify() to ensure it can be fully read
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.load()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupted or unreadable image data.",
        )

    # 3. Write file to destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    return ext, content_type


async def add_attachment(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User,
    file: UploadFile,
    caption: Optional[str] = None,
) -> Attachment:
    """Upload and process an attachment, validating via Pillow in a threadpool."""
    case, session = await get_case_or_404(db, case_id, user)

    # 1. Read in chunks to enforce size limit before in-memory buffering
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    chunk_size = 64 * 1024
    buffer = io.BytesIO()
    total_bytes = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB.",
            )
        buffer.write(chunk)

    file_bytes = buffer.getvalue()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty file uploaded.",
        )

    # 2. Generate random filename and destination path
    file_id = uuid.uuid4()
    # Temporary placeholder destination until format is verified
    temp_filename = f"{file_id}.tmp"
    rel_dir = Path(str(session.id)) / str(case.id)
    upload_root = settings.upload_dir_path.resolve()
    target_dir = (upload_root / rel_dir).resolve()

    # Guard against path traversal
    if not str(target_dir).startswith(str(upload_root)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path.",
        )

    # 3. Validate image and save file via threadpool
    # Determine ext and content_type first using thread
    dest_file_stub = target_dir / temp_filename
    ext, content_type = await asyncio.to_thread(_validate_and_save_image_sync, file_bytes, dest_file_stub)

    # Rename to final filename with detected extension
    final_filename = f"{file_id}.{ext}"
    final_path = target_dir / final_filename
    dest_file_stub.rename(final_path)

    # Relative path stored in database
    rel_file_path = str(rel_dir / final_filename)

    # 4. Create Attachment record
    attachment = Attachment(
        test_case_id=case.id,
        file_path=rel_file_path,
        caption=caption.strip() if caption else None,
        figure_no=1,  # will be recomputed
    )
    db.add(attachment)
    await db.flush()

    # 5. Recompute figure numbers for the whole session
    await recompute_session_figure_numbers(db, session.id)

    # 6. Commit database transaction
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def update_attachment_caption(
    db: AsyncSession,
    attachment_id: uuid.UUID,
    user: User,
    caption: Optional[str],
) -> Attachment:
    """Update an attachment's caption."""
    attachment, _, _ = await get_attachment_or_404(db, attachment_id, user)
    attachment.caption = caption.strip() if caption else None
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def delete_attachment(
    db: AsyncSession,
    attachment_id: uuid.UUID,
    user: User,
) -> None:
    """Delete an attachment from database and disk (best effort)."""
    attachment, _, session = await get_attachment_or_404(db, attachment_id, user)
    file_path_to_delete = attachment.file_path

    # Delete from DB
    await db.delete(attachment)
    await db.flush()

    # Recompute figure numbers for the session
    await recompute_session_figure_numbers(db, session.id)

    # Commit DB FIRST
    await db.commit()

    # Delete disk file (best effort)
    try:
        full_path = settings.upload_dir_path / file_path_to_delete
        if full_path.exists():
            full_path.unlink()
    except Exception as e:
        logger.warning("Failed to delete attachment file %s: %s", file_path_to_delete, e)


async def get_attachment_file_path(
    db: AsyncSession,
    attachment_id: uuid.UUID,
    user: User,
) -> Tuple[Path, str]:
    """Retrieve validated file path on disk and content-type for an attachment."""
    attachment, _, _ = await get_attachment_or_404(db, attachment_id, user)

    full_path = (settings.upload_dir_path / attachment.file_path).resolve()
    upload_root = settings.upload_dir_path.resolve()

    # Path traversal protection
    if not str(full_path).startswith(str(upload_root)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    # Determine Content-Type based on extension
    ext = full_path.suffix.lstrip(".").lower()
    ext_to_content_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    media_type = ext_to_content_type.get(ext, "application/octet-stream")

    return full_path, media_type
