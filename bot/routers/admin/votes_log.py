from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB, PageCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from db.models.vote import VoteStatus
from repositories import user_repo, vote_repo
from utils.pagination import PAGE_SIZE, build_pagination_row, page_footer
from utils.timezone import format_local

router = Router(name="admin_votes_log")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

STATUS_ICON = {
    VoteStatus.CONFIRMED: "✅",
    VoteStatus.PENDING: "♻️",
    VoteStatus.REJECTED: "❌",
}


async def _render_page(session: AsyncSession, offset: int) -> tuple[str, InlineKeyboardMarkup]:
    votes = await vote_repo.list_paginated(session, offset, PAGE_SIZE)
    total = await vote_repo.count_all(session)

    if not votes:
        return "🗳 Ovozlar yo'q.", admin_kb.with_back_row([])

    lines = ["🗳 Ovozlar ro'yxati:\n"]
    for v in votes:
        user = await user_repo.get_by_telegram_id(session, v.user_id)
        who = f"@{user.username}" if user and user.username else str(v.user_id)
        icon = STATUS_ICON[v.status]
        lines.append(f"{icon} | {format_local(v.created_at)} | {v.phone_number} | {who}")

    lines.append(f"\n{page_footer(offset, PAGE_SIZE, total)}")
    row = build_pagination_row("votes", offset, PAGE_SIZE, total)
    kb = admin_kb.with_back_row([row] if row else [])
    return "\n".join(lines), kb


@router.callback_query(AdminMenuCB.filter(F.section == "votes"))
async def show_votes(callback: CallbackQuery, session: AsyncSession) -> None:
    text, kb = await _render_page(session, offset=0)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(PageCB.filter(F.scope == "votes"))
async def paginate_votes(
    callback: CallbackQuery, callback_data: PageCB, session: AsyncSession
) -> None:
    text, kb = await _render_page(session, offset=callback_data.offset)
    await callback.message.edit_text(text, reply_markup=kb)
