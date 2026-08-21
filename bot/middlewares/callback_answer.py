from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class AutoAnswerCallbackMiddleware(BaseMiddleware):
    """Guarantees every callback query gets answered, even if the handler raises.

    Without this, an unhandled exception (or a forgotten .answer()) leaves the
    tapped inline button spinning in the user's client until Telegram times it
    out client-side — this is what shows up as the bot "hanging".
    """

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        finally:
            try:
                await event.answer()
            except Exception:  # noqa: BLE001 - already answered or too old, safe to ignore
                pass
