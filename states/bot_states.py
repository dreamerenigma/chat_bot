from aiogram.fsm.state import StatesGroup, State


class UserForm(StatesGroup):
    waiting_for_username = State()
    confirmation_sent = State()
    waiting_for_new_bot_name = State()


class BotForm(StatesGroup):
    waiting_for_bot_name = State()
    waiting_for_bot_username = State()
    waiting_for_new_bot_pic = State()
    waiting_for_change_bot_command = State()


class BotState(StatesGroup):
    waiting_for_token_retrieval = State()
    waiting_for_token_revocation = State()
    waiting_for_delete_bot = State()
    waiting_for_confirmation = State()
    waiting_for_select_bot = State()


class ChatState(StatesGroup):
    chatting = State()


class GameCreation(StatesGroup):
    waiting_for_game_name = State()
    waiting_for_game_description = State()
    waiting_for_photo = State()
    waiting_for_gif_or_name = State()
    waiting_for_short_name = State()
    waiting_for_game_link = State()
    waiting_for_bot_selection = State()
    waiting_for_agreement = State()
    waiting_list_games = State()
    waiting_for_game_edit = State()
    waiting_for_new_title = State()
    waiting_for_new_photo = State()
