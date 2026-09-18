from aiogram.fsm.state import State, StatesGroup


class PostCreation(StatesGroup):
    waiting_topic = State()
    waiting_bullets = State()
    waiting_source_text = State()


class PostEditing(StatesGroup):
    waiting_new_text = State()
    waiting_image = State()


class Scheduling(StatesGroup):
    waiting_date = State()
    waiting_time = State()
