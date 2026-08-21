from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB, PageCB, WithdrawalActionCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from config import settings
from repositories import user_repo, withdrawal_repo
from services import withdrawal_service
from utils.formatting import format_money, mask_card
from utils.pagination import PAGE_SIZE, build_pagination_row, page_footer
from utils.timezone import format_local

router = Router(name="admin_withdrawals")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _render_page(session: AsyncSession, offset: int) -> tuple[str, InlineKeyboardMarkup]:
    items = await withdrawal_repo.list_pending_paginated(session, offset, PAGE_SIZE)
    total = await withdrawal_repo.count_pending(session)

    if not items:
        return "🧾 Kutilayotgan zayafkalar yo'q.", admin_kb.with_back_row([])

    lines = ["🧾 Kutilayotgan zayafkalar:\n"]
    rows = []
    for w in items:
        user = await user_repo.get_by_telegram_id(session, w.user_id)
        who = f"@{user.username}" if user and user.username else str(w.user_id)
        lines.append(
            f"#{w.id} | {format_local(w.created_at)} | {who}\n"
            f"{w.payment_system.value.upper()} {mask_card(w.card_number)} — {format_money(w.amount)}"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ #{w.id} to'landi deb belgilash",
                    callback_data=WithdrawalActionCB(withdrawal_id=w.id, action="mark_paid").pack(),
                )
            ]
        )

    pagination_row = build_pagination_row("withdrawals", offset, PAGE_SIZE, total)
    if pagination_row:
        rows.append(pagination_row)

    lines.append(f"\n{page_footer(offset, PAGE_SIZE, total)}")
    return "\n\n".join(lines), admin_kb.with_back_row(rows)


@router.callback_query(AdminMenuCB.filter(F.section == "withdrawals"))
async def show_withdrawals(callback: CallbackQuery, session: AsyncSession) -> None:
    text, kb = await _render_page(session, offset=0)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(PageCB.filter(F.scope == "withdrawals"))
async def paginate_withdrawals(
    callback: CallbackQuery, callback_data: PageCB, session: AsyncSession
) -> None:
    text, kb = await _render_page(session, offset=callback_data.offset)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(WithdrawalActionCB.filter(F.action == "mark_paid"))
async def mark_paid(
    callback: CallbackQuery,
    callback_data: WithdrawalActionCB,
    session: AsyncSession,
    bot: Bot,
) -> None:
    withdrawal = await withdrawal_repo.get_by_id(session, callback_data.withdrawal_id)
    if withdrawal is None:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    if withdrawal.status.value == "paid":
        await callback.answer("Bu so'rov allaqachon to'langan.", show_alert=True)
        return

    user = await withdrawal_service.mark_paid(session, withdrawal)

    if callback.message.chat.id == settings.payments_channel_id:
        paid_at_str = format_local(withdrawal.paid_at)
        new_text = f"{callback.message.text or ''}\n\n✅ To'landi — {paid_at_str}"
        await callback.message.edit_text(new_text, reply_markup=None)
    else:
        text, kb = await _render_page(session, offset=0)
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("To'landi deb belgilandi.")

    if user is not None:
        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ {format_money(withdrawal.amount)} miqdoridagi pul yechish so'rovingiz to'landi.",
            )
        except TelegramForbiddenError:
            user.is_blocked = True
