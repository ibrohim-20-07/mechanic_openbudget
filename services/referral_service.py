from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.settings import REFERRAL_BONUS
from db.models.user import User
from repositories import referral_repo, settings_repo, user_repo
from services import balance_service


@dataclass
class ReferralCredit:
    referrer: User
    bonus_amount: Decimal


async def maybe_credit_first_vote_bonus(
    session: AsyncSession, referred_user: User, triggering_vote_id: int
) -> ReferralCredit | None:
    if referred_user.referred_by is None:
        return None

    referral = await referral_repo.get_by_referred_id(session, referred_user.telegram_id)
    if referral is None or referral.credited_at is not None:
        return None

    referrer = await user_repo.get_by_telegram_id(session, referred_user.referred_by)
    if referrer is None:
        return None

    bonus_raw = await settings_repo.get(session, REFERRAL_BONUS)
    bonus = Decimal(bonus_raw) if bonus_raw else Decimal("0")
    if bonus <= 0:
        return None

    await balance_service.adjust(
        session,
        referrer,
        bonus,
        reason=f"referral_bonus:{referred_user.telegram_id}",
    )
    referral.bonus_amount = bonus
    referral.triggering_vote_id = triggering_vote_id
    referral.credited_at = datetime.now(timezone.utc)
    await session.flush()

    return ReferralCredit(referrer=referrer, bonus_amount=bonus)
