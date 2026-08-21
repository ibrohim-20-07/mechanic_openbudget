from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_content = State()
    confirm_preview = State()
