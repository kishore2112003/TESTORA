import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user_setting import UserSetting
from app.services import user_service

AUTH_PREFIX = f"{settings.API_V1_STR}/auth"


@pytest.mark.asyncio
async def test_root_and_health(client: AsyncClient):
    """Test public health and welcome endpoints at root without version prefix."""
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["app"] == settings.APP_NAME

    # /health stays at root (no prefix) for Docker health checks
    res_health = await client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_unprefixed_auth_routes_not_mounted(client: AsyncClient):
    """Confirm the duplicate unprefixed /auth routes were removed and return 404."""
    res = await client.post("/auth/login", json={"email": "test@testora.local", "password": "pass"})
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_first_user_registration_becomes_admin(client: AsyncClient):
    """The very first registered user in an empty database becomes admin automatically."""
    payload = {
        "name": "First Admin",
        "email": "first_admin@testora.local",
        "password": "SecurePassword123!",
        "role": "user",  # Even if requested as 'user', first user becomes 'admin'
    }
    response = await client.post(f"{AUTH_PREFIX}/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "first_admin@testora.local"
    assert data["name"] == "First Admin"
    assert data["role"] == "admin"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_subsequent_registration_requires_admin(client: AsyncClient):
    """Once a user exists, unauthenticated or non-admin registrations are rejected."""
    # 1. Register first user (Admin)
    admin_data = {
        "name": "Primary Admin",
        "email": "admin@example.com",
        "password": "Admin@123",
    }
    res = await client.post(f"{AUTH_PREFIX}/register", json=admin_data)
    assert res.status_code == 201
    assert res.json()["role"] == "admin"

    # 2. Try registering a second user unauthenticated -> should fail 401
    user_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "Password123!",
    }
    res_unauth = await client.post(f"{AUTH_PREFIX}/register", json=user_data)
    assert res_unauth.status_code == 401

    # 3. Log in as admin
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": admin_data["email"], "password": admin_data["password"]},
    )
    assert login_res.status_code == 200
    client.cookies.update(login_res.cookies)

    # Register Jane Doe while authenticated as admin
    res_admin_register = await client.post(
        f"{AUTH_PREFIX}/register",
        json=user_data,
    )
    assert res_admin_register.status_code == 201
    assert res_admin_register.json()["email"] == "jane@example.com"
    assert res_admin_register.json()["role"] == "user"

    # Clear admin cookies
    client.cookies.clear()

    # 4. Log in as Jane Doe (non-admin)
    jane_login = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert jane_login.status_code == 200
    client.cookies.update(jane_login.cookies)

    # Jane attempts to register a 3rd user -> should fail 403 Forbidden
    res_forbidden = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "name": "Bob Smith",
            "email": "bob@example.com",
            "password": "Password123!",
        },
    )
    assert res_forbidden.status_code == 403
    assert "admin privileges" in res_forbidden.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_email_registration_fails(client: AsyncClient):
    """Attempting to register with an existing email returns 400 Bad Request."""
    user_data = {
        "name": "User One",
        "email": "duplicate@testora.local",
        "password": "Password123!",
    }
    res1 = await client.post(f"{AUTH_PREFIX}/register", json=user_data)
    assert res1.status_code == 201

    # Attempt to register again with same email
    res2 = await client.post(f"{AUTH_PREFIX}/register", json=user_data)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_flow_and_cookie_generation(client: AsyncClient):
    """Successful login sets httpOnly cookie and returns user profile."""
    credentials = {
        "name": "Auth Tester",
        "email": "authtester@testora.local",
        "password": "SuperSecretPassword123!",
    }
    await client.post(f"{AUTH_PREFIX}/register", json=credentials)

    # Valid login
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == credentials["email"]
    assert settings.COOKIE_NAME in login_res.cookies

    # Invalid password
    bad_pass_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": credentials["email"], "password": "WrongPassword"},
    )
    assert bad_pass_res.status_code == 401
    assert "incorrect email or password" in bad_pass_res.json()["detail"].lower()

    # Non-existent user
    non_existent_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": "nobody@testora.local", "password": "Password123!"},
    )
    assert non_existent_res.status_code == 401


