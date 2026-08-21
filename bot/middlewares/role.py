from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import settings


def _extract_from_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Update):
        inner = event.message or event.callback_query or event.edited_message
        return inner.from_user.id if inner and inner.from_user else None
    from_user = getattr(event, "from_user", None)
    return from_user.id if from_user else None


class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _extract_from_user_id(event)
        data["is_admin"] = user_id is not None and user_id == settings.admin_id
        return await handler(event, data)
