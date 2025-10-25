from aiogram.fsm.state import State, StatesGroup


class ProfileCreation(StatesGroup):
    choosing_game = State()
    entering_steam_link = State()
    entering_faceit_link = State()
    entering_dotabuff_link = State()
    choosing_country = State()
    choosing_positions = State()
    choosing_goals = State()
    entering_about = State()
    uploading_screenshot = State()
    confirming = State()


class SearchState(StatesGroup):
    viewing_profiles = State()


class ReviewState(StatesGroup):
    choosing_rating = State()
    entering_comment = State()


class ReportState(StatesGroup):
    choosing_reason = State()
    entering_comment = State()