from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def create_bot_action_keyboard():
    """Создает клавиатуру с действиями для бота."""
    buttons = [
        InlineKeyboardButton(text="API Token", callback_data="bot_action:token"),
        InlineKeyboardButton(text="Редактирование Бота", callback_data="bot_action:edit"),
        InlineKeyboardButton(text="Настройки Бота", callback_data="bot_action:settings"),
        InlineKeyboardButton(text="Оплата", callback_data="bot_action:payments"),
        InlineKeyboardButton(text="Передача права собственности", callback_data="bot_action:ownership"),
        InlineKeyboardButton(text="Удалить Бота", callback_data="bot_action:delete"),
        InlineKeyboardButton(text="« Вернуться к Списку Ботов", callback_data="bot_action:back")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])