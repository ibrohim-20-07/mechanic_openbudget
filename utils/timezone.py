from datetime import datetime
from zoneinfo import ZoneInfo

from config import settings

TASHKENT_TZ = ZoneInfo(settings.timezone)


def to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # values coming out of asyncpg for TIMESTAMPTZ columns are UTC-aware;
        # a naive value here means the DB session wasn't UTC-aware, treat as UTC
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TASHKENT_TZ)


def format_local(dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
    return to_local(dt).strftime(fmt)
