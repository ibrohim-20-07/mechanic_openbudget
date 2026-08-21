from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import user_repo


def _extract_from_user(event: TelegramObject) -> TgUser | None:
    if isinstance(event, Update):
        inner = event.message or event.callback_query or event.edited_message
        return inner.from_user if inner else None
    return getattr(event, "from_user", None)


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = _extract_from_user(event)
        if tg_user is not None and not tg_user.is_bot:
            session: AsyncSession = data["session"]
            db_user = await user_repo.get_by_telegram_id(session, tg_user.id)
            if db_user is None:
                db_user = await user_repo.create_user(
                    session,
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    full_name=tg_user.full_name,
                )
            elif db_user.username != tg_user.username or db_user.full_name != tg_user.full_name:
                db_user.username = tg_user.username
                db_user.full_name = tg_user.full_name
            data["db_user"] = db_user
        return await handler(event, data)
