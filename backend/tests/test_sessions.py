import asyncio
import io
import os
import tempfile
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.session import Session
from app.models.test_case import TestCase
from app.models.user import User
from app.services import session_service

# Avoid pytest warning treating TestCase model as a test class
TestCase.__test__ = False

AUTH_PREFIX = "/api/v1/auth"
SESSIONS_PREFIX = "/api/v1/sessions"
CASES_PREFIX = "/api/v1/cases"
ATTACHMENTS_PREFIX = "/api/v1/attachments"


def create_test_image(format="PNG", size=(100, 100), color=(0, 194, 203)) -> bytes:
    """Generate in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


async def register_and_login(client: AsyncClient, name="QA Tester", email="qa@testora.local", role="user") -> dict:
    """Register or log in user and return headers with auth cookies."""
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": email, "password": "Password123!"},
    )
    if login_res.status_code != 200:
        reg_res = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"name": name, "email": email, "password": "Password123!"},
        )
        assert reg_res.status_code == 201
        login_res = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_res.status_code == 200

    return login_res.json()["user"]


# ---------------------------------------------------------------------------
# 1. Session Creation & Prefix Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_session_defaults_and_custom_prefix(client: AsyncClient):
    """Session creation supports default and custom prefixes (auto-uppercased), starting in draft."""
    user = await register_and_login(client, email="s_creator@testora.local")

    # 1. Default prefix
    payload1 = {
        "ticket_no": "TCK-101",
        "ticket_title": "Login authentication flow",
        "environment": "QA",
        "testing_types": ["Functional", "Security"],
    }
    res1 = await client.post(SESSIONS_PREFIX, json=payload1)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["ticket_no"] == "TCK-101"
    assert data1["tc_prefix"] == "TC"
    assert data1["tc_counter"] == 0
    assert data1["status"] == "draft"
    assert data1["environment"] == "QA"

    # 2. Custom prefix (lowercase converted to uppercase)
    payload2 = {
        "ticket_no": "TCK-102",
        "ticket_title": "OTP Flow",
        "environment": "Dev",
        "tc_prefix": "tc-otp",
    }
    res2 = await client.post(SESSIONS_PREFIX, json=payload2)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["tc_prefix"] == "TC-OTP"


# ---------------------------------------------------------------------------
# 2. Sequential TC IDs, Non-Reuse after Delete & Prefix Change
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tc_ids_sequential_not_reused_and_prefix_change(client: AsyncClient):
    """Verify sequential TC IDs, non-reuse after case deletion, and prefix update affecting only new cases."""
    await register_and_login(client, email="tc_seq@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "SEQ-1", "ticket_title": "Sequential Test", "tc_prefix": "TC"},
    )
    session_id = s_res.json()["id"]

    # Append Case 1 -> TC-01
    c1_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "First case"})
    assert c1_res.status_code == 201
    c1 = c1_res.json()
    assert c1["tc_id"] == "TC-01"
    assert c1["position"] == 0

    # Append Case 2 -> TC-02
    c2_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Second case"})
    assert c2_res.status_code == 201
    c2 = c2_res.json()
    assert c2["tc_id"] == "TC-02"
    assert c2["position"] == 1

    # Delete Case 1
    del_res = await client.delete(f"{CASES_PREFIX}/{c1['id']}")
    assert del_res.status_code == 200

    # Append Case 3 -> Must be TC-03 (TC-01 is NEVER reused)
    c3_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Third case"})
    assert c3_res.status_code == 201
    c3 = c3_res.json()
    assert c3["tc_id"] == "TC-03"

    # Change prefix to "TC-AUTH"
    up_res = await client.put(f"{SESSIONS_PREFIX}/{session_id}", json={"tc_prefix": "TC-AUTH"})
    assert up_res.status_code == 200
    assert up_res.json()["tc_prefix"] == "TC-AUTH"

    # Append Case 4 -> Must use new prefix with next counter f"TC-AUTH-04"
    c4_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Fourth case"})
    assert c4_res.status_code == 201
    c4 = c4_res.json()
    assert c4["tc_id"] == "TC-AUTH-04"


# ---------------------------------------------------------------------------
# 3. Concurrent Case Creation on File-Based SQLite
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_case_creation_no_duplicates_file_sqlite():
    """Verify concurrent case creation produces no duplicate TC IDs on a file-based SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        user_id = uuid.uuid4()
        session_id = uuid.uuid4()

        async with session_maker() as session:
            user = User(
                id=user_id,
                name="Concurrent Tester",
                email="concur@testora.local",
                password_hash="fakehash",
                role="user",
            )
            sess = Session(
                id=session_id,
                user_id=user_id,
                ticket_no="CONCUR-1",
                ticket_title="Concurrency Test",
                tc_prefix="TC",
                tc_counter=0,
                status="draft",
            )
            session.add_all([user, sess])
            await session.commit()

        # Concurrently create 15 cases using separate DB connections
        num_cases = 15

        async def worker(idx: int):
            async with session_maker() as s:
                u = await s.get(User, user_id)
                data = session_service.TestCaseCreate(scenario=f"Concurrent scenario {idx}")
                return await session_service.create_test_case(s, session_id, u, data)

        created_cases = await asyncio.gather(*(worker(i) for i in range(num_cases)))

        tc_ids = [c.tc_id for c in created_cases]
        assert len(tc_ids) == num_cases
        # Zero duplicates
        assert len(set(tc_ids)) == num_cases

        # Confirm all sequential: TC-01 to TC-15
        expected_ids = {f"TC-{i:02d}" for i in range(1, num_cases + 1)}
        assert set(tc_ids) == expected_ids

        await engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ---------------------------------------------------------------------------
