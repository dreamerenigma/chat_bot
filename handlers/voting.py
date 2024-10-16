from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
import random

class VotingCallback(CallbackData, prefix="voting"):
    action: str
    image_id: str

vote_counts = {}

router = Router()

user_votes = {}

message_votes = {}

def create_voting_keyboard(image_id):
    like_count = vote_counts[image_id]["like"]
    dislike_count = vote_counts[image_id]["dislike"]

    like_count_text = f'❤️ {like_count}' if like_count > 0 else '❤️'
    dislike_count_text = f'👎🏽 {dislike_count}' if dislike_count > 0 else '👎🏽'

    like_button = InlineKeyboardButton(
        text=like_count_text,
        callback_data=VotingCallback(action='like', image_id=image_id).pack()
    )
    dislike_button = InlineKeyboardButton(
        text=dislike_count_text,
        callback_data=VotingCallback(action='dislike', image_id=image_id).pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[like_button, dislike_button]])

async def get_random_image_url():
    image_id = str(random.randint(1, 1000))
    return f"https://picsum.photos/800/600?random={image_id}", image_id

@router.message(Command(commands=["vote"]))
async def vote_command(message: types.Message):
    image_url, image_id = await get_random_image_url()

    vote_counts[image_id] = {'like': 0, 'dislike': 0}

    sent_message = await message.answer_photo(
        photo=image_url,
        caption="Нравится ли вам эта фотография?",
        reply_markup=create_voting_keyboard(image_id=image_id)
    )

    if image_id not in message_votes:
        message_votes[image_id] = []
    message_votes[image_id].append(sent_message)

@router.callback_query(VotingCallback.filter())
async def vote_callback(callback: types.CallbackQuery, callback_data: VotingCallback):
    user_id = callback.from_user.id
    image_id = callback_data.image_id
    action = callback_data.action

    if image_id not in user_votes:
        user_votes[image_id] = {}

    previous_vote = user_votes[image_id].get(user_id)

    if previous_vote == action:
        vote_counts[image_id][action] -= 1
        del user_votes[image_id][user_id]
        await callback.answer(f"Вы отменили ваш голос за {action}")
    else:
        if previous_vote:
            vote_counts[image_id][previous_vote] -= 1

        vote_counts[image_id][action] += 1
        user_votes[image_id][user_id] = action
        await callback.answer(f"Вы проголосовали за {'❤️' if action == 'like' else '👎🏽'}")

    for msg in message_votes[image_id]:
        try:
            await msg.edit_reply_markup(
                reply_markup=create_voting_keyboard(image_id=image_id)
            )
        except Exception as e:
            print(f"Ошибка при обновлении сообщения: {e}")

def register_handlers_voting(dp):
    dp.include_router(router)
