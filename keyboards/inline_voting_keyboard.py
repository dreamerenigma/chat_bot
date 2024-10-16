from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

class VotingCallback(CallbackData, prefix="voting"):
    action: str

like_button = InlineKeyboardButton(text='❤️', callback_data=VotingCallback(action='like').pack())
dislike_button = InlineKeyboardButton(text='👎🏽', callback_data=VotingCallback(action='dislike').pack())

voting_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [like_button, dislike_button]
])
