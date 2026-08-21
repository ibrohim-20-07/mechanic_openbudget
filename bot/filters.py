from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, is_admin: bool) -> bool:
        return is_admin
