from aiogram.fsm.state import State, StatesGroup


class VotingStates(StatesGroup):
    waiting_phone = State()
    waiting_vote_confirm = State()
    waiting_screenshot = State()
