from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.models.withdrawal import PaymentSystem, Withdrawal, WithdrawalStatus
from repositories import user_repo
from services import balance_service


class InsufficientBalance(Exception):
    pass


async def create_withdrawal(
    session: AsyncSession,
    user: User,
    payment_system: PaymentSystem,
    card_number: str,
    amount: Decimal,
) -> Withdrawal:
    if amount > user.balance:
        raise InsufficientBalance()

    withdrawal = Withdrawal(
        user_id=user.telegram_id,
        payment_system=payment_system,
        card_number=card_number,
        amount=amount,
    )
    session.add(withdrawal)
    await session.flush()

    await balance_service.adjust(
        session,
        user,
        -amount,
        reason=f"withdrawal_pending:{withdrawal.id}",
        related_withdrawal_id=withdrawal.id,
    )
    return withdrawal


async def mark_paid(session: AsyncSession, withdrawal: Withdrawal) -> User | None:
    withdrawal.status = WithdrawalStatus.PAID
    withdrawal.paid_at = datetime.now(timezone.utc)

    user = await user_repo.get_by_telegram_id(session, withdrawal.user_id)
    if user is not None:
        user.total_withdrawn = user.total_withdrawn + withdrawal.amount
    await session.flush()
    return user
