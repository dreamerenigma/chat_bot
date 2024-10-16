import sqlite3
from aiogram.types import Message
from database.database import create_connection


async def is_bot_username_taken(bot_username: str) -> bool:
    """Check if the bot username is already taken."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bots WHERE bot_username = ?", (bot_username,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


async def save_bot_to_db(bot_id: int, bot_name: str, bot_username: str, token: str,
                         about: str = '🚫', description: str = '🚫',
                         description_picture: str = '🚫 нет описания изображения', bot_pic: str = '🖼 есть ботпик',
                         commands: str = 'пока нет команд', privacy_policy: str = '🚫'):
    """Save a new bot to the database with additional fields."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO bots (bot_id, bot_name, bot_username, token,
                                          about, description, description_picture, 
                                          bot_pic, commands, privacy_policy) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (bot_id, bot_name, bot_username, token,
                    about, description, description_picture,
                    bot_pic, commands, privacy_policy))
    conn.commit()
    conn.close()


async def update_bot_in_db(bot_username: str, bot_name: str, token: str):
    """Update bot's name, username, and token in the database."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''UPDATE bots SET bot_name = ?, token = ? WHERE bot_username = ?''',
                   (bot_name, token, bot_username))
    conn.commit()
    conn.close()


async def update_bot_pic_in_db(bot_pic: str, bot_username: str):
    """Update bot's picture in the database."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''UPDATE bots SET bot_pic = ? WHERE bot_username = ?''',
                   (bot_pic, bot_username))
    conn.commit()
    conn.close()


async def save_token_to_db(bot_id: int, new_token: str) -> bool:
    """Save the new token to the database for the specified bot."""
    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bots SET token = ? WHERE bot_id = ?", (new_token, bot_id))
        conn.commit()

        if cursor.rowcount > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Произошла ошибка при сохранении токена: {e}")
        return False
    finally:
        if conn:
            conn.close()


async def get_bot_from_db(bot_username: str):
    """Retrieve a bot from the database by its username."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bots WHERE bot_username = ?", (bot_username,))
    bot = cursor.fetchone()
    conn.close()

    if bot:
        return {
            "id": bot[0],
            "bot_id": bot[1],
            "bot_name": bot[2],
            "bot_username": bot[3],
            "token": bot[4],
            "about": bot[5],
            "description": bot[6],
            "description_picture": bot[7],
            "bot_pic": bot[8],
            "commands": bot[9],
            "privacy_policy": bot[10]
        }
    return None


async def delete_bot_from_db(bot_username: str) -> bool:
    """Delete a bot from the database by its username."""
    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bots WHERE bot_username = ?", (bot_username,))
        conn.commit()

        if cursor.rowcount > 0:
            return True
        else:
            return False

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


async def get_bots_list_from_db():
    """Retrieve a bots from the database by its username."""
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT bot_username, bot_name FROM bots")
            bots = cursor.fetchall()
            conn.close()

            return bots
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []
    else:
        print("Не удалось подключиться к базе данных")
        return []


async def new_command_list_from_db(bot_id: int, bot_username: str, message: Message, db):
    new_commands = message.text.strip()

    print(f"New commands received: {new_commands}")
    print(f"Bot ID: {bot_id}, Bot Username: {bot_username}")

    if new_commands == "/empty":
        commands_list = ""
    else:
        commands_list = "\n".join(new_commands.split("\n"))

    if bot_id is not None and bot_username:
        try:
            await db.execute(
                """
                UPDATE bots
                SET commands = $1
                WHERE bot_id = $2 OR bot_username = $3
                """, (commands_list, bot_id, bot_username)
            )
            await db.commit()
            return True
        except Exception as e:
            print(f"Error updating commands: {e}")
            await message.answer("Не удалось обновить команды из-за ошибки.")
            return False
    else:
        await message.answer("Не удалось обновить команды. Не указаны bot_id или bot_username.")
        return False
