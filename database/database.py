import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def create_connection():
    """Create a database connection to the SQLite database specified by db_file."""
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_tables():
    """Create the necessary tables if they don't already exist."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT NOT NULL,
            bot_name TEXT NOT NULL,
            description TEXT,
            link TEXT NOT NULL,
            image_path TEXT,
            gif_path TEXT,
            short_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id INTEGER UNIQUE NOT NULL,
            bot_name TEXT NOT NULL,
            bot_username TEXT NOT NULL,
            token TEXT NOT NULL,
            about TEXT DEFAULT '🚫',
            description TEXT DEFAULT '🚫',
            description_picture TEXT DEFAULT '🚫 нет описания изображения',
            bot_pic TEXT DEFAULT '🖼 есть ботпик',
            commands TEXT DEFAULT 'пока нет команд',
            privacy_policy TEXT DEFAULT '🚫'
        )
    ''')

    conn.commit()
    conn.close()
