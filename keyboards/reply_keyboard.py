from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

@router.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.answer("Доступные опции:", reply_markup=create_keyboard())

@router.message(lambda message: message.text == "Общение с ботом")
async def chat_with_bot_command(message: types.Message, state: FSMContext):
    await handle_chat_command(message, state)

@router.message(Command("chat"))
async def handle_chat_command(message: types.Message, state: FSMContext):
    await message.answer("Вы начали общение с ботом.", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state("chat")

def register_menu_handler(dp):
    dp.include_router(router)

def create_keyboard():
    buttons = [
        [types.KeyboardButton(text="Общение с ботом"), types.KeyboardButton(text="Погода")],
        [types.KeyboardButton(text="Генерация картинок"), types.KeyboardButton(text="Генерация видео")]
    ]

    markup = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

    return markup

def create_ok_keyboard():
    ok_button = types.KeyboardButton(text="ОК")
    markup = types.ReplyKeyboardMarkup(
        keyboard=[[ok_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup

def create_rules_keyboard():
    agree_button = types.KeyboardButton(text="Согласен")
    disagree_button = types.KeyboardButton(text="Не согласен")
    markup = types.ReplyKeyboardMarkup(
        keyboard=[[agree_button, disagree_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup

def select_bot_keyboard(bot_name):
    bot_button = types.KeyboardButton(text=f"{bot_name}")
    markup = types.ReplyKeyboardMarkup(
        keyboard=[[bot_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup


def select_bots_keyboard(bots_list):
    if not bots_list:
        return None

    buttons = [types.KeyboardButton(text=f"@{bot_username}") for bot_username, bot_name in bots_list]

    markup = types.ReplyKeyboardMarkup(
        keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup
