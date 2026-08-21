from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.balance_history import BalanceHistory
from db.models.user import User


async def adjust(
    session: AsyncSession,
    user: User,
    amount: Decimal,
    reason: str,
    related_vote_id: int | None = None,
    related_withdrawal_id: int | None = None,
    created_by_admin: bool = False,
) -> BalanceHistory:
    user.balance = user.balance + amount
    entry = BalanceHistory(
        user_id=user.telegram_id,
        amount=amount,
        reason=reason,
        related_vote_id=related_vote_id,
        related_withdrawal_id=related_withdrawal_id,
        created_by_admin=created_by_admin,
    )
    session.add(entry)
    await session.flush()
    return entry
