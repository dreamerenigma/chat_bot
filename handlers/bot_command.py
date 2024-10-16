from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.bots_database import new_command_list_from_db
from states.bot_states import BotForm

router = Router()


async def change_bot_command(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        "ОК. Отправьте мне список команд для вашего бота. Пожалуйста, используйте этот формат:\n\n"
        "command1 - Описание\n"
        "command2 - Другое описание\n\n"
        "Отправьте /empty, чтобы оставить список пустым."
    )
    await callback.message.answer(
        "ОК. Отправьте мне список команд для вашего бота. Пожалуйста, используйте этот формат:\n\n"
        "command1 - Описание\n"
        "command2 - Другое описание\n\n"
        "Отправьте /empty, чтобы оставить список пустым."
    )
    await state.set_state(BotForm.waiting_for_change_bot_command)


@router.message(BotForm.waiting_for_change_bot_command)
async def process_command_list(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    bot_username = data.get("bot_username")

    success = await new_command_list_from_db(bot_id, bot_username, message, state)

    if success:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Back to Bot", callback_data="bot_action:back_to_bot"),
                    InlineKeyboardButton(text="Back to Bots List", callback_data="bot_action:back_to_bots_list")
                ]
            ]
        )

        await message.answer("Success! Command list updated. /help", reply_markup=keyboard)
    else:
        await message.answer("Error: Could not update command list.")

    if success:
        await message.answer("Success! Command list updated. /help")
    else:
        await message.answer("Failed to update commands.")
