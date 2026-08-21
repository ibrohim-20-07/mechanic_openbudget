import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from bot.middlewares.callback_answer import AutoAnswerCallbackMiddleware
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.register_user import RegisterUserMiddleware
from bot.middlewares.role import RoleMiddleware
from bot.routers import root_router
from config import settings
from db.base import async_session_factory
from repositories import settings_repo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
)
logger = logging.getLogger("openbudget")


async def seed_global_settings() -> None:
    async with async_session_factory() as session:
        await settings_repo.seed_defaults(session)


async def on_error(event: ErrorEvent) -> None:
    logger.exception("Handler xatosi: %s", event.exception, exc_info=event.exception)
    update = event.update
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if message is not None:
        try:
            await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.")
        except Exception:  # noqa: BLE001 - best-effort notification only
            pass


async def main() -> None:
    await seed_global_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(RegisterUserMiddleware())
    dp.update.outer_middleware(RoleMiddleware())
    dp.callback_query.outer_middleware(AutoAnswerCallbackMiddleware())

    dp.include_router(root_router)
    dp.errors.register(on_error)

    me = await bot.get_me()
    dp["bot_username"] = me.username

    logger.info("OpenBudget bot ishga tushmoqda (@%s)...", me.username)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
