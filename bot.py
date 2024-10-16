import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN_API
from database.database import create_tables
from middleware.middleware import ResetStateMiddleware
from utils.language import messages
from register_handlers import register_handlers

language = "ru"

bot = Bot(token=TOKEN_API)
storage = MemoryStorage()
dispatcher = Dispatcher(storage=storage, middlewares=[ResetStateMiddleware()])
register_handlers(dispatcher)


def initialize_database():
    create_tables()


async def main():
    initialize_database()
    print(messages[language]["bot_started"])
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print(messages[language]["bot_stopped"])
