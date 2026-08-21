from aiogram.fsm.state import State, StatesGroup


class WithdrawalStates(StatesGroup):
    waiting_card_number = State()
    waiting_amount = State()
