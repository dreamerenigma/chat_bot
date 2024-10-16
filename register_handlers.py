from aiogram import Dispatcher
from handlers import common, voting
from handlers.bot_actions import handle_ownership_action, choose_recipient_callback, process_username, \
    handle_confirmation_sent, change_bot_name, process_new_bot_name, change_bot_botpic, process_new_bot_pic
from handlers.bot_command import change_bot_command
from keyboards.reply_keyboard import register_menu_handler
from handlers.game_handlers import router as game_router
from filters.filters import register_handlers_filter
from handlers.bot_handlers import register_bot_handlers
from handlers.user_handlers import register_user_handlers
from states.bot_states import UserForm, BotForm


def register_handlers(dp: Dispatcher):
    # Регистрация всех обработчиков
    common.register_handlers_common(dp)
    voting.register_handlers_voting(dp)
    register_menu_handler(dp)

    # Подключение роутеров
    dp.include_router(game_router)
    register_handlers_filter(dp)
    register_bot_handlers(dp)
    register_user_handlers(dp)

    # Регистрация callback'ов
    dp.callback_query.register(handle_ownership_action, lambda c: c.data == "bot_action:ownership")
    dp.callback_query.register(choose_recipient_callback, lambda c: c.data == "bot_action:choose_recipient")
    dp.callback_query.register(change_bot_name, lambda c: c.data == "bot_action:change_name")
    dp.callback_query.register(change_bot_botpic, lambda c: c.data == "bot_action:change_botpic")
    dp.callback_query.register(change_bot_command, lambda c: c.data == "bot_action:change_commands")

    # Регистрация сообщений
    dp.message.register(process_username, UserForm.waiting_for_username)
    dp.message.register(handle_confirmation_sent, UserForm.confirmation_sent)
    dp.message.register(process_new_bot_name, UserForm.waiting_for_new_bot_name)

    # Регистрация обработчика для фотографий
    dp.message.register(process_new_bot_pic, BotForm.waiting_for_new_bot_pic)
