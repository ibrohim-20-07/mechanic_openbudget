from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.get(User, telegram_id)


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
    referred_by: int | None = None,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        referral_code=str(telegram_id),
        referred_by=referred_by,
    )
    session.add(user)
    await session.flush()
    return user


async def get_by_phone(session: AsyncSession, phone_number: str) -> User | None:
    result = await session.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


async def list_not_blocked(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.is_blocked.is_(False)))
    return list(result.scalars().all())