# 4. Maximum 500 Cases Limit
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_enforce_max_500_cases_limit(client: AsyncClient, db_session: AsyncSession):
    """Enforce maximum 500 cases per session with 422 error."""
    await register_and_login(client, email="limit500@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "LIM-500", "ticket_title": "500 Case Limit Test"},
    )
    session_id = uuid.UUID(s_res.json()["id"])

    # Directly insert 500 cases into the database
    bulk_cases = [
        TestCase(
            session_id=session_id,
            tc_id=f"TC-{i:03d}",
            position=i - 1,
            scenario=f"Scenario {i}",
            status="not_run",
        )
        for i in range(1, 501)
    ]
    db_session.add_all(bulk_cases)
    await db_session.commit()

    # Attempting to add the 501st case via API must fail with 422
    res = await client.post(
        f"{SESSIONS_PREFIX}/{session_id}/cases",
        json={"scenario": "501st case"},
    )
    assert res.status_code == 422
    assert "maximum limit of 500" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Case Update & Steps Replacement
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_update_and_steps_replacement(client: AsyncClient):
    """Updating a case with 'steps' replaces the entire ordered steps list."""
    await register_and_login(client, email="steps_user@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "STP-1", "ticket_title": "Steps Test"},
    )
    session_id = s_res.json()["id"]

    # Create case with 3 initial steps
    c_res = await client.post(
        f"{SESSIONS_PREFIX}/{session_id}/cases",
        json={
            "scenario": "Login test",
            "steps": [
                {"description": "Open login page"},
                {"description": "Enter email and password"},
                {"description": "Click submit"},
            ],
        },
    )
    assert c_res.status_code == 201
    case_id = c_res.json()["id"]
    assert len(c_res.json()["steps"]) == 3
    assert c_res.json()["steps"][0]["step_no"] == 1

    # Replace with 2 new steps
    up_res = await client.put(
        f"{CASES_PREFIX}/{case_id}",
        json={
            "scenario": "Updated login test",
            "steps": [
                {"description": "Navigate to SSO portal"},
                {"description": "Authorize via OAuth"},
            ],
        },
    )
    assert up_res.status_code == 200
    updated = up_res.json()
    assert updated["scenario"] == "Updated login test"
    assert len(updated["steps"]) == 2
    assert updated["steps"][0]["description"] == "Navigate to SSO portal"
    assert updated["steps"][0]["step_no"] == 1
    assert updated["steps"][1]["description"] == "Authorize via OAuth"
    assert updated["steps"][1]["step_no"] == 2


