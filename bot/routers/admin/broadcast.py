from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from bot.states.broadcast_states import BroadcastStates
from services import broadcast_service

router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

SEND_CB = "bc_send"
CANCEL_CB = "bc_cancel"


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data=SEND_CB),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CANCEL_CB),
            ]
        ]
    )


@router.callback_query(AdminMenuCB.filter(F.section == "broadcast"))
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_content)
    await callback.message.edit_text(
        "📢 Xabar matnini yuboring (rasm bilan birga yuborishingiz ham mumkin, "
        "rasm ostiga matn yozing):",
        reply_markup=admin_kb.cancel_kb(),
    )


@router.message(BroadcastStates.waiting_content, F.photo)
async def content_with_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.caption or "", photo_file_id=message.photo[-1].file_id)
    await state.set_state(BroadcastStates.confirm_preview)
    await message.answer("Quyidagi xabar yuboriladi:")
    await message.answer_photo(
        message.photo[-1].file_id, caption=message.caption or "", reply_markup=_confirm_kb()
    )


@router.message(BroadcastStates.waiting_content, F.text)
async def content_text_only(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text, photo_file_id=None)
    await state.set_state(BroadcastStates.confirm_preview)
    await message.answer("Quyidagi xabar yuboriladi:")
    await message.answer(message.text, reply_markup=_confirm_kb())


@router.callback_query(BroadcastStates.confirm_preview, F.data == CANCEL_CB)
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(admin_kb.PANEL_TITLE, reply_markup=admin_kb.admin_root_kb())


@router.callback_query(BroadcastStates.confirm_preview, F.data == SEND_CB)
async def send_broadcast(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    await callback.message.answer("Yuborilmoqda...")
    broadcast = await broadcast_service.send_broadcast(
        session, bot, data["text"], data.get("photo_file_id")
    )
    await state.clear()
    await callback.message.answer(
        f"✅ Yuborildi: {broadcast.sent_count}\n❌ Xato: {broadcast.failed_count}",
        reply_markup=admin_kb.with_back_row([]),
    )
