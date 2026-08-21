from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.referral import Referral


async def create_referral(session: AsyncSession, referrer_id: int, referred_id: int) -> Referral:
    referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
    session.add(referral)
    await session.flush()
    return referral


async def get_by_referred_id(session: AsyncSession, referred_id: int) -> Referral | None:
    result = await session.execute(select(Referral).where(Referral.referred_id == referred_id))
    return result.scalar_one_or_none()
