from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(default=None)
    full_name: Mapped[str | None] = mapped_column(default=None)
    phone_number: Mapped[str | None] = mapped_column(default=None)

    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_withdrawn: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    votes_confirmed_count: Mapped[int] = mapped_column(default=0)

    referred_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), default=None
    )
    referral_code: Mapped[str] = mapped_column(unique=True)

    is_blocked: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
