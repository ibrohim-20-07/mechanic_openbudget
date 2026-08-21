from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_kb import REFERRAL_BUTTON
from db.models.referral import Referral
from db.models.settings import REFERRAL_PROMO_TEXT
from db.models.user import User
from repositories import settings_repo
from utils.formatting import format_money

router = Router(name="user_referral")


@router.message(F.text == REFERRAL_BUTTON)
async def show_referral(
    message: Message, session: AsyncSession, db_user: User, bot_username: str, state: FSMContext
) -> None:
    await state.clear()
    link = f"https://t.me/{bot_username}?start={db_user.referral_code}"
    promo_text = await settings_repo.get(session, REFERRAL_PROMO_TEXT) or ""

    total_stmt = select(func.count()).select_from(Referral).where(
        Referral.referrer_id == db_user.telegram_id
    )
    credited_stmt = select(func.coalesce(func.sum(Referral.bonus_amount), 0)).where(
        Referral.referrer_id == db_user.telegram_id, Referral.credited_at.is_not(None)
    )
    total_referred = (await session.execute(total_stmt)).scalar() or 0
    total_earned = (await session.execute(credited_stmt)).scalar() or 0

    await message.answer(
        f"{promo_text}\n\n"
        f"🔗 Sizning havolangiz:\n{link}\n\n"
        f"👥 Taklif qilinganlar: {total_referred}\n"
        f"💰 Referaldan topilgan: {format_money(total_earned)}"
    )
