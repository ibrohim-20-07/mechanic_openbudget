from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks import PageCB

PAGE_SIZE = 10


def build_pagination_row(
    scope: str, offset: int, limit: int, total: int
) -> list[InlineKeyboardButton]:
    row = []
    if offset > 0:
        row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=PageCB(scope=scope, offset=max(0, offset - limit)).pack(),
            )
        )
    if offset + limit < total:
        row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=PageCB(scope=scope, offset=offset + limit).pack(),
            )
        )
    return row


def page_footer(offset: int, limit: int, total: int) -> str:
    shown_to = min(offset + limit, total)
    return f"Ko'rsatilmoqda: {offset + 1}-{shown_to} / Jami: {total} ta" if total else "Bo'sh"
