import asyncio
from bot_setup import create_bot, create_dispatcher
from database.database import create_tables
from utils.language import messages
from config import BASE_URL, WEBHOOK_PATH, HOST, PORT, USE_WEBHOOK, ENVIRONMENT
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

language = "ru"


def initialize_database():
    create_tables()


async def start_webhook(bot, dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(f"{BASE_URL}{WEBHOOK_PATH}")

    app = web.Application()
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=WEBHOOK_PATH)

    setup_application(app, dispatcher, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=HOST, port=PORT)
    print(f"Запуск вебхука на {BASE_URL}{WEBHOOK_PATH}")
    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await site.stop()
        await runner.cleanup()


async def start_long_polling(bot, dispatcher):
    print(messages[language]["bot_started"])
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


async def main():
    initialize_database()

    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        if ENVIRONMENT == "production" and USE_WEBHOOK:
            await start_webhook(bot, dispatcher)
        else:
            # await bot.delete_webhook(drop_pending_updates=True)
            await start_long_polling(bot, dispatcher)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print(messages[language]["bot_stopped"])
