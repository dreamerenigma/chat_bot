import hashlib
import os
import sqlite3
from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image, UnidentifiedImageError
from database.bots_database import get_bot_from_db, get_bots_list_from_db
from database.database import create_connection
from database.game_database import get_game_from_db, get_games_list_for_bot, save_game_to_db, save_image_to_db
from handlers.messages import rules_message
from keyboards.reply_keyboard import create_ok_keyboard, create_rules_keyboard, select_bots_keyboard
from states.bot_states import GameCreation, BotState

router = Router()

created_games = []

IMAGE_FOLDER = "D:/Programming/Languages/Python/Projects/Bots/Telegram/chat_bot/assets/images/game_image/other"
GIF_FOLDER = "D:/Programming/Languages/Python/Projects/Bots/Telegram/chat_bot/assets/images/game_image/gif"

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}

def allowed_file(file_name):
    return '.' in file_name and file_name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


def is_gif_file(filepath):
    try:
        with Image.open(filepath) as img:
            return img.format == 'GIF'
    except (OSError, UnidentifiedImageError) as e:
        print(f"Error identifying image file: {e}")
        return False


def generate_filename(file_id: str, file_format: str = 'jpg') -> str:
    hash_object = hashlib.md5(file_id.encode())
    short_hash = hash_object.hexdigest()[:10]
    return f"{short_hash}.{file_format}"


@router.message(Command(commands=["newgame"]))
async def new_game_command(message: types.Message):
    await message.answer(
        "Обслуживание определенных страниц определенным пользователям Telegram — чрезвычайно мощный инструмент, позволяющий создавать крутые игры HTML5 и интегрированные интерфейсы. Но такая мощь также требует большой ответственности со стороны разработчиков ботов. Пожалуйста, внимательно прочтите наши Правила и примите их только в том случае, если вы с ними согласны.",
        reply_markup=create_ok_keyboard()
    )


@router.message(lambda message: message.text == "ОК")
async def ok_button_handler(message: types.Message):
    await message.answer(rules_message, reply_markup=create_rules_keyboard())


@router.message(lambda message: message.text in ["Согласен", "Не согласен"])
async def agreement_handler(message: types.Message, state: FSMContext):
    if message.text == "Согласен":
        bots_list = await get_bots_list_from_db()
        if bots_list:
            markup = select_bots_keyboard(bots_list)
            await message.answer(
                "Очень хорошо. Какой бот будет предлагать игру? Обратите внимание, что целевой бот должен работать в режиме inline. Вы можете включить режим inline, отправив /setinline.",
                reply_markup=markup
            )
            await state.set_state(BotState.waiting_for_select_bot)
        else:
            await message.answer("У вас нет доступных ботов. Пожалуйста, добавьте ботов в систему.")
    else:
        await message.answer("Ладно, возвращайтесь, если передумаете.")


@router.message(BotState.waiting_for_select_bot)
async def select_bot_handler(message: types.Message, state: FSMContext):
    bot_name = message.text.strip()
    await state.update_data(bot_name=bot_name)
    await message.answer(f"Создание новой игры для {bot_name}. Введите краткое название игры.")
    await state.set_state(GameCreation.waiting_for_game_name)


@router.message(GameCreation.waiting_for_game_name)
async def game_description_handler(message: types.Message, state: FSMContext):
    game_name = message.text
    await state.update_data(game_name=game_name)
    await message.answer("Введите краткое описание игры.")
    await state.set_state(GameCreation.waiting_for_game_description)


