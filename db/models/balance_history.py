from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class BalanceHistory(Base):
    __tablename__ = "balance_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # signed: + credit, - debit
    reason: Mapped[str]

    related_vote_id: Mapped[int | None] = mapped_column(ForeignKey("votes.id"), default=None)
    related_withdrawal_id: Mapped[int | None] = mapped_column(
        ForeignKey("withdrawals.id"), default=None
    )

    created_by_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
