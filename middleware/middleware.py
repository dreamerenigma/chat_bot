from aiogram import BaseMiddleware
from aiogram.types import Update


class ResetStateMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        if event.message and event.message.text.startswith('/'):
            state = data.get('state')
            if state:
                await state.finish()
        return await handler(event, data)
