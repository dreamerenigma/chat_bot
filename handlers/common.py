from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ban_words import ban_words
from database.bots_database import get_bots_list_from_db
from filters.filters import ProfanityFilter, handle_profanity
from handlers.messages import welcome_text
from keyboards.reply_keyboard import select_bots_keyboard
from states.bot_states import BotForm, BotState, GameCreation

router = Router()

profanity_filter = ProfanityFilter(ban_words)

async def start_command(message: types.Message):
    await message.answer(welcome_text, parse_mode='HTML', disable_web_page_preview=True)

async def help_command(message: types.Message):
    await message.answer(welcome_text, parse_mode='HTML', disable_web_page_preview=True)

def register_handlers_common(dp):
    router.message.register(start_command, Command(commands=["start"]))
    router.message.register(help_command, Command(commands=["help"]))
    router.message(profanity_filter)(handle_profanity)
    dp.include_router(router)

@router.message(Command(commands=["id"]))
async def get_chat_id(message: types.Message):
    chat_id = message.chat.id
    await message.answer(f"ID группы: {chat_id}")

@router.message(Command(commands=["token"]))
async def generate_token_command(message: types.Message, state: FSMContext):
    bots_list = await get_bots_list_from_db()
    if bots_list:
        markup = select_bots_keyboard(bots_list)
        await message.answer("Выберите бота, чтобы получить его токен:", reply_markup=markup)

        await state.set_state(BotState.waiting_for_token_retrieval)
    else:
        await message.answer("У вас нет доступных ботов для просмотра токена.")

@router.message(Command(commands=["revoke"]))
async def generate_revoke_token_command(message: types.Message, state: FSMContext):
    bots_list = await get_bots_list_from_db()
    if bots_list:
        markup = select_bots_keyboard(bots_list)
        await message.answer("Выберите бота для генерации нового токена. Внимание: ваш старый токен перестанет работать.", reply_markup=markup)
        await state.set_state(BotState.waiting_for_token_revocation)
    else:
        await message.answer("У вас нет доступных ботов для генерации токена.")


@router.message(Command(commands=["clear"]))
async def clear_command(message: types.Message):
    await message.answer("Чат очищен!")


@router.message(Command(commands=["cancel"]))
async def cancel_command(message: types.Message):
    await message.answer("Нет активной команды для отмены. Я все равно ничего не делал. 😴...")


@router.message(Command(commands=["newbot"]))
async def newbot_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Хорошо, новый бот. Как мы его назовем? Пожалуйста, выберите имя для вашего бота.")
    await state.set_state(BotForm.waiting_for_bot_name)


@router.message(Command(commands=["editgame"]))
async def edit_game_command_handler(message: types.Message, state: FSMContext):
    await message.answer("Редактирование игр. Пожалуйста, пришлите мне игру или ссылку на игру (например, t.me/bot?game=game).")
    await state.set_state(GameCreation.waiting_for_game_edit)


@router.message(Command(commands=["deletegame"]))
async def delete_game_command(message: types.Message, state: FSMContext):
    await message.answer("Чтобы удалить игру, отправьте мне игру или ссылку на игру (например, t.me/bot?game=game).")
    await state.set_state(GameCreation.waiting_for_game_link)


@router.message(Command(commands=["deletebot"]))
async def delete_bot_command(message: types.Message, state: FSMContext):
    bots_list = await get_bots_list_from_db()
    if bots_list:
        markup = select_bots_keyboard(bots_list)
        await message.answer("Выберите бота для удаления:", reply_markup=markup)
        await state.set_state(BotState.waiting_for_delete_bot)
    else:
        await message.answer("У вас сейчас нет ботов. Используйте команду /newbot для создания первого бота.")


@router.message(Command(commands=["listgames"]))
async def delete_game(message: types.Message, state: FSMContext):
    bots_list = await get_bots_list_from_db()
    if bots_list:
        markup = select_bots_keyboard(bots_list)
        await message.answer("Выберите бота, чтобы получить список его игр.", reply_markup=markup)
        await state.set_state(GameCreation.waiting_list_games)
    else:
        await message.answer("У вас сейчас нет игр. Используйте команду /newgame для создания первой игры.")


@router.message(Command(commands=["skip"]))
async def skip_command(message: types.Message, state: FSMContext):
    await state.set_state(GameCreation.waiting_for_new_photo)
    await message.answer("Пожалуйста, отправьте новое фото. Используйте /skip, чтобы оставить фото как есть.")


@router.message(Command(commands=["skip"]), GameCreation.waiting_for_new_photo)
async def skip_photo_command(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте новый GIF. Используйте /skip, чтобы оставить GIF как есть, или /empty, чтобы удалить текущий GIF.")
    await state.clear()