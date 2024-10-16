from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class FilterCallback(CallbackData, prefix='filter'):
    action: str

leave_button = InlineKeyboardButton(text='🙏 Оставить', callback_data=FilterCallback(action='keep').pack())
ban_button = InlineKeyboardButton(text='🚫 Забанить', callback_data=FilterCallback(action='ban').pack())

filter_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [leave_button, ban_button]
])