from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from bot.states.settings_states import ReferralSettingsStates
from db.models.settings import REFERRAL_BONUS, REFERRAL_PROMO_TEXT
from repositories import settings_repo
from utils.formatting import format_money

router = Router(name="admin_referral_settings")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

EDIT_BONUS_CB = "rs_edit:bonus"
EDIT_TEXT_CB = "rs_edit:text"


def _settings_kb():
    return admin_kb.with_back_row(
        [
            [InlineKeyboardButton(text="🎁 Bonus miqdorini o'zgartirish", callback_data=EDIT_BONUS_CB)],
            [InlineKeyboardButton(text="✏️ Matnni o'zgartirish", callback_data=EDIT_TEXT_CB)],
        ]
    )


async def _render(session: AsyncSession) -> str:
    values = await settings_repo.get_all(session)
    bonus = values.get(REFERRAL_BONUS, "0")
    text = values.get(REFERRAL_PROMO_TEXT, "—")
    return f"🔗 Referal sozlamalari:\n\n🎁 Bonus: {format_money(bonus)}\n✏️ Matn: {text}"


@router.callback_query(AdminMenuCB.filter(F.section == "referral"))
async def show_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.message.edit_text(await _render(session), reply_markup=_settings_kb())


@router.callback_query(F.data == EDIT_BONUS_CB)
async def edit_bonus_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReferralSettingsStates.waiting_bonus)
    await callback.message.edit_text(
        "Yangi referal bonus miqdorini so'mda kiriting:", reply_markup=admin_kb.cancel_kb()
    )


@router.message(ReferralSettingsStates.waiting_bonus, F.text)
async def edit_bonus_apply(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("❗ Musbat son kiriting:", reply_markup=admin_kb.cancel_kb())
        return
    await settings_repo.set_value(session, REFERRAL_BONUS, message.text.strip())
    await state.clear()
    await message.answer(await _render(session), reply_markup=_settings_kb())


@router.callback_query(F.data == EDIT_TEXT_CB)
async def edit_text_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReferralSettingsStates.waiting_promo_text)
    await callback.message.edit_text(
        "Yangi referal matnini kiriting:", reply_markup=admin_kb.cancel_kb()
    )


@router.message(ReferralSettingsStates.waiting_promo_text, F.text)
async def edit_text_apply(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await settings_repo.set_value(session, REFERRAL_PROMO_TEXT, message.text.strip())
    await state.clear()
    await message.answer(await _render(session), reply_markup=_settings_kb())
