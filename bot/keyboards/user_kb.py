from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

VOTE_BUTTON = "📮 Ovoz berish"
ACCOUNT_BUTTON = "💰 Hisobim"
REFERRAL_BUTTON = "🔗 Referal"
WITHDRAW_BUTTON = "💸 Pul yechish"
MY_VOTES_BUTTON = "🗳 Ovozlarim"
CANCEL_BUTTON = "❌ Bekor qilish"

# Every reply-keyboard label a user can tap from the persistent main menu. FSM steps that
# accept free-text input must exclude these — otherwise tapping a menu button while mid-flow
# (e.g. mid vote-submission) gets silently swallowed as if it were the expected input, which
# looks like the bot "hanging" / ignoring the tap.
MENU_BUTTON_TEXTS = frozenset(
    {VOTE_BUTTON, ACCOUNT_BUTTON, REFERRAL_BUTTON, MY_VOTES_BUTTON, CANCEL_BUTTON}
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=VOTE_BUTTON)],
            [KeyboardButton(text=ACCOUNT_BUTTON), KeyboardButton(text=REFERRAL_BUTTON)],
            [KeyboardButton(text=MY_VOTES_BUTTON)],
        ],
        resize_keyboard=True,
    )


def cancel_only_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
    )
