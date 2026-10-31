import os
import tempfile
import uuid
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import BACKEND_DIR


def test_alembic_migrations_apply_cleanly_on_fresh_database():
    """Verify that alembic upgrade head runs without error on a brand new database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        fresh_db_path = tmp_file.name

    try:
        # Prepare alembic configuration pointing to the fresh SQLite database
        alembic_ini_path = str(BACKEND_DIR / "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            f"sqlite+aiosqlite:///{fresh_db_path}",
        )

        # Run migration
        command.upgrade(alembic_cfg, "head")

        # Verify tables created using synchronous sqlite engine
        sync_engine = create_engine(f"sqlite:///{fresh_db_path}")
        inspector = inspect(sync_engine)
        table_names = inspector.get_table_names()

        expected_tables = {
            "users",
            "sessions",
            "test_cases",
            "test_steps",
            "attachments",
            "export_logs",
            "user_settings",
            "alembic_version",
        }
        for table in expected_tables:
            assert table in table_names, f"Expected table '{table}' not found in migrated database"

        # Check columns on sessions table
        session_cols = {col["name"]: col for col in inspector.get_columns("sessions")}
        assert "tc_prefix" in session_cols
        assert "tc_counter" in session_cols

        # Check constraints on test_cases
        unique_constraints = inspector.get_unique_constraints("test_cases")
        uc_col_sets = [set(uc["column_names"]) for uc in unique_constraints]
        assert {"session_id", "tc_id"} in uc_col_sets

        sync_engine.dispose()
    finally:
        if os.path.exists(fresh_db_path):
            os.remove(fresh_db_path)


def test_alembic_upgrade_with_existing_session_rows_sets_server_defaults():
    """Verify that upgrading from previous revision b5819fcb4ae3 with an existing session row sets defaults."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        fresh_db_path = tmp_file.name

    try:
        alembic_ini_path = str(BACKEND_DIR / "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            f"sqlite+aiosqlite:///{fresh_db_path}",
        )

        # 1. Upgrade to previous revision only
        command.upgrade(alembic_cfg, "b5819fcb4ae3")

        sync_engine = create_engine(f"sqlite:///{fresh_db_path}")
        with sync_engine.begin() as conn:
            user_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            conn.execute(
                text(
                    "INSERT INTO users (id, name, email, password_hash, role) "
                    "VALUES (:id, 'Test User', 'mig@example.com', 'hash', 'user')"
                ),
                {"id": user_id},
            )
            conn.execute(
                text(
                    "INSERT INTO sessions (id, user_id, ticket_no, ticket_title, testing_types, status) "
                    "VALUES (:id, :user_id, 'TICK-101', 'Migration Session', '[]', 'draft')"
                ),
                {"id": session_id, "user_id": user_id},
            )

        # 2. Upgrade to head (applies c743810ef12a)
        command.upgrade(alembic_cfg, "head")

        # 3. Verify existing session row acquired tc_prefix='TC' and tc_counter=0
        with sync_engine.connect() as conn:
            row = conn.execute(
                text("SELECT tc_prefix, tc_counter FROM sessions WHERE id = :id"),
                {"id": session_id},
            ).fetchone()
            assert row is not None
            assert row[0] == "TC"
            assert row[1] == 0

        sync_engine.dispose()
    finally:
        if os.path.exists(fresh_db_path):
            os.remove(fresh_db_path)
