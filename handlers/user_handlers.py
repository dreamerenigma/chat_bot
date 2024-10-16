from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.bots_database import get_bot_from_db
from database.database import create_connection
from handlers.bot_actions import update_bot_message

router = Router()

@router.message(Command(commands=["mybots"]))
async def choose_bots_command_handler(message: types.Message, state: FSMContext):
    await state.clear()
    response_message = "Выберите бота из списка ниже:"

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bot_username, bot_name FROM bots")
    bots = cursor.fetchall()
    conn.close()

    if not bots:
        await message.answer("У вас сейчас нет ботов. Используйте команду /newbot для создания первого бота.")
        return

    buttons = []
    for bot in bots:
        bot_username, bot_name = bot
        button = InlineKeyboardButton(
            text=f"@{bot_username}",
            callback_data=f"select_bot:{bot_username}:{bot_name}"
        )
        buttons.append(button)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

    await message.answer(response_message, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "bot_action:back")
async def back_to_bot_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    if not bot_name or not bot_username:
        print("Попытка вернуться к списку ботов без данных о боте.")
        await callback.message.edit_text("Ошибка: недостаточно данных для возврата к списку ботов.")
        return

    try:
        await choose_bots_command_handler(callback.message, state)
    except Exception as e:
        print(f"Ошибка при возврате к списку ботов: {e}")
        await callback.message.answer("Произошла ошибка при возврате к списку ботов.")


@router.callback_query(lambda c: c.data.startswith("select_bot"))
async def handle_bot_selection(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ошибка: неверные данные выбора.")
        return

    _, bot_username, bot_name = parts
    await state.update_data(bot_name=bot_name, bot_username=bot_username)

    bot_data = await get_bot_from_db(bot_username)
    if bot_data is None:
        await callback.message.edit_text("Ошибка при получении данных о боте.")
        return

    token = bot_data['token']
    await state.update_data(token=token)

    await update_bot_message(callback, state)

def register_user_handlers(dp):
    dp.include_router(router)