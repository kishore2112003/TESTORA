import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from sqlalchemy import Date, DateTime, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.test_case import TestCase


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_no: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ticket_title: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    testing_types: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TestCase.position",
    )

    def __repr__(self) -> str:
        return f"<Session id={self.id} ticket_no={self.ticket_no} status={self.status}>"