@router.message(GameCreation.waiting_for_game_description)
async def game_photo_handler(message: types.Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer("Пожалуйста, загрузите фото размером 640x360 пикселей.")
    await state.set_state(GameCreation.waiting_for_photo)


@router.message(GameCreation.waiting_for_photo)
async def photo_handler(message: types.Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        file_name = generate_filename(file_id, 'jpg')

        if not allowed_file(file_name):
            await message.answer("Недопустимый формат файла.")
            return

        destination = os.path.join(IMAGE_FOLDER, file_name)

        await message.bot.download_file(file_path, destination)

        try:
            with Image.open(destination) as img:
                width, height = img.size
                if width != 640 or height != 360:
                    await message.answer("Извините, размеры изображения недействительны. Должно быть 640x360.")
                    os.remove(destination)
                    return

                if not file_name.lower().endswith('.jpg'):
                    file_name += '.jpg'
                destination = os.path.join(IMAGE_FOLDER, file_name)
                img.save(destination, format='JPEG')

        except OSError:
            if os.path.exists(destination):
                os.remove(destination)
            await message.answer("Ошибка при обработке изображения.")
            return None  # Return None for processing errors
        except Exception as e:
            await message.answer("Произошла непредвиденная ошибка.")
            print(f"Unexpected error: {e}")
            if os.path.exists(destination):
                os.remove(destination)
            return None  # Return None for unexpected errors

        await state.update_data(image_path=destination)
        await message.answer("Теперь загрузите демо-файл GIF или отправьте /empty, чтобы пропустить этот шаг.")
        await state.set_state(GameCreation.waiting_for_gif_or_name)
        return destination  # Return the valid image path
    else:
        await message.answer("Пожалуйста, загрузите изображение.")
        return None  # Return None if no image is found


@router.message(GameCreation.waiting_for_gif_or_name)
async def gif_handler(message: types.Message, state: FSMContext):
    if message.animation:
        animation = message.animation
        file_id = animation.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        file_name = generate_filename(file_id, 'gif')

        if not allowed_file(file_name):
            await message.answer("Недопустимый формат файла.")
            return

        if not file_name.lower().endswith('.gif'):
            file_name += '.gif'
        destination = os.path.join(GIF_FOLDER, file_name)

        try:
            await message.bot.download_file(file_path, destination)

            if not os.path.exists(destination):
                await message.answer("Не удалось загрузить файл GIF.")
                return

            if not is_gif_file(destination):
                await message.answer("Файл не является действительным GIF.")
                os.remove(destination)
                return

            with Image.open(destination) as img:
                img.verify()
                width, height = img.size
                if (width, height) not in [(320, 180), (640, 360), (960, 540)]:
                    await message.answer("Недопустимые размеры GIF. Должны быть 320x180, 640x360 или 960x540 пикселей.")
                    os.remove(destination)
                    return

                img.save(destination, format='GIF')

        except OSError as e:
            if os.path.exists(destination):
                os.remove(destination)
            await message.answer(f"Ошибка при обработке файла GIF: {e}")
            return
        except Exception as e:
            await message.answer("Произошла непредвиденная ошибка.")
            print(f"Unexpected error: {e}")
            if os.path.exists(destination):
                os.remove(destination)
            return

        await state.update_data(gif_path=destination)
        await message.answer(
            "Молодец! Теперь, пожалуйста, выберите короткое имя для вашей игры: 3-30 символов, a-zA-Z0-9_. Это короткое имя будет использоваться в URL-адресах типа t.me/DialogiusBot?game=tetris и служить уникальным идентификатором для вашей игры.")
        await state.set_state(GameCreation.waiting_for_short_name)

    elif message.text == "/empty":
        await empty_command_handler(message, state)
    else:
        await message.answer("Пожалуйста, загрузите GIF-анимацию или отправьте /empty, чтобы пропустить этот шаг.")


@router.message(Command(commands=["empty"]))
async def empty_command_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Нет проблем, вы всегда можете добавить GIF позже с помощью команды /editgame. "
        "Теперь выберите короткое имя для игры: 3-30 символов, a-zA-Z0-9_. "
        "Оно будет использоваться в URL-адресах типа t.me/DialogiusBot?game=tetris и служить уникальным идентификатором для вашей игры."
    )
    await state.set_state(GameCreation.waiting_for_short_name)


@router.message(GameCreation.waiting_for_short_name)
async def game_short_name_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    game_name = data.get("game_name")
    short_name = message.text.strip()
    bot_name = data.get('bot_name')

    if bot_name:
        bot_name = bot_name.lstrip('@')

    description = data.get('description')
    image_path = data.get('image_path')
    gif_path = data.get('gif_path', '🚫 не имеет GIF')

    if bot_name is None:
        await message.answer("Ошибка: Имя бота не задано.")
        return

    if 3 <= len(short_name) <= 30 and all(c.isalnum() or c in ['_', '-'] for c in short_name):
        game_link = f"https://t.me/DialogiusBot?game={short_name}"

        conn = None
        try:
            conn = create_connection()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO games (game_name, bot_name, description, link, image_path, gif_path, short_name)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (game_name, bot_name, description, game_link, image_path, gif_path, short_name))
            conn.commit()

            await state.update_data(short_name=short_name)

            await message.answer(
                f"Теперь вы можете использовать {short_name} как значение параметра short_name в Bot API. "
                f"Ваша ссылка на игру {game_link}. Откройте её, чтобы начать разработку игры!",
                disable_web_page_preview=True
            )
        except sqlite3.Error as e:
            await message.answer(f"Ошибка базы данных: {str(e)}")
        finally:
            if conn:
                conn.close()

        await state.clear()
    else:
        await message.answer(
            "Неверное короткое имя. Имя должно содержать от 3 до 30 символов и включать только латинские буквы, цифры, символы '_' или '-'.")


