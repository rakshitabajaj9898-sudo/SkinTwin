from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class ConsentAuditLog(Base):
    __tablename__ = "consent_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    consent_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("consent_records.id", ondelete="SET NULL"),
        nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    new_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    collection_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )