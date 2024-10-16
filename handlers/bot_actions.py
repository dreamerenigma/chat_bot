import logging
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database.bots_database import delete_bot_from_db, get_bot_from_db, save_token_to_db, update_bot_in_db, update_bot_pic_in_db
from keyboards.inline_bot_options_keyboard import create_bot_action_keyboard
from states.bot_states import UserForm, BotForm
from utils.token_generator import generate_token

router = Router()

async def update_bot_message(callback: CallbackQuery, state: FSMContext, message=None):
    from handlers.user_handlers import choose_bots_command_handler

    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    if not bot_name or not bot_username:
        await callback.message.edit_text("Ошибка: недостаточно данных для выбора бота.")
        return

    response_message = message or f"Вот: {bot_name} @{bot_username}.\nЧто вы хотите сделать с ботом?"
    keyboard = create_bot_action_keyboard()

    old_markup_str = str(callback.message.reply_markup).strip()
    new_markup_str = str(keyboard).strip()

    if callback.message.text.strip() == response_message.strip() and old_markup_str == new_markup_str:
        logging.info("Сообщение уже актуально.")
        await callback.answer("Сообщение уже актуально.")
        return

    try:
        await callback.message.edit_text(response_message, reply_markup=keyboard)
        await callback.answer()
    except TelegramBadRequest as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await callback.answer("Произошла ошибка при обновлении сообщения.")

    if callback.data == "bot_action:back":
        await choose_bots_command_handler(callback.message, state)


async def handle_token_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")
    bot_data = await get_bot_from_db(bot_username)
    bot_id = data.get("bot_id")

    if bot_data:
        bot_id = bot_data['bot_id']
        token = bot_data['token']
        token_message = (
            f"Вот токен для бота {bot_name} @{bot_username}:\n\n"
            f"`{bot_id}:{token}`\n"
        )
    else:
        token_message = "Error: Bot data not found. Please check the bot username."

    buttons = [
        InlineKeyboardButton(text="Отозвать текущий токен", callback_data=f"bot_action:revoke_token:{bot_id}:{bot_name}:{bot_username}"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[buttons[0]], [buttons[1]]])

    await callback.message.edit_text(token_message, reply_markup=keyboard, parse_mode="Markdown")


async def handle_edit_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")
    bot_data = await get_bot_from_db(bot_username)

    if bot_data:
        about = bot_data.get("about", "🚫")
        description = bot_data.get("description", "🚫")
        description_picture = "🖼 есть описание картинки" if bot_data.get("description_picture") else "🚫 нет описания картинки"
        bot_pic = "🖼 есть ботпик" if bot_data.get("botpic") else "🚫 нет ботпика"
        commands = bot_data.get("commands", "нет команд")
        privacy_policy = bot_data.get("privacy_policy", "🚫")

        response_message = (
            f"Редактировать @{bot_username} информацию.\n\n"
            f"*Имя:* {bot_name}\n"
            f"*Информация:* {about}\n"
            f"*Описание:* {description}\n"
            f"*Описание изображения:* {description_picture}\n"
            f"*Ботпик:* {bot_pic}\n"
            f"*Команды:* {commands}\n"
            f"*Политика конфиденциальности:* {privacy_policy}"
        )

        response_message = response_message.replace('.', '\\.')

        buttons = [
            InlineKeyboardButton(text="Изменить Имя", callback_data="bot_action:change_name"),
            InlineKeyboardButton(text="Изменить Информацию", callback_data="bot_action:change_about"),
            InlineKeyboardButton(text="Изменить Описание", callback_data="bot_action:change_description"),
            InlineKeyboardButton(text="Изменить Описание Изображения", callback_data="bot_action:change_description_picture"),
            InlineKeyboardButton(text="Изменить Ботпик", callback_data="bot_action:change_botpic"),
            InlineKeyboardButton(text="Изменить Команды", callback_data="bot_action:change_commands"),
            InlineKeyboardButton(text="Изменить Политику Конфиденциальности", callback_data="bot_action:change_privacy"),
            InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back"),
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

        await callback.message.edit_text(response_message, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await callback.message.edit_text("Ошибка при получении данных о боте.")


async def handle_delete_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    buttons = [
        InlineKeyboardButton(text="Нет, неважно.", callback_data="bot_action:nevermind"),
        InlineKeyboardButton(text="Да, удалить бота", callback_data="bot_action:confirm_delete"),
        InlineKeyboardButton(text="Нет", callback_data="bot_action:no"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0]], [buttons[1]], [buttons[2]], [buttons[3]]
    ])

    await callback.message.edit_text(
        f"Вы собираетесь удалить своего бота {bot_name} @{bot_username}. Это верно?",
        reply_markup=keyboard
    )


async def handle_confirm_delete_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    confirmation_message = (
        f"Вы ПОЛНОСТЬЮ уверены, что хотите удалить бота {bot_name} @{bot_username} ?"
    )

    buttons = [
        InlineKeyboardButton(text="Нет!", callback_data="bot_action:no"),
        InlineKeyboardButton(text="Да, я уверен на 100%!", callback_data="bot_action:final_confirm_delete"),
        InlineKeyboardButton(text="Черт возьми, нет!", callback_data="bot_action:hell_no"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0]],
        [buttons[1]],
        [buttons[2]],
        [buttons[3]]
    ])

    await callback.message.edit_text(confirmation_message, reply_markup=keyboard)


async def handle_final_confirm_delete(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    deletion_successful = await delete_bot_from_db(bot_username)

    if deletion_successful:
        back_button = InlineKeyboardButton(text="« Назад к списку ботов", callback_data="bot_action:back")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        await callback.message.edit_text(f"Вы удалили {bot_name} @{bot_username}.", reply_markup=keyboard)
    else:
        await callback.message.edit_text("Ошибка при удалении бота. Попробуйте еще раз.")


async def handle_revoke_token(callback: CallbackQuery):
    _, action, bot_id_str, bot_name, bot_username = callback.data.split(":")
    bot_id = int(bot_id_str)

    new_token = generate_token()

    if await save_token_to_db(bot_id, new_token):
        token_message = (
            f"Токен для бота {bot_name} @{bot_username} был отозван.\n"
            f"Новый токен:\n\n"
            f"`{bot_id}:{new_token}`\n"
        )
    else:
        token_message = "Ошибка: не удалось обновить токен в базе данных."

    buttons = [
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[buttons[0]]])

    await callback.message.edit_text(token_message, reply_markup=keyboard, parse_mode="Markdown")


async def handle_payments_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")

    confirmation_message = (
        f"Payment providers for {bot_name} @{bot_username}."
    )

    buttons = [
        InlineKeyboardButton(text="🇷🇺 Сбербанк »", callback_data="bot_action:sber"),
        InlineKeyboardButton(text="🇷🇺 ЮKassa »", callback_data="bot_action:youkassa"),
        InlineKeyboardButton(text="🇷🇺 PayMaster »", callback_data="bot_action:paymaster"),
        InlineKeyboardButton(text="🇷🇺 Bank 131 »", callback_data="bot_action:bank131"),
        InlineKeyboardButton(text="🇷🇺 Robokassa »", callback_data="bot_action:robokassa"),
        InlineKeyboardButton(text="🇷🇺 PayBox.money »", callback_data="bot_action:paybox"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0]],
        [buttons[1]],
        [buttons[2]],
        [buttons[3]],
        [buttons[4]],
        [buttons[5]],
        [buttons[6]]
    ])

    await callback.message.edit_text(confirmation_message, reply_markup=keyboard)


async def handle_settings_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_username = data.get("bot_username")

    confirmation_message = (
        f"Settings for @{bot_username}."
    )

    buttons = [
        InlineKeyboardButton(text="Встроенный режим", callback_data="bot_action:inline_mode"),
        InlineKeyboardButton(text="Бизнес режим", callback_data="bot_action:business_mode"),
        InlineKeyboardButton(text="Разрешить группы?", callback_data="bot_action:allow_group"),
        InlineKeyboardButton(text="Групповая конфиденциальность", callback_data="bot_action:group_privacy"),
        InlineKeyboardButton(text="Права администратора группы", callback_data="bot_action:group_admin_rights"),
        InlineKeyboardButton(text="Права администратора канала", callback_data="bot_action:channel_admin_rights"),
        InlineKeyboardButton(text="Платежи", callback_data="bot_action:payments"),
        InlineKeyboardButton(text="Домен", callback_data="bot_action:domain"),
        InlineKeyboardButton(text="Кнопка меню", callback_data="bot_action:menu_button"),
        InlineKeyboardButton(text="Настроить мини-приложение", callback_data="bot_action:configure_mini_app"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0]],
        [buttons[1]],
        [buttons[2], buttons[3]],
        [buttons[4], buttons[5]],
        [buttons[6], buttons[7]],
        [buttons[7]],
        [buttons[8]],
        [buttons[9]],
        [buttons[10]]
    ])

    await callback.message.edit_text(confirmation_message, reply_markup=keyboard)