@pytest.mark.asyncio
async def test_protected_me_endpoint_requires_cookie(client: AsyncClient):
    """GET /api/v1/auth/me returns 401 without cookie, 200 with valid cookie."""
    # Attempt without any cookie -> 401
    unauth_res = await client.get(f"{AUTH_PREFIX}/me")
    assert unauth_res.status_code == 401
    assert "not authenticated" in unauth_res.json()["detail"].lower()

    # Register and login
    user_data = {
        "name": "Cookie Tester",
        "email": "cookietester@testora.local",
        "password": "Password123!",
    }
    await client.post(f"{AUTH_PREFIX}/register", json=user_data)
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_res.status_code == 200
    client.cookies.update(login_res.cookies)

    # Query /me with session cookie
    me_res = await client.get(f"{AUTH_PREFIX}/me")
    assert me_res.status_code == 200
    user_profile = me_res.json()
    assert user_profile["email"] == user_data["email"]
    assert user_profile["name"] == user_data["name"]
    assert "id" in user_profile


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient):
    """POST /api/v1/auth/logout clears the session cookie and prevents subsequent authenticated calls."""
    user_data = {
        "name": "Logout Tester",
        "email": "logout@testora.local",
        "password": "Password123!",
    }
    await client.post(f"{AUTH_PREFIX}/register", json=user_data)
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_res.status_code == 200
    client.cookies.update(login_res.cookies)

    # Verify session is working
    res_before = await client.get(f"{AUTH_PREFIX}/me")
    assert res_before.status_code == 200

    # Call logout
    logout_res = await client.post(f"{AUTH_PREFIX}/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"

    # In HTTP, delete_cookie sets cookie to empty or expires in the past
    cookie_value = logout_res.cookies.get(settings.COOKIE_NAME, "")
    assert cookie_value == ""

    # Clear client cookies to simulate browser honoring Set-Cookie removal
    client.cookies.clear()

    # Attempting to call /auth/me without valid cookie returns 401
    res_after = await client.get(f"{AUTH_PREFIX}/me")
    assert res_after.status_code == 401


@pytest.mark.asyncio
async def test_user_settings_created_for_every_user(client: AsyncClient, db_session: AsyncSession):
    """Confirm user_service.create_user automatically creates a user_settings row for each user."""
    # Test via create_user directly
    created = await user_service.create_user(
        db=db_session,
        name="Settings Test User",
        email="settings_user@testora.local",
        password="Password123!",
        role="user",
    )
    assert created.id is not None

    # Check user_settings row in database
    result = await db_session.execute(select(UserSetting).where(UserSetting.user_id == created.id))
    setting = result.scalar_one_or_none()
    assert setting is not None
    assert setting.user_id == created.id
    assert setting.default_environment == "development"


@pytest.mark.asyncio
async def test_change_password_unauthenticated_fails(client: AsyncClient):
    """Calling /change-password unauthenticated returns 401."""
    res = await client.post(
        f"{AUTH_PREFIX}/change-password",
        json={"current_password": "OldPassword123!", "new_password": "NewPassword123!"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_change_password_validation_and_flow(client: AsyncClient):
    """Verify change-password flow: success, wrong current, weak new, same password, and subsequent logins."""
    user_data = {
        "name": "Password Changer",
        "email": "pw_changer@testora.local",
        "password": "InitialPassword123!",
    }
    await client.post(f"{AUTH_PREFIX}/register", json=user_data)

    # 1. Log in
    login_res = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_res.status_code == 200
    client.cookies.update(login_res.cookies)

    # 2. Reject short new password (< 8 chars) -> 422
    short_res = await client.post(
        f"{AUTH_PREFIX}/change-password",
        json={"current_password": "InitialPassword123!", "new_password": "short"},
    )
    assert short_res.status_code == 422

    # 3. Reject wrong current password -> 400
    wrong_curr_res = await client.post(
        f"{AUTH_PREFIX}/change-password",
        json={"current_password": "WrongPassword123!", "new_password": "BrandNewPassword123!"},
    )
    assert wrong_curr_res.status_code == 400
    assert "incorrect current password" in wrong_curr_res.json()["detail"].lower()

    # 4. Reject new password equal to current password -> 400
    same_res = await client.post(
        f"{AUTH_PREFIX}/change-password",
        json={"current_password": "InitialPassword123!", "new_password": "InitialPassword123!"},
    )
    assert same_res.status_code == 400
    assert "cannot be the same" in same_res.json()["detail"].lower()

    # 5. Successful change -> 200
    new_pw = "BrandNewPassword123!"
    success_res = await client.post(
        f"{AUTH_PREFIX}/change-password",
        json={"current_password": "InitialPassword123!", "new_password": new_pw},
    )
    assert success_res.status_code == 200
    assert "password changed successfully" in success_res.json()["message"].lower()

    # 6. Clear session and verify old password fails, new password succeeds
    client.cookies.clear()

    old_login = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": "InitialPassword123!"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": user_data["email"], "password": new_pw},
    )
    assert new_login.status_code == 200
    assert new_login.json()["user"]["email"] == user_data["email"]
