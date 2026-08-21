from aiogram.fsm.state import State, StatesGroup


class ProjectCreateStates(StatesGroup):
    waiting_name = State()
    waiting_url = State()
    waiting_target_choice = State()
    waiting_target_number = State()


class ProjectEditStates(StatesGroup):
    waiting_new_name = State()
    waiting_new_url = State()
    waiting_new_target_number = State()
