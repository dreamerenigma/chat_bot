from database.database import create_connection

def get_game_from_db(name: str = None, link: str = None):
    """Retrieve a game from the database by game_name, short_name, or link."""
    conn = create_connection()
    cursor = conn.cursor()

    if link:
        cursor.execute("SELECT * FROM games WHERE link=?", (link,))
    elif name:
        cursor.execute("SELECT * FROM games WHERE game_name = ? OR short_name = ?", (name, name))
    else:
        return None

    game = cursor.fetchone()
    conn.close()

    if game:
        return {
            "id": game[0],
            "game_name": game[1],
            "bot_name": game[2],
            "description": game[3],
            "link": game[4],
            "image_path": game[5],
            "gif_path": game[6],
            "short_name": game[7],
        }

    return None


async def get_games_list_for_bot(bot_name: str) -> list:
    """Retrieve a list of games for a specific bot based on bot_name from the database."""
    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT game_name, short_name FROM games WHERE bot_name = ?", (bot_name,))
        games = cursor.fetchall()

        return [{'game_name': game[0], 'short_name': game[1]} for game in games]

    except Exception as e:
        print(f"Ошибка при получении списка игр: {e}")
        return []

    finally:
        if conn:
            conn.close()

def save_game_to_db(game_name: str, bot_name: str, description: str, link: str, image_path: str, gif_path: str, short_name: str):
    """Save or update game data in the database."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM games WHERE link=?", (link,))
    game = cursor.fetchone()

    if game:
        cursor.execute("""
            UPDATE games 
            SET game_name=?, bot_name=?, description=?, image_path=?, gif_path=?, short_name=? 
            WHERE link=?
        """, (game_name, bot_name, description, image_path, gif_path, short_name, link))
        conn.commit()
        conn.close()
        return True
    else:
        cursor.execute("""
            INSERT INTO games (game_name, bot_name, description, link, image_path, gif_path, short_name) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (game_name, bot_name, description, link, image_path, gif_path, short_name))
        conn.commit()
        conn.close()
        return False

def save_image_to_db(link: str, image_path: str):
    """Save or update the image path for a game in the database."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM games WHERE link=?", (link,))
    game = cursor.fetchone()

    if game:
        cursor.execute("""UPDATE games SET image_path=? WHERE link=? """, (image_path, link))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False