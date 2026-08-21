import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.broadcast import Broadcast
from repositories import user_repo

BATCH_SIZE = 25
BATCH_PAUSE_SECONDS = 1.0


async def send_broadcast(
    session: AsyncSession, bot: Bot, text: str, photo_file_id: str | None = None
) -> Broadcast:
    users = await user_repo.list_not_blocked(session)
    sent = 0
    failed = 0

    for i, user in enumerate(users, start=1):
        try:
            if photo_file_id:
                await bot.send_photo(user.telegram_id, photo_file_id, caption=text)
            else:
                await bot.send_message(user.telegram_id, text)
            sent += 1
        except TelegramForbiddenError:
            user.is_blocked = True
            failed += 1
        except TelegramBadRequest:
            failed += 1

        if i % BATCH_SIZE == 0:
            await asyncio.sleep(BATCH_PAUSE_SECONDS)

    broadcast = Broadcast(text=text, photo_file_id=photo_file_id, sent_count=sent, failed_count=failed)
    session.add(broadcast)
    await session.flush()
    return broadcast
