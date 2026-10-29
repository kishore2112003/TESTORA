import os
import tempfile
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

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

        sync_engine.dispose()
    finally:
        if os.path.exists(fresh_db_path):
            os.remove(fresh_db_path)
