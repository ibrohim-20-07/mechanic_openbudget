import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class VoteStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        Index("ix_votes_user_status", "user_id", "status"),
        Index("ix_votes_project_id", "project_id"),
        Index("ix_votes_created_at", "created_at"),
        # a phone number can have at most one active (pending/confirmed) vote at a time —
        # backstops the application-level check in vote_repo.get_active_by_phone against races
        Index(
            "one_active_vote_per_phone",
            "phone_number",
            unique=True,
            postgresql_where=text("status IN ('PENDING'::vote_status, 'CONFIRMED'::vote_status)"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    phone_number: Mapped[str]
    screenshot_file_ids: Mapped[list[str]] = mapped_column(ARRAY(String))

    status: Mapped[VoteStatus] = mapped_column(
        Enum(VoteStatus, name="vote_status"), default=VoteStatus.PENDING, index=True
    )

    admin_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    admin_channel_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)

    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reward_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
