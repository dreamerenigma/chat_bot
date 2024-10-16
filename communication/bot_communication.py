from aiogram import types, Router
from aiogram.fsm.context import FSMContext

router = Router()


@router.message()
async def echo_message(message: types.Message, state: FSMContext):
    if await state.get_state() == "chat":
        user_id = message.from_user.id
        reply_message = f"Вы сказали: {message.text}"
        await send_message_to_user(user_id, reply_message, message.bot)


async def send_message_to_user(user_id: int, message: str, bot):
    """Отправить сообщение пользователю."""
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


def register_handlers(dp):
    dp.include_router(router)
