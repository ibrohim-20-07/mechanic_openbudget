from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import MyVotesCB
from bot.keyboards.user_kb import MY_VOTES_BUTTON
from db.models.user import User
from db.models.vote import VoteStatus
from repositories import vote_repo
from utils.pagination import PAGE_SIZE, page_footer
from utils.timezone import format_local

router = Router(name="user_my_votes")

STATUS_MAP: dict[str, VoteStatus | None] = {
    "all": None,
    "confirmed": VoteStatus.CONFIRMED,
    "pending": VoteStatus.PENDING,
    "rejected": VoteStatus.REJECTED,
}
STATUS_LABEL = {
    "all": "Barchasi",
    "confirmed": "Tasdiqlangan",
    "pending": "Kutilayotgan",
    "rejected": "Bekor qilingan",
}
STATUS_ICON = {
    VoteStatus.CONFIRMED: "✅",
    VoteStatus.PENDING: "♻️",
    VoteStatus.REJECTED: "❌",
}


async def _render(
    session: AsyncSession, user_id: int, status_key: str, offset: int
) -> tuple[str, InlineKeyboardMarkup]:
    status_enum = STATUS_MAP[status_key]
    votes = await vote_repo.list_by_user_paginated(session, user_id, status_enum, offset, PAGE_SIZE)
    total = await vote_repo.count_by_user(session, user_id, status_enum)

    lines = [
        f"🔍 {STATUS_LABEL[status_key]}\n",
        "✅ - Tasdiqlangan | ♻️ - Kutilayotgan | ❌ - Bekor qilingan",
        "―" * 20,
    ]
    if not votes:
        lines.append("Bo'sh.")
    for v in votes:
        icon = STATUS_ICON[v.status]
        lines.append(f"{icon} | {format_local(v.created_at)} | {v.phone_number}")
    lines.append(f"\n{page_footer(offset, PAGE_SIZE, total)}")

    def cb(status: str, off: int) -> str:
        return MyVotesCB(status=status, offset=off).pack()

    rows = [
        [
            InlineKeyboardButton(text="🔍 Barchasi", callback_data=cb("all", 0)),
            InlineKeyboardButton(text="✅ Tasdiqlangan", callback_data=cb("confirmed", 0)),
        ],
        [
            InlineKeyboardButton(text="♻️ Kutilayotgan", callback_data=cb("pending", 0)),
            InlineKeyboardButton(text="❌ Bekor", callback_data=cb("rejected", 0)),
        ],
    ]
    pagination_row = []
    if offset > 0:
        pagination_row.append(
            InlineKeyboardButton(text="◀️ Oldingi", callback_data=cb(status_key, max(0, offset - PAGE_SIZE)))
        )
    if offset + PAGE_SIZE < total:
        pagination_row.append(
            InlineKeyboardButton(text="Oldinga ⏩", callback_data=cb(status_key, offset + PAGE_SIZE))
        )
    if pagination_row:
        rows.append(pagination_row)

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == MY_VOTES_BUTTON)
async def open_my_votes(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await state.clear()
    text, kb = await _render(session, db_user.telegram_id, "all", 0)
    await message.answer(text, reply_markup=kb)


@router.callback_query(MyVotesCB.filter())
async def paginate_my_votes(
    callback: CallbackQuery, callback_data: MyVotesCB, session: AsyncSession, db_user: User
) -> None:
    text, kb = await _render(session, db_user.telegram_id, callback_data.status, callback_data.offset)
    await callback.message.edit_text(text, reply_markup=kb)
