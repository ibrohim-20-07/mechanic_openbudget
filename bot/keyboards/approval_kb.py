from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks import VoteDecisionCB


def vote_decision_kb(vote_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=VoteDecisionCB(vote_id=vote_id, action="approve").pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=VoteDecisionCB(vote_id=vote_id, action="reject").pack(),
                ),
            ]
        ]
    )
