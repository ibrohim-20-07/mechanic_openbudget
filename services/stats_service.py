from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.balance_history import BalanceHistory
from db.models.referral import Referral
from db.models.user import User
from db.models.vote import Vote, VoteStatus
from db.models.withdrawal import Withdrawal, WithdrawalStatus

PERIOD_LABELS = {
    "today": "Bugun",
    "yesterday": "Kecha",
    "week": "Bu hafta",
    "month": "Bu oy",
    "all": "Umumiy",
}


@dataclass
class PeriodStats:
    label: str
    votes_total: int
    votes_confirmed: int
    votes_rejected: int
    votes_pending: int
    sum_credited: Decimal
    sum_withdrawn: Decimal
    new_users: int
    referral_bonus_paid: Decimal


def _today_bounds(tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _yesterday_bounds(tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_today, _ = _today_bounds(tz)
    return start_today - timedelta(days=1), start_today


def _week_bounds(tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_today, _ = _today_bounds(tz)
    monday = start_today - timedelta(days=datetime.now(tz).weekday())
    return monday, monday + timedelta(days=7)


def _month_bounds(tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.now(tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def resolve_period(period_key: str, tz: ZoneInfo) -> tuple[str, datetime | None, datetime | None]:
    if period_key == "today":
        start, end = _today_bounds(tz)
    elif period_key == "yesterday":
        start, end = _yesterday_bounds(tz)
    elif period_key == "week":
        start, end = _week_bounds(tz)
    elif period_key == "month":
        start, end = _month_bounds(tz)
    elif period_key == "all":
        return PERIOD_LABELS["all"], None, None
    else:
        raise ValueError(f"unknown period: {period_key}")
    return PERIOD_LABELS[period_key], start, end


async def get_period_stats(
    session: AsyncSession, label: str, start: datetime | None, end: datetime | None
) -> PeriodStats:
    vote_stmt = select(Vote.status, func.count()).group_by(Vote.status)
    if start is not None:
        vote_stmt = vote_stmt.where(Vote.created_at >= start, Vote.created_at < end)
    vote_rows = (await session.execute(vote_stmt)).all()
    counts = {status: count for status, count in vote_rows}
    votes_confirmed = counts.get(VoteStatus.CONFIRMED, 0)
    votes_rejected = counts.get(VoteStatus.REJECTED, 0)
    votes_pending = counts.get(VoteStatus.PENDING, 0)
    votes_total = votes_confirmed + votes_rejected + votes_pending

    credited_stmt = select(func.coalesce(func.sum(BalanceHistory.amount), 0)).where(
        BalanceHistory.reason.like("vote_confirmed:%")
    )
    if start is not None:
        credited_stmt = credited_stmt.where(
            BalanceHistory.created_at >= start, BalanceHistory.created_at < end
        )
    sum_credited = (await session.execute(credited_stmt)).scalar() or 0

    withdrawn_stmt = select(func.coalesce(func.sum(Withdrawal.amount), 0)).where(
        Withdrawal.status == WithdrawalStatus.PAID
    )
    if start is not None:
        withdrawn_stmt = withdrawn_stmt.where(
            Withdrawal.paid_at >= start, Withdrawal.paid_at < end
        )
    sum_withdrawn = (await session.execute(withdrawn_stmt)).scalar() or 0

    users_stmt = select(func.count()).select_from(User)
    if start is not None:
        users_stmt = users_stmt.where(User.created_at >= start, User.created_at < end)
    new_users = (await session.execute(users_stmt)).scalar() or 0

    ref_stmt = select(func.coalesce(func.sum(Referral.bonus_amount), 0)).where(
        Referral.credited_at.is_not(None)
    )
    if start is not None:
        ref_stmt = ref_stmt.where(Referral.credited_at >= start, Referral.credited_at < end)
    referral_bonus_paid = (await session.execute(ref_stmt)).scalar() or 0

    return PeriodStats(
        label=label,
        votes_total=votes_total,
        votes_confirmed=votes_confirmed,
        votes_rejected=votes_rejected,
        votes_pending=votes_pending,
        sum_credited=Decimal(sum_credited),
        sum_withdrawn=Decimal(sum_withdrawn),
        new_users=new_users,
        referral_bonus_paid=Decimal(referral_bonus_paid),
    )
