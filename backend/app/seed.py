import asyncio
import logging
from typing import Optional

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.user import User
from app.services import user_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def seed_admin() -> Optional[User]:
    """Create default admin user if one does not already exist."""
    admin_email = settings.FIRST_SUPERUSER_EMAIL
    admin_password = settings.FIRST_SUPERUSER_PASSWORD
    admin_name = settings.FIRST_SUPERUSER_NAME

    logger.info("Checking for default admin account: %s", admin_email)

    async with AsyncSessionLocal() as db:
        existing = await user_service.get_user_by_email(db, admin_email)
        if existing:
            logger.info("Admin account '%s' already exists (ID: %s). Skipping creation.", admin_email, existing.id)
            return existing

        admin = await user_service.create_user(
            db=db,
            name=admin_name,
            email=admin_email,
            password=admin_password,
            role="admin",
        )
        logger.info("Default admin '%s' created successfully with ID: %s", admin_email, admin.id)
        return admin


def main():
    asyncio.run(seed_admin())


if __name__ == "__main__":
    main()
