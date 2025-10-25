from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from states import ReviewState
from config import GAMES

router = Router()
db = Database()


@router.message(F.text == "💞 Мэтчи")
async def show_matches(message: Message, state: FSMContext):
    user_id = message.from_user.id
    games = await db.get_user_games(user_id)

    if not games:
        await message.answer("У вас пока нет анкет")
        return

    all_matches = []
    for game in games:
        matches = await db.get_matches(user_id, game)
        for match in matches:
            match['game'] = game
            all_matches.append(match)

    if not all_matches:
        await message.answer(
            "💔 У вас пока нет мэтчей\n\n"
            "Продолжайте искать тиммейтов в разделе Поиск!"
        )
        return

    text = "💞 <b>Ваши мэтчи:</b>\n\n"

    for i, match in enumerate(all_matches, 1):
        game_name = GAMES.get(match['game'])
        text += f"{i}. <b>{match['username']}</b> ({game_name})\n"

        if match.get('about_text'):
            # Показываем Discord или другие контакты из описания
            lines = match['about_text'].split('\n')
            for line in lines:
                if any(word in line.lower() for word in ['discord', 'telegram', 'steam', 'контакт']):
                    text += f"   📞 {line}\n"

        text += "\n"

    text += "💬 Напишите человеку и договоритесь об игре!"

    # Добавляем кнопки для отзывов
    builder = InlineKeyboardBuilder()
    for i, match in enumerate(all_matches):
        builder.button(
            text=f"⭐ Оставить отзыв {match['username']}",
            callback_data=f"review:{match['user_id']}:{match['game']}"
        )
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(F.text == "❤️ Лайки")
async def show_likes(message: Message):
    user_id = message.from_user.id
    games = await db.get_user_games(user_id)

    if not games:
        await message.answer("У вас пока нет анкет")
        return

    all_likes = []
    for game in games:
        likes = await db.get_incoming_likes(user_id, game)
        for like in likes:
            like['game'] = game
            all_likes.append(like)

    if not all_likes:
        await message.answer(
            "💔 Вас пока никто не лайкнул\n\n"
            "Не расстраивайтесь, продолжайте искать!"
        )
        return

    text = "❤️ <b>Вас лайкнули:</b>\n\n"

    for i, like in enumerate(all_likes, 1):
        game_name = GAMES.get(like['game'])
        text += f"{i}. <b>{like['username']}</b> ({game_name})\n"

        if like.get('positions'):
            text += f"   🎯 {', '.join(like['positions'])}\n"

        if like.get('goals'):
            text += f"   🎮 {', '.join(like['goals'])}\n"

        text += "\n"

    text += "💡 Лайкните их в ответ в разделе Поиск, чтобы создать мэтч!"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("review:"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    to_user_id = int(parts[1])
    game = parts[2]

    await state.update_data(review_to_user=to_user_id, review_game=game)

    await callback.message.answer(
        "⭐ Оцените игрока от 1 до 5 звезд:",
        reply_markup=get_rating_kb()
    )
    await state.set_state(ReviewState.choosing_rating)
    await callback.answer()


@router.callback_query(ReviewState.choosing_rating, F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(review_rating=rating)

    await callback.message.edit_text(
        f"Вы поставили {'⭐' * rating}\n\n"
        "Хотите добавить комментарий?\n"
        "Отправьте текст или нажмите /skip"
    )
    await state.set_state(ReviewState.entering_comment)
    await callback.answer()


@router.message(ReviewState.entering_comment)
async def process_review_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    from_user_id = message.from_user.id
    to_user_id = data.get('review_to_user')
    game = data.get('review_game')
    rating = data.get('review_rating')

    comment = None if message.text == "/skip" else message.text

    await db.add_review(from_user_id, to_user_id, game, rating, comment)

    await message.answer(
        "✅ Отзыв успешно добавлен!\n"
        "Спасибо за вашу оценку."
    )
    await state.clear()


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    # Тут можно показать отзывы о пользователе
    await message.answer(
        "📊 Раздел отзывов в разработке\n\n"
        "Здесь будут отображаться все отзывы о вас."
    )