from aiogram import types, Bot, Dispatcher, Router
from aiogram.filters import BaseFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ChatPermissions
from ban_words import ban_words
from config import BOT_TOKEN
from keyboards.inline_filter_keyboard import filter_keyboard, FilterCallback

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dispatcher = Dispatcher(storage=storage)
router = Router()

original_vote_prompt = ""

user_offenses = {}
vote_counts = {}
vote_count = 0
total_votes_needed = 25
max_offenses = 5


class ProfanityFilter(BaseFilter):
    def __init__(self, bad_words: list):
        self.bad_words = bad_words

    async def __call__(self, message: types.Message) -> bool:
        return bool(message.text) and any(bad_word in message.text.lower() for bad_word in self.bad_words)


profanity_filter = ProfanityFilter(ban_words)


async def show_vote_window(message: types.Message):
    global vote_count
    global original_vote_prompt
    vote_count = 0

    offending_user = message.from_user.username or message.from_user.id
    original_vote_prompt = f"Пользователь @{offending_user} нарушил правила. Проголосуйте:"

    try:
        vote_message = f"{original_vote_prompt}\n\nПроголосовали {vote_count} из {total_votes_needed}"

        vote_msg = await message.answer(
            vote_message,
            reply_markup=filter_keyboard
        )

        user_offenses[message.from_user.id] = vote_msg.message_id
    except Exception as e:
        print(f"Error showing vote window: {e}")


@router.message(profanity_filter)
async def message_handler(message: types.Message):
    await handle_profanity(message)


@router.callback_query(FilterCallback.filter())
async def handle_vote(callback: types.CallbackQuery, callback_data: FilterCallback):
    global vote_count
    global original_vote_prompt

    action = callback_data.action
    user_id = callback.from_user.id

    if user_id in vote_counts:
        await callback.answer("Вы уже проголосовали!", show_alert=True)
        return

    vote_counts[user_id] = action
    vote_count += 1

    vote_message = f"{original_vote_prompt}\n\nПроголосовали {vote_count} из {total_votes_needed}."

    await callback.message.edit_text(vote_message, reply_markup=filter_keyboard)
    await callback.answer("Ваш голос учтен!")


async def ban_user(user_id: int, chat_id: int):
    chat = await bot.get_chat(chat_id)

    if chat.type in ["supergroup", "channel"]:
        try:
            permissions = ChatPermissions(can_send_messages=False)

            await bot.restrict_chat_member(chat_id, user_id, permissions=permissions)
            print(f"User {user_id} has been banned in chat {chat_id}.")
        except Exception as e:
            print(f"Failed to ban user {user_id}: {e}")
    else:
        print(f"Cannot ban user {user_id} in chat {chat_id} because it is not a supergroup.")


async def handle_profanity(message: types.Message):
    filtered_text = message.text
    for ban_word in ban_words:
        filtered_text = filtered_text.replace(ban_word, "*" * len(ban_word))

    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_offenses:
        user_offenses[user_id] = 0

    if filtered_text != message.text:
        user_offenses[user_id] += 1

        try:
            chat_member = await bot.get_chat_member(chat_id, user_id)
        except Exception as e:
            print(f"Failed to get chat member: {e}")
            chat_member = None

        if chat_member:
            if chat_member.status in ["administrator", "creator"]:
                await message.reply("Вы же админ, будьте культурны в выражениях!")
            else:
                await message.reply("Пожалуйста, избегайте нецензурных слов!")
        else:
            await message.reply("Пожалуйста, избегайте нецензурных слов!")

        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

        if user_offenses[user_id] >= max_offenses:
            try:
                await ban_user(user_id, chat_id)
            except Exception as e:

                if "not a supergroup" in str(e):
                    await bot.send_message(chat_id, "Невозможно забанить пользователя, так как чат не является супергруппой.")
                else:
                    print(f"Failed to ban user: {e}")

            if chat_member and chat_member.status not in ["administrator", "creator"]:
                try:
                    await bot.send_message(chat_id=chat_id, text="Вы были забанены за неоднократные нарушения правил.")
                except Exception as e:
                    print(f"Failed to send ban message: {e}")
            return

        if chat_member and chat_member.status not in ["administrator", "creator"]:
            if user_offenses[user_id] % 3 == 0 and user_offenses[user_id] < max_offenses:
                await show_vote_window(message)


def register_handlers_filter(dp):
    dp.include_router(router)