# ---------------------------------------------------------------------------
# 6. Status and Executed_at Behavior
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_status_and_executed_at_behavior(client: AsyncClient):
    """Moving status away from not_run sets executed_at; moving back clears it."""
    await register_and_login(client, email="exec_time@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "EXC-1", "ticket_title": "Execution Timestamp"},
    )
    session_id = s_res.json()["id"]

    c_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Status test"})
    case_id = c_res.json()["id"]
    assert c_res.json()["status"] == "not_run"
    assert c_res.json()["executed_at"] is None

    # Move to pass -> sets executed_at
    pass_res = await client.put(f"{CASES_PREFIX}/{case_id}", json={"status": "pass"})
    assert pass_res.status_code == 200
    assert pass_res.json()["status"] == "pass"
    assert pass_res.json()["executed_at"] is not None

    # Move back to not_run -> clears executed_at
    reset_res = await client.put(f"{CASES_PREFIX}/{case_id}", json={"status": "not_run"})
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "not_run"
    assert reset_res.json()["executed_at"] is None


# ---------------------------------------------------------------------------
# 7. Session Status Transitions
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_session_status_transitions(client: AsyncClient):
    """Session transitions: draft -> in_progress -> completed -> in_progress on case update."""
    await register_and_login(client, email="transitions@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "TRS-1", "ticket_title": "Transitions Test"},
    )
    session_id = s_res.json()["id"]
    assert s_res.json()["status"] == "draft"

    # Add a case in not_run -> session remains draft
    c_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Case 1"})
    case_id = c_res.json()["id"]
    detail_res1 = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert detail_res1.json()["status"] == "draft"

    # Update case to 'fail' -> session becomes in_progress
    await client.put(f"{CASES_PREFIX}/{case_id}", json={"status": "fail"})
    detail_res2 = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert detail_res2.json()["status"] == "in_progress"

    # Complete session -> completed
    comp_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/complete")
    assert comp_res.status_code == 200
    detail_res3 = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert detail_res3.json()["status"] == "completed"

    # Updating case actual_result in completed session reverts it to in_progress
    await client.put(f"{CASES_PREFIX}/{case_id}", json={"actual_result": "Fixed in patch"})
    detail_res4 = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert detail_res4.json()["status"] == "in_progress"


# ---------------------------------------------------------------------------
# 8. Case Reordering
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_reorder_valid_and_invalid(client: AsyncClient):
    """Reorder updates positions; invalid or mismatched IDs return 422."""
    await register_and_login(client, email="reorder@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "REO-1", "ticket_title": "Reorder Test"},
    )
    session_id = s_res.json()["id"]

    c1 = (await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "A"})).json()
    c2 = (await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "B"})).json()
    c3 = (await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "C"})).json()

    # 1. Valid reorder: C, A, B
    reorder_res = await client.put(
        f"{SESSIONS_PREFIX}/{session_id}/cases/reorder",
        json={"ordered_case_ids": [c3["id"], c1["id"], c2["id"]]},
    )
    assert reorder_res.status_code == 200
    reordered = reorder_res.json()
    assert reordered[0]["id"] == c3["id"]
    assert reordered[0]["position"] == 0
    assert reordered[1]["id"] == c1["id"]
    assert reordered[1]["position"] == 1
    assert reordered[2]["id"] == c2["id"]
    assert reordered[2]["position"] == 2

    # 2. Missing ID in reorder -> 422
    bad_res1 = await client.put(
        f"{SESSIONS_PREFIX}/{session_id}/cases/reorder",
        json={"ordered_case_ids": [c3["id"], c1["id"]]},
    )
    assert bad_res1.status_code == 422

    # 3. Foreign ID -> 422
    bad_res2 = await client.put(
        f"{SESSIONS_PREFIX}/{session_id}/cases/reorder",
        json={"ordered_case_ids": [c3["id"], c1["id"], c2["id"], str(uuid.uuid4())]},
    )
    assert bad_res2.status_code == 422


