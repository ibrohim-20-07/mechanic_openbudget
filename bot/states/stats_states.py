from aiogram.fsm.state import State, StatesGroup


class StatsStates(StatesGroup):
    waiting_start_date = State()
    waiting_end_date = State()