@router.message(Command(commands=["mygames"]))
async def choose_game_command_handler(message: types.Message):
    response_message = "Выберите игру:"

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, bot_name, short_name FROM games")
    games = cursor.fetchall()
    conn.close()

    if not games:
        await message.answer("У вас сейчас нет игр. Используйте команду /newgame для создания первой игры.")
        return

    buttons = [
        InlineKeyboardButton(text=f"{short_name} {bot_name}", callback_data=f"select_game:{game_name}")
        for game_name, bot_name, short_name in games
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

    await message.answer(response_message, reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("select_game:"))
async def select_game_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.update_data(previous_message_text=callback.message.text)

    data = await state.get_data()
    game_name = data.get("game_name")
    short_name = data.get("short_name")

    if not short_name:
        try:
            game_name = callback.data.split(":")[1]
            game_data = get_game_from_db(game_name)

            if game_data:
                short_name = game_data.get("short_name")
                await state.update_data(short_name=short_name)
            else:
                await callback.message.edit_text(f"Ошибка: Игра с именем {game_name} не найдена в базе данных.")
                return

        except IndexError:
            await callback.message.edit_text("Ошибка при извлечении данных игры.")
            return

    game_data = get_game_from_db(short_name)

    if game_data:
        link = game_data.get("link")
        description = game_data.get("description")
        gif_path = game_data.get("gif_path")

        response_message = (
            f"{game_name} `{short_name}`\n\n"
            f"*Поделиться URL:* {link}\n"
            f"*Описание:* {description}\n"
            f"*GIF:* {gif_path}\n"
        )

        response_message = response_message.replace('.', '\\.')
        response_message = response_message.replace('-', '\\-')
        response_message = response_message.replace('=', '\\=')
        response_message = response_message.replace('_', '\\_')

        buttons = [
            InlineKeyboardButton(text="Изменить заголовок", callback_data="bot_action:edit_title"),
            InlineKeyboardButton(text="Изменить описание", callback_data="bot_action:edit_description"),
            InlineKeyboardButton(text="Редактировать фото", callback_data="bot_action:edit_photo"),
            InlineKeyboardButton(text="Редактировать GIF", callback_data="bot_action:edit_gif"),
            InlineKeyboardButton(text="Удалить игру", callback_data="bot_action:delete_game"),
            InlineKeyboardButton(text="« Вернуться к Боту", callback_data="bot_action:back"),
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

        await callback.message.edit_text(response_message, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await callback.message.edit_text("Ошибка при получении данных о боте.")


@router.callback_query(lambda c: c.data == "bot_action:back")
async def back_to_bot_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    bot_name = data.get("bot_name")
    bot_username = data.get("bot_username")
    bot_data = await get_bot_from_db(bot_username)

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, bot_name, short_name FROM games")
    games = cursor.fetchall()
    conn.close()

    if not games:
        await callback.message.answer("У вас сейчас нет игр. Используйте команду /newgame для создания первой игры.")
        return

    if bot_data:
        response_message = (
            f"Вот список {bot_name} @{bot_username} игр:"
        )
    else:
        response_message = "Ошибка: Данные бота не найдены. Проверьте имя пользователя бота."

    buttons = [
        InlineKeyboardButton(text=f"{short_name}", callback_data=f"select_game:{game_name}")
        for game_name, _, short_name in games
    ]

    buttons.append(InlineKeyboardButton(text="« Вернуться к Списку Игр", callback_data="action:back_to_list_games"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

    await callback.message.edit_text(response_message, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "action:back_to_list_games")
async def back_to_list_games_callback(callback: CallbackQuery):
    await callback.answer()

    response_message = "Выберите игру:"

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, bot_name, short_name FROM games")
    games = cursor.fetchall()
    conn.close()

    if not games:
        await callback.message.answer("У вас сейчас нет игр. Используйте команду /newgame для создания первой игры.")
        return

    buttons = [
        InlineKeyboardButton(text=f"{short_name} {bot_name}", callback_data=f"select_game:{game_name}")
        for game_name, bot_name, short_name in games
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

    await callback.message.edit_text(response_message, reply_markup=keyboard)


@router.message(GameCreation.waiting_for_game_edit)
async def waiting_for_game_edit_handler(message: types.Message, state: FSMContext):
    game_link = message.text.strip()  # Ensure there are no extra spaces
    print(f"Game link received: '{game_link}'")  # Debug print

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name FROM games WHERE link=?", (game_link,))
    game = cursor.fetchone()
    conn.close()

    await state.update_data(game_link=game_link)

    if game:
        description = game[0]
        await message.answer(
            f"Хорошо. Пожалуйста, введите новый заголовок. Текущий заголовок: {description}. Используйте /skip, чтобы оставить заголовок как есть."
        )
        await state.set_state(GameCreation.waiting_for_new_title)
    else:
        await message.answer("Игра с такой ссылкой не найдена в базе данных.")


@router.message(lambda message: message.text is not None, GameCreation.waiting_for_new_title)
async def new_title_handler(message: types.Message, state: FSMContext):
    new_title = message.text
    data = await state.get_data()
    game_link = data.get("game_link").strip()

    existing_game = get_game_from_db(new_title, game_link)
    if existing_game:
        description = existing_game['description']
        save_game_to_db(
            game_name=new_title,
            bot_name=existing_game['bot_name'],
            description=description,
            link=game_link,
            image_path=existing_game['image_path'],
            gif_path=existing_game['gif_path'],
            short_name=existing_game['short_name'],
        )

        response_message = (
            f"*Пожалуйста, введите новое описание*.\n\n"
            f"*Текущее описание:* {description}\n\n Используйте /skip, чтобы оставить описание как есть."
        )

        response_message = (
            response_message
            .replace('.', '\\.')
            .replace('-', '\\-')
            .replace('(', '\\(')
            .replace(')', '\\)')
        )
        await message.answer(response_message, parse_mode='MarkdownV2')
    else:
        await message.answer("Игра с такой ссылкой не найдена в базе данных.")
    await state.clear()


@router.message(lambda message: message.photo is not None, GameCreation.waiting_for_new_photo)
async def new_photo_handler(message: types.Message, state: FSMContext):
    if message.photo:
        image_path = await photo_handler(message, state)
        if image_path:
            data = await state.get_data()
            link = data.get("game_link")

            if link:
                save_image_to_db(link, image_path=image_path)
                await message.answer("Фото успешно получено! Используйте /skip, чтобы оставить фото как есть.")
            else:
                await message.answer("Не удалось найти ссылку на игру. Проверьте, правильно ли она была сохранена.")
        else:
            await message.answer("Не удалось сохранить фото. Попробуйте еще раз.")
    await state.clear()


@router.message(lambda message: message.text is not None and message.text.startswith("https://t.me/"))
async def game_link_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "waiting_for_game_link":
        return

    game_link = message.text

    await message.answer("Ссылка получена!")

    short_name = game_link.split("game=")[-1] if "game=" in game_link else None

    if not short_name:
        await message.answer("Неверная ссылка на игру. Пожалуйста, отправьте правильную ссылку.")
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name FROM games WHERE link=?", (game_link,))
    game = cursor.fetchone()
    conn.close()

    if game:
        game_name = game[0]
        await message.answer(f"Хорошо, удаляю {game_name} ({short_name}). Пожалуйста, введите 'Да, я полностью уверен.', чтобы продолжить.")
        await state.update_data(game_link=game_link, game_name=game_name)
        await state.set_state("waiting_for_confirmation")
    else:
        await message.answer("Игра с такой ссылкой не найдена в базе данных.")


@router.message(StateFilter("waiting_for_confirmation"))
async def confirmation_handler(message: types.Message, state: FSMContext):
    user_input = message.text.strip().lower()

    if user_input == "да, я полностью уверен.":
        data = await state.get_data()
        game_link = data.get("game_link")

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM games WHERE link=?", (game_link,))
        conn.commit()

        if cursor.rowcount > 0:
            await message.answer("Игра была успешно удалена.")
        else:
            await message.answer("Игра не была найдена в базе данных для удаления.")

        conn.close()
        await state.clear()
    else:
        await message.answer(
            "Удаление отменено. Пожалуйста, введите 'Да, я полностью уверен.', чтобы подтвердить удаление.")
        await state.clear()


@router.message(GameCreation.waiting_list_games)
async def handle_bot_selection_for_games(message: types.Message, state: FSMContext):
    bot_name = message.text
    await state.update_data(bot_name=bot_name)

    games_list = await get_games_list_for_bot(bot_name)

    if games_list:
        games_message = "Игры:\n"
        for game in games_list:
            games_message += f"{game['game_name']} ({game['short_name']})\n"

        await message.answer(games_message)
    else:
        await message.answer(f"Для бота {bot_name} игр не найдено. Используйте команду /newgame для создания игры.")

    await state.clear()