# ---------------------------------------------------------------------------
# 9. Attachment Upload Validation & Secure Download
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_attachment_upload_validations_and_file_download(client: AsyncClient):
    """Test image upload validation (valid, wrong type, oversized, corrupt) and download headers."""
    await register_and_login(client, email="attach@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "ATT-1", "ticket_title": "Attachment Test"},
    )
    session_id = s_res.json()["id"]
    c_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Evidence"})
    case_id = c_res.json()["id"]

    # 1. Valid PNG upload
    valid_png = create_test_image("PNG")
    res_upload = await client.post(
        f"{CASES_PREFIX}/{case_id}/attachments",
        files={"file": ("screenshot.png", valid_png, "image/png")},
        data={"caption": "Login screen"},
    )
    assert res_upload.status_code == 201
    attachment = res_upload.json()
    att_id = attachment["id"]
    assert attachment["caption"] == "Login screen"
    assert attachment["figure_no"] == 1
    assert attachment["file_path"].endswith(".png")

    # 2. Download file with correct headers
    dl_res = await client.get(f"{ATTACHMENTS_PREFIX}/{att_id}/file")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "image/png"
    assert dl_res.headers["x-content-type-options"] == "nosniff"
    assert dl_res.headers["cache-control"] == "private"
    assert dl_res.content == valid_png

    # 3. Wrong type (text file) -> 415
    txt_file = b"This is plain text"
    res_wrong = await client.post(
        f"{CASES_PREFIX}/{case_id}/attachments",
        files={"file": ("log.txt", txt_file, "text/plain")},
    )
    assert res_wrong.status_code in (415, 422)

    # 4. Corrupt image file disguised as .png -> 422
    corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_DATA"
    res_corrupt = await client.post(
        f"{CASES_PREFIX}/{case_id}/attachments",
        files={"file": ("fake.png", corrupt_bytes, "image/png")},
    )
    assert res_corrupt.status_code == 422

    # 5. Oversized image (> 5 MB) -> 413
    big_bytes = b"X" * (settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1024)
    res_big = await client.post(
        f"{CASES_PREFIX}/{case_id}/attachments",
        files={"file": ("huge.png", big_bytes, "image/png")},
    )
    assert res_big.status_code == 413


