import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class PaymentSystem(str, enum.Enum):
    HUMO = "humo"
    UZCARD = "uzcard"
    CLICK = "click"
    PAYME = "payme"
    PAYNET = "paynet"


class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)

    payment_system: Mapped[PaymentSystem] = mapped_column(
        Enum(PaymentSystem, name="payment_system")
    )
    card_number: Mapped[str]
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    status: Mapped[WithdrawalStatus] = mapped_column(
        Enum(WithdrawalStatus, name="withdrawal_status"),
        default=WithdrawalStatus.PENDING,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    admin_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    admin_channel_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
