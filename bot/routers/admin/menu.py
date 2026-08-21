from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.callbacks import AdminCancelCB, AdminMenuCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb

router = Router(name="admin_menu")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def open_admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(admin_kb.PANEL_TITLE, reply_markup=admin_kb.admin_root_kb())


@router.callback_query(AdminMenuCB.filter(F.section == "root"))
async def show_root(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(admin_kb.PANEL_TITLE, reply_markup=admin_kb.admin_root_kb())


@router.callback_query(AdminCancelCB.filter())
async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(admin_kb.PANEL_TITLE, reply_markup=admin_kb.admin_root_kb())
