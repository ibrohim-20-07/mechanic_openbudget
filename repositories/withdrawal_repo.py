from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.withdrawal import Withdrawal, WithdrawalStatus


async def get_by_id(session: AsyncSession, withdrawal_id: int) -> Withdrawal | None:
    return await session.get(Withdrawal, withdrawal_id)


async def set_admin_message(
    session: AsyncSession, withdrawal: Withdrawal, message_id: int, chat_id: int
) -> None:
    withdrawal.admin_message_id = message_id
    withdrawal.admin_channel_chat_id = chat_id
    await session.flush()


async def list_pending_paginated(
    session: AsyncSession, offset: int, limit: int
) -> list[Withdrawal]:
    stmt = (
        select(Withdrawal)
        .where(Withdrawal.status == WithdrawalStatus.PENDING)
        .order_by(Withdrawal.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_pending(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Withdrawal).where(
        Withdrawal.status == WithdrawalStatus.PENDING
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def list_by_user_paginated(
    session: AsyncSession, user_id: int, offset: int, limit: int
) -> list[Withdrawal]:
    stmt = (
        select(Withdrawal)
        .where(Withdrawal.user_id == user_id)
        .order_by(Withdrawal.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_by_user(session: AsyncSession, user_id: int) -> int:
    stmt = select(func.count()).select_from(Withdrawal).where(Withdrawal.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar() or 0
