from aiogram.fsm.state import State, StatesGroup


class GlobalSettingsStates(StatesGroup):
    waiting_vote_price = State()
    waiting_min_withdrawal = State()


class ReferralSettingsStates(StatesGroup):
    waiting_bonus = State()
    waiting_promo_text = State()
