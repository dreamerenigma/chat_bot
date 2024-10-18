from decouple import config

ADMIN_ID = config("ADMIN_ID")
BOT_TOKEN = config("BOT_TOKEN")
HOST = config("HOST")
PORT = int(config("PORT"))
WEBHOOK_PATH = f'/{BOT_TOKEN}'
BASE_URL = config("BASE_URL")
ENVIRONMENT = config("ENVIRONMENT", "development")
USE_WEBHOOK = config("USE_WEBHOOK", cast=bool, default=False)

if BOT_TOKEN is None:
    raise ValueError("TOKEN_API is not set in the environment variables.")