async def handle_ownership_action(callback: CallbackQuery):
    text_message = "Вы можете передать право собственности на бота другому пользователю Telegram."

    buttons = [
        InlineKeyboardButton(text="Выберите получателя", callback_data="bot_action:choose_recipient"),
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back")
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0]],
        [buttons[1]]
    ])

    await callback.message.edit_text(text_message, reply_markup=keyboard)


async def choose_recipient_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Пожалуйста, поделитесь контактной информацией нового владельца или его именем пользователя.")
    await callback.message.answer("Пожалуйста, поделитесь контактной информацией нового владельца или его именем пользователя.")
    await state.set_state(UserForm.waiting_for_username)


async def process_username(message: types.Message, state: FSMContext):
    try:
        logging.info(f"Received message: {message.text}")
        username = message.text.strip()

        current_user_username = f"@{message.from_user.username}" if message.from_user.username else None

        if len(username) == 0:
            await message.answer("Имя пользователя не может быть пустым. Пожалуйста, введите имя пользователя.")
        elif not username.startswith('@'):
            await message.answer("Неправильный формат. Обязательно отправьте контакт или имя пользователя.")
        elif not username[1:].isalnum() and not username[1:].replace('_', '').isalnum():
            await message.answer("Имя пользователя может содержать только буквы, цифры и символ '_'. Пожалуйста, попробуйте снова.")
        elif username == current_user_username:
            await message.answer("Право собственности на бота не может быть передано самому себе.")
        elif username.lower().startswith("@bot") or "channel" in username.lower():
            await message.answer("Право собственности на бота не может быть передано каналу или другому боту.")
        else:
            await message.answer("Упс! Убедитесь, что новый владелец отправил хотя бы одно сообщение боту и не заблокировал его.")
            await state.set_state(UserForm.confirmation_sent)
    except Exception as e:
        logging.error(f"Error in process_username: {e}")


async def handle_confirmation_sent(message: types.Message):
    await message.answer("Неправильный формат. Обязательно отправьте контакт или имя пользователя.")


async def choose_recipient_callback(callback: CallbackQuery, state: FSMContext):
    logging.info("choose_recipient_callback was called")
    await choose_recipient_action(callback, state)


async def change_bot_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer("ОК. Пришлите мне новое имя для вашего бота.")
    await callback.message.answer("ОК. Пришлите мне новое имя для вашего бота.")
    await state.set_state(UserForm.waiting_for_new_bot_name.state)


def create_return_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back"),
        InlineKeyboardButton(text="« Вернуться к Списку Ботов", callback_data="bot_action:back_to_list")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])


async def process_new_bot_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    token = data.get("token")
    bot_username = data.get("bot_username")

    await update_bot_in_db(bot_username=bot_username, bot_name=new_name, token=token)
    await state.update_data(bot_name=new_name)

    keyboard = create_return_keyboard()

    await message.answer(f"Успешно! Имя обновлено. /help", reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "bot_action:back_to_list")
async def handle_back_to_list(callback: CallbackQuery):
    from handlers.user_handlers import choose_bots_command_handler
    message = callback.message
    await choose_bots_command_handler(message)
    await callback.answer()


async def change_bot_botpic(callback: CallbackQuery, state: FSMContext):
    await callback.answer("ОК. Отправьте мне новую фотографию профиля для бота.")
    await callback.message.answer("ОК. Отправьте мне новую фотографию профиля для бота.")
    await state.set_state(BotForm.waiting_for_new_bot_pic.state)


async def process_new_bot_pic(message: types.Message, state: FSMContext):
    from bot import bot

    if not message.photo:
        await message.answer("Пожалуйста, отправьте изображение для обновления фотографии профиля.")
        return

    data = await state.get_data()
    bot_username = data.get("bot_username")

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)

    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)

    bot_pic_path = f"/assets/images/bot_pic/{bot_username}.jpg"

    with open(bot_pic_path, 'wb') as new_file:
        new_file.write(downloaded_file.read())

    await update_bot_pic_in_db(bot_username=bot_username, bot_pic=bot_pic_path)
    await state.update_data(bot_pic=bot_pic_path)

    keyboard = create_return_keyboard()

    await message.answer(f"Успех! Фотография профиля обновлена. /help", reply_markup=keyboard)