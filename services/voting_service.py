from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.project import Project
from db.models.settings import VOTE_PRICE
from db.models.user import User
from db.models.vote import Vote, VoteStatus
from repositories import project_repo, settings_repo, user_repo, vote_repo
from services import balance_service, project_service, referral_service
from services.referral_service import ReferralCredit


class VoteAlreadyDecided(Exception):
    """Raised when a vote is no longer pending (double-tap / race on the approval buttons)."""


@dataclass
class ConfirmResult:
    vote: Vote
    user: User
    reward_amount: Decimal
    referral_credit: ReferralCredit | None
    deactivated_project: Project | None
    activated_project: Project | None


async def submit_vote(
    session: AsyncSession,
    user: User,
    project: Project,
    phone_number: str,
    screenshot_file_ids: list[str],
) -> Vote:
    # the reward is locked in at the price shown to the user right now — if the admin
    # changes vote_price before this request is reviewed, this vote still pays the
    # amount the user was promised at submission time, not whatever the price is later.
    price_raw = await settings_repo.get(session, VOTE_PRICE)
    price = Decimal(price_raw) if price_raw else Decimal("0")

    return await vote_repo.create_vote(
        session,
        user_id=user.telegram_id,
        project_id=project.id,
        phone_number=phone_number,
        screenshot_file_ids=screenshot_file_ids,
        reward_amount=price,
    )


async def confirm_vote(session: AsyncSession, vote_id: int) -> ConfirmResult:
    vote = await vote_repo.get_pending_for_update(session, vote_id)
    if vote is None:
        raise VoteAlreadyDecided()

    price = vote.reward_amount

    vote.status = VoteStatus.CONFIRMED
    vote.decided_at = datetime.now(timezone.utc)
    await session.flush()

    project = await project_repo.get_by_id_for_update(session, vote.project_id)
    project.confirmed_votes_count += 1
    await session.flush()

    user = await user_repo.get_by_telegram_id(session, vote.user_id)
    await balance_service.adjust(
        session, user, price, reason=f"vote_confirmed:{vote.id}", related_vote_id=vote.id
    )

    is_first_confirmed = user.votes_confirmed_count == 0
    user.votes_confirmed_count += 1
    await session.flush()

    referral_credit = None
    if is_first_confirmed:
        referral_credit = await referral_service.maybe_credit_first_vote_bonus(
            session, user, vote.id
        )

    deactivated_project = None
    activated_project = None
    if (
        project.is_active
        and project.target_votes is not None
        and project.confirmed_votes_count >= project.target_votes
    ):
        activated_project = await project_service.advance_to_next(session, project)
        deactivated_project = project

    return ConfirmResult(
        vote=vote,
        user=user,
        reward_amount=price,
        referral_credit=referral_credit,
        deactivated_project=deactivated_project,
        activated_project=activated_project,
    )


async def reject_vote(session: AsyncSession, vote_id: int) -> Vote:
    vote = await vote_repo.get_pending_for_update(session, vote_id)
    if vote is None:
        raise VoteAlreadyDecided()

    vote.status = VoteStatus.REJECTED
    vote.decided_at = datetime.now(timezone.utc)
    await session.flush()
    return vote
