from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import MyWithdrawalsCB
from bot.routers.user.account import ACCOUNT_BACK_CB, MY_WITHDRAWALS_OPEN_CB
from db.models.user import User
from db.models.withdrawal import WithdrawalStatus
from repositories import withdrawal_repo
from utils.formatting import format_money, mask_card
from utils.pagination import PAGE_SIZE, page_footer
from utils.timezone import format_local

router = Router(name="user_my_withdrawals")

STATUS_ICON = {
    WithdrawalStatus.PENDING: "♻️",
    WithdrawalStatus.PAID: "✅",
}


async def _render(session: AsyncSession, user_id: int, offset: int) -> tuple[str, InlineKeyboardMarkup]:
    items = await withdrawal_repo.list_by_user_paginated(session, user_id, offset, PAGE_SIZE)
    total = await withdrawal_repo.count_by_user(session, user_id)

    lines = ["📋 To'lovlar tarixi\n", "✅ - To'landi | ♻️ - Kutilmoqda", "―" * 20]
    if not items:
        lines.append("Bo'sh.")
    for w in items:
        icon = STATUS_ICON[w.status]
        lines.append(
            f"{icon} | {format_local(w.created_at)} | {w.payment_system.value.upper()} "
            f"{mask_card(w.card_number)} — {format_money(w.amount)}"
        )
    lines.append(f"\n{page_footer(offset, PAGE_SIZE, total)}")

    pagination_row = []
    if offset > 0:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️ Oldingi", callback_data=MyWithdrawalsCB(offset=max(0, offset - PAGE_SIZE)).pack()
            )
        )
    if offset + PAGE_SIZE < total:
        pagination_row.append(
            InlineKeyboardButton(
                text="Oldinga ⏩", callback_data=MyWithdrawalsCB(offset=offset + PAGE_SIZE).pack()
            )
        )
    rows = [pagination_row] if pagination_row else []
    rows.append([InlineKeyboardButton(text="« Hisobim", callback_data=ACCOUNT_BACK_CB)])

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == MY_WITHDRAWALS_OPEN_CB)
async def open_my_withdrawals(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    text, kb = await _render(session, db_user.telegram_id, 0)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(MyWithdrawalsCB.filter())
async def paginate_my_withdrawals(
    callback: CallbackQuery, callback_data: MyWithdrawalsCB, session: AsyncSession, db_user: User
) -> None:
    text, kb = await _render(session, db_user.telegram_id, callback_data.offset)
    await callback.message.edit_text(text, reply_markup=kb)