# ---------------------------------------------------------------------------
# 10. Figure Number Recomputation & Disk File Cleanup
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_figure_no_recomputation_and_disk_file_cleanup(client: AsyncClient):
    """Figure numbers recompute sequentially across session cases; deleted attachments are removed from disk."""
    await register_and_login(client, email="fig_cleanup@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "FIG-1", "ticket_title": "Figure Test"},
    )
    session_id = s_res.json()["id"]

    c1 = (await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Case A"})).json()
    c2 = (await client.post(f"{SESSIONS_PREFIX}/{session_id}/cases", json={"scenario": "Case B"})).json()

    img1 = create_test_image("PNG", size=(50, 50))
    img2 = create_test_image("JPEG", size=(50, 50))

    # Add attachment to Case 1 -> Figure 1
    att1 = (
        await client.post(
            f"{CASES_PREFIX}/{c1['id']}/attachments",
            files={"file": ("a.png", img1, "image/png")},
        )
    ).json()
    assert att1["figure_no"] == 1

    # Add attachment to Case 2 -> Figure 2
    att2 = (
        await client.post(
            f"{CASES_PREFIX}/{c2['id']}/attachments",
            files={"file": ("b.jpg", img2, "image/jpeg")},
        )
    ).json()
    assert att2["figure_no"] == 2

    # Reorder cases: Case 2 first, then Case 1
    await client.put(
        f"{SESSIONS_PREFIX}/{session_id}/cases/reorder",
        json={"ordered_case_ids": [c2["id"], c1["id"]]},
    )

    # In detail view, attachment on Case 2 is now Figure 1, Case 1 is Figure 2
    detail = (await client.get(f"{SESSIONS_PREFIX}/{session_id}")).json()
    cases_dict = {c["id"]: c for c in detail["cases"]}
    assert cases_dict[c2["id"]]["attachments"][0]["figure_no"] == 1
    assert cases_dict[c1["id"]]["attachments"][0]["figure_no"] == 2

    # Check file exists on disk
    file_on_disk = settings.upload_dir_path / att1["file_path"]
    assert file_on_disk.exists()

    # Delete attachment 1 -> file removed from disk
    del_res = await client.delete(f"{ATTACHMENTS_PREFIX}/{att1['id']}")
    assert del_res.status_code == 200
    assert not file_on_disk.exists()

    # Remaining attachment on Case 2 recomputes to Figure 1
    detail_after = (await client.get(f"{SESSIONS_PREFIX}/{session_id}")).json()
    assert detail_after["cases"][0]["attachments"][0]["figure_no"] == 1


# ---------------------------------------------------------------------------
# 11. Ownership Rules & Soft-Delete Returns 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ownership_isolation_and_soft_delete(client: AsyncClient, db_session: AsyncSession):
    """Non-owner receives 404; admin can access; soft-deleted session returns 404."""
    # 1. First registered user in clean test DB becomes Admin
    admin_user = await register_and_login(client, name="Super Admin", email="super_admin@testora.local")
    assert admin_user["role"] == "admin"

    # 2. Admin registers Owner user
    reg_owner = await client.post(
        f"{AUTH_PREFIX}/register",
        json={"name": "Owner User", "email": "owner@testora.local", "password": "Password123!"},
    )
    assert reg_owner.status_code == 201

    # 3. Admin registers Other user
    reg_other = await client.post(
        f"{AUTH_PREFIX}/register",
        json={"name": "Other User", "email": "other@testora.local", "password": "Password123!"},
    )
    assert reg_other.status_code == 201

    # 4. Log in as Owner and create session
    await client.post(f"{AUTH_PREFIX}/login", json={"email": "owner@testora.local", "password": "Password123!"})
    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "OWN-1", "ticket_title": "Ownership Test"},
    )
    assert s_res.status_code == 201
    session_id = s_res.json()["id"]

    # 5. Log in as Other User -> GET session must return 404 (NOT 403)
    await client.post(f"{AUTH_PREFIX}/login", json={"email": "other@testora.local", "password": "Password123!"})
    other_res = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert other_res.status_code == 404

    # 6. Log in as Admin -> GET session must succeed (200)
    await client.post(f"{AUTH_PREFIX}/login", json={"email": "super_admin@testora.local", "password": "Password123!"})
    admin_res = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert admin_res.status_code == 200

    # 7. Soft delete session
    session_obj = await db_session.get(Session, uuid.UUID(session_id))
    session_obj.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    # 8. Log in as Owner -> GET soft-deleted session returns 404
    await client.post(f"{AUTH_PREFIX}/login", json={"email": "owner@testora.local", "password": "Password123!"})
    soft_res = await client.get(f"{SESSIONS_PREFIX}/{session_id}")
    assert soft_res.status_code == 404


# ---------------------------------------------------------------------------
# 12. Complete Session Returns Correct Counts
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_complete_session_returns_correct_counts(client: AsyncClient):
    """POST /sessions/{id}/complete returns accurate status counts."""
    await register_and_login(client, email="counts_user@testora.local")

    s_res = await client.post(
        SESSIONS_PREFIX,
        json={"ticket_no": "CNT-1", "ticket_title": "Counts Test"},
    )
    session_id = s_res.json()["id"]

    # Add cases with various statuses: 2 pass, 1 fail, 1 blocked, 1 skipped, 1 not_run
    statuses = ["pass", "pass", "fail", "blocked", "skipped", "not_run"]
    for idx, st in enumerate(statuses):
        await client.post(
            f"{SESSIONS_PREFIX}/{session_id}/cases",
            json={"scenario": f"Case {idx}", "status": st},
        )

    comp_res = await client.post(f"{SESSIONS_PREFIX}/{session_id}/complete")
    assert comp_res.status_code == 200
    counts = comp_res.json()
    assert counts["pass"] == 2
    assert counts["fail"] == 1
    assert counts["blocked"] == 1
    assert counts["skipped"] == 1
    assert counts["not_run"] == 1
    assert counts["total"] == 6
