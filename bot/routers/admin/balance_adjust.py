from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from bot.states.balance_states import BalanceAdjustStates
from repositories import user_repo
from services import balance_service
from utils.formatting import format_money
from utils.phone import normalize_uz_phone

router = Router(name="admin_balance_adjust")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

SKIP_REASON = "o'tkazib yuborish"
CONFIRM_CB = "bal_confirm"
CANCEL_CB = "bal_cancel"


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=CONFIRM_CB),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CANCEL_CB),
            ]
        ]
    )


@router.callback_query(AdminMenuCB.filter(F.section == "balance"))
async def start_lookup(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BalanceAdjustStates.waiting_user_lookup)
    await callback.message.edit_text(
        "💳 Foydalanuvchi Telegram ID yoki telefon raqamini kiriting:",
        reply_markup=admin_kb.cancel_kb(),
    )


@router.message(BalanceAdjustStates.waiting_user_lookup, F.text)
async def lookup_received(message: Message, session: AsyncSession, state: FSMContext) -> None:
    raw = message.text.strip()
    user = None
    if raw.isdigit():
        user = await user_repo.get_by_telegram_id(session, int(raw))
    if user is None:
        phone = normalize_uz_phone(raw)
        if phone:
            user = await user_repo.get_by_phone(session, phone)

    if user is None:
        await message.answer("❗ Foydalanuvchi topilmadi. Qayta kiriting:", reply_markup=admin_kb.cancel_kb())
        return

    await state.update_data(user_id=user.telegram_id)
    await state.set_state(BalanceAdjustStates.waiting_amount)
    await message.answer(
        f"Foydalanuvchi: {user.full_name or '—'} (ID: {user.telegram_id})\n"
        f"Joriy balans: {format_money(user.balance)}\n\n"
        "Necha so'm? (+ qo'shish, - ayirish, masalan: +50000 yoki -20000)",
        reply_markup=admin_kb.cancel_kb(),
    )


@router.message(BalanceAdjustStates.waiting_amount, F.text)
async def amount_received(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(" ", "")
    if not raw or raw[0] not in "+-" or not raw[1:].isdigit():
        await message.answer("❗ Format: +50000 yoki -20000. Qayta kiriting:", reply_markup=admin_kb.cancel_kb())
        return

    await state.update_data(amount=raw)
    await state.set_state(BalanceAdjustStates.waiting_reason)
    await message.answer(
        f"Sabab kiriting (yoki '{SKIP_REASON}' deb yozing):", reply_markup=admin_kb.cancel_kb()
    )


@router.message(BalanceAdjustStates.waiting_reason, F.text)
async def reason_received(message: Message, session: AsyncSession, state: FSMContext) -> None:
    reason = message.text.strip()
    await state.update_data(reason=reason)

    data = await state.get_data()
    user = await user_repo.get_by_telegram_id(session, data["user_id"])
    amount = Decimal(data["amount"])

    await message.answer(
        "🧾 So'rovni tekshiring:\n\n"
        f"Foydalanuvchi: {user.full_name or '—'} (ID: {user.telegram_id})\n"
        f"O'zgarish: {'+' if amount >= 0 else ''}{format_money(amount)}\n"
        f"Yangi balans: {format_money(user.balance + amount)}\n"
        f"Sabab: {reason}",
        reply_markup=_confirm_kb(),
    )


@router.callback_query(BalanceAdjustStates.waiting_reason, F.data == CANCEL_CB)
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(admin_kb.PANEL_TITLE, reply_markup=admin_kb.admin_root_kb())


@router.callback_query(BalanceAdjustStates.waiting_reason, F.data == CONFIRM_CB)
async def confirm(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    user = await user_repo.get_by_telegram_id(session, data["user_id"])
    if user is None:
        await state.clear()
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    amount = Decimal(data["amount"])
    reason = data["reason"]
    if reason.lower() == SKIP_REASON:
        reason = "Admin tomonidan qo'lda o'zgartirish"

    await balance_service.adjust(session, user, amount, reason=reason, created_by_admin=True)
    await state.clear()

    await callback.message.edit_text(
        f"✅ Balans yangilandi. Yangi balans: {format_money(user.balance)}",
        reply_markup=admin_kb.with_back_row([]),
    )
