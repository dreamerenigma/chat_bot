import random
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from database.bots_database import is_bot_username_taken, save_bot_to_db, get_bot_from_db, save_token_to_db, delete_bot_from_db
from handlers.user_handlers import choose_bots_command_handler
from states.bot_states import BotForm, BotState
from utils.token_generator import generate_token
from handlers.bot_actions import (
    update_bot_message,
    handle_token_action,
    handle_edit_action,
    handle_delete_action,
    handle_confirm_delete_action,
    handle_final_confirm_delete,
    handle_revoke_token, handle_payments_action, handle_settings_action, handle_ownership_action
)

router = Router()


@router.message(StateFilter(BotForm.waiting_for_bot_name))
async def process_bot_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state != BotForm.waiting_for_bot_name.state:
        await state.clear()
        await message.answer("Вы не находитесь в процессе создания бота. Используйте /newbot, чтобы начать снова.")
        return

    bot_name = message.text.strip()
    await state.update_data(bot_name=bot_name)
    await message.answer(
        "Хорошо. Теперь давайте выберем имя пользователя для вашего бота. Оно должно заканчиваться на `bot`. Например, так: TetrisBot или tetris_bot."
    )
    await state.set_state(BotForm.waiting_for_bot_username)


@router.message(StateFilter(BotForm.waiting_for_bot_username))
async def process_bot_username(message: types.Message, state: FSMContext):
    bot_username = message.text
    data = await state.get_data()
    bot_name = data.get("bot_name")

    if not (bot_username.endswith("bot") or bot_username.endswith("Bot")):
        await message.answer("Извините, имя пользователя должно заканчиваться на 'bot'. Например, 'Tetris_bot' или 'TetrisBot'.")
        return

    if await is_bot_username_taken(bot_username):
        await message.answer("Извините, это имя пользователя уже занято. Пожалуйста, попробуйте что-то другое.")
        return

    bot_id = random.randint(1000000000, 9999999999)
    token = generate_token()

    await save_bot_to_db(bot_id, bot_name, bot_username, token)
    await state.update_data(bot_id=bot_id, bot_name=bot_name, bot_username=bot_username, token=token)

    updated_data = await state.get_data()
    print(f"Updated state data: {updated_data}")

    await message.answer(
        f"Готово! Поздравляю с новым ботом. Вы найдете его на t.me/{bot_username}. "
        f"Теперь вы можете добавить описание, раздел «О нас» и фотографию профиля для своего бота. Список команд см. в /help. "
        f"Кстати, когда вы закончите создавать своего крутого бота, напишите в нашу службу поддержки ботов, если вам нужно лучшее имя пользователя для него. "
        f"Прежде чем сделать это, убедитесь, что бот полностью работоспособен.\n\n"
        f"<b>Используйте этот токен для доступа к HTTP API:</b>\n"
        f"<code>{bot_id}:{token}</code>\n"
        f"Храните свой токен в надежном месте, его может использовать любой желающий для управления вашим ботом.\n\n"
        f"Описание API бота см. на этой странице: https://core.telegram.org/bots/api",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await state.clear()


@router.callback_query(lambda c: c.data.startswith("bot_action"))
async def handle_bot_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "token":
        await handle_token_action(callback, state)
    elif action == "revoke_token":
        await handle_revoke_token(callback)
    elif action == "edit":
        await handle_edit_action(callback, state)
    elif action == "settings":
        await handle_settings_action(callback, state)
    elif action == "payments":
        await handle_payments_action(callback, state)
    elif action == "ownership":
        await handle_ownership_action(callback)
    elif action == "delete":
        await handle_delete_action(callback, state)
    elif action == "confirm_delete":
        await handle_confirm_delete_action(callback, state)
    elif action == "final_confirm_delete":
        await handle_final_confirm_delete(callback, state)
    elif action in ["nevermind", "hell_no", "no"]:
        await update_bot_message(callback, state)
    elif action == "back":
        await choose_bots_command_handler(callback.message, state)

    await callback.answer()


@router.callback_query(lambda c: c.data == "choose_bots")
async def handle_choose_bots(callback: CallbackQuery):
    message = callback.message
    await choose_bots_command_handler(message)
    await callback.answer()


@router.message(BotState.waiting_for_token_retrieval)
async def handle_bot_token(message: types.Message, state: FSMContext):
    bot_username = message.text[1:]

    bot_data = await get_bot_from_db(bot_username)
    if bot_data:
        bot_id = bot_data['bot_id']
        token = bot_data['token']

        response_message = (
            "Вы можете использовать этот токен для доступа к HTTP API:\n"
            f"<code>{bot_id}:{token}</code>\n\n"
            "Описание API бота смотрите на этой странице: https://core.telegram.org/bots/api"
        )

        await message.answer(response_message, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer("Ошибка: не удалось найти информацию о боте.")

    await state.clear()

@router.message(BotState.waiting_for_token_revocation)
async def handle_revoke_token(message: types.Message, state: FSMContext):
    bot_username = message.text[1:]

    bot_data = await get_bot_from_db(bot_username)
    if bot_data:
        bot_id = bot_data['bot_id']

        new_token = generate_token()

        try:
            await save_token_to_db(bot_id, new_token)
            response_message = (
                "Ваш токен был заменен на новый. Вы можете использовать этот токен для доступа к HTTP API:\n\n"
                f"<code>{bot_id}:{new_token}</code>"
            )
        except Exception as e:
            print(f"Ошибка при сохранении токена в базе данных: {e}")
            await message.answer("Ошибка: не удалось сохранить новый токен в базе данных.")
            return

        await message.answer(response_message, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer("Ошибка: не удалось найти информацию о боте.")

    await state.clear()


@router.message(BotState.waiting_for_delete_bot)
async def handle_bot_selection(message: types.Message, state: FSMContext):
    bot_username = message.text
    await state.update_data(bot_username=bot_username)

    confirmation_message = (
        f"Хорошо, вы выбрали {bot_username}. Вы уверены?\n"
        "Отправьте 'Да, я полностью уверен', чтобы подтвердить, что вы действительно хотите удалить этого бота."
    )
    await message.answer(confirmation_message)
    await state.set_state(BotState.waiting_for_confirmation)


@router.message(BotState.waiting_for_confirmation)
async def handle_bot_deletion_confirmation(message: types.Message, state: FSMContext):
    if message.text == "Да, я полностью уверен":
        data = await state.get_data()
        bot_username = data.get("bot_username")

        bot_username_cleaned = bot_username.replace("@", "")

        success = await delete_bot_from_db(bot_username_cleaned)

        if success:
            await message.answer(f"Готово! Бот @{bot_username_cleaned} удалён. /help")
        else:
            await message.answer(f"Не удалось удалить бота @{bot_username_cleaned}. Возможно, его уже нет в базе.")

        await state.clear()
    else:
        await message.answer("Пожалуйста, отправьте 'Да, я полностью уверен', чтобы подтвердить удаление.")


def register_bot_handlers(dp):
    dp.include_router(router)