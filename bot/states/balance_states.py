from aiogram.fsm.state import State, StatesGroup


class BalanceAdjustStates(StatesGroup):
    waiting_user_lookup = State()
    waiting_amount = State()
    waiting_reason = State()
