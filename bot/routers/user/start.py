from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import user_kb
from db.models.user import User
from repositories import referral_repo, user_repo

router = Router(name="user_start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    await _maybe_attach_referral(session, db_user, command.args)

    # Admin sees the same plain user experience here — the admin panel only
    # opens explicitly via the /admin command, never automatically on /start.
    await message.answer(
        "🎯 OpenBudget botiga xush kelibsiz.\n\nQuyidagi tugmalardan birini tanlang.",
        reply_markup=user_kb.main_menu(),
    )


async def _maybe_attach_referral(session: AsyncSession, db_user: User, payload: str | None) -> None:
    if db_user.referred_by is not None or not payload or not payload.isdigit():
        return

    referrer_id = int(payload)
    if referrer_id == db_user.telegram_id:
        return

    referrer = await user_repo.get_by_telegram_id(session, referrer_id)
    if referrer is None:
        return

    existing = await referral_repo.get_by_referred_id(session, db_user.telegram_id)
    if existing is not None:
        return

    db_user.referred_by = referrer_id
    await referral_repo.create_referral(session, referrer_id=referrer_id, referred_id=db_user.telegram_id)
