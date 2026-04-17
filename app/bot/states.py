from aiogram.fsm.state import State, StatesGroup

class InterrapidisimoFlow(StatesGroup):
    waiting_for_tracking_number = State()
    waiting_for_pqr_details = State()
