from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from states import SearchState, ReportState
from config import GAMES

router = Router()
db = Database()


@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    user_id = message.from_user.id
    games = await db.get_user_games(user_id)

    if not games:
        await message.answer("Сначала создайте анкету!")
        return

    if len(games) > 1:
        await message.answer(
            "Выберите игру для поиска:",
            reply_markup=get_games_kb()
        )
        # Тут добавить обработчик выбора игры
    else:
        game = games[0]
        await state.update_data(search_game=game)
        await show_next_profile(message, state)


async def show_next_profile(message: Message, state: FSMContext):
    """Показывает следующую анкету"""
    data = await state.get_data()
    game = data.get('search_game')
    user_id = message.from_user.id

    profile = await db.get_next_profile(user_id, game)

    if not profile:
        # Предлагаем сбросить просмотренные
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Начать сначала", callback_data="reset_viewed")
        builder.button(text="🏠 В меню", callback_data="to_menu")

        await message.answer(
            "😔 Анкеты закончились!\n\n"
            "Вы просмотрели все доступные анкеты.\n"
            "Можете начать просмотр сначала или вернуться позже.",
            reply_markup=builder.as_markup()
        )
        return

    await state.update_data(current_profile_id=profile['user_id'])

    # Формируем текст анкеты
    game_name = GAMES.get(game)
    text = f"🎮 <b>{game_name}</b>\n"
    text += f"👤 <b>{profile['username']}</b>\n\n"

    if profile.get('country'):
        text += f"🌍 Страна: {profile['country']}\n"

    if profile.get('positions'):
        text += f"🎯 Позиции: {', '.join(profile['positions'])}\n"

    if profile.get('goals'):
        text += f"🎮 Цели: {', '.join(profile['goals'])}\n"

    if profile.get('avg_rating') > 0:
        text += f"⭐ Рейтинг: {profile['avg_rating']:.1f} ({profile['review_count']} отзывов)\n"

    if profile.get('about_text'):
        text += f"\n📝 О себе:\n{profile['about_text']}\n"

    # Отправляем анкету
    if profile.get('rating_screenshot'):
        await message.answer_photo(
            photo=profile['rating_screenshot'],
            caption=text,
            reply_markup=get_search_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_search_kb(),
            parse_mode="HTML"
        )

    await state.set_state(SearchState.viewing_profiles)


@router.callback_query(SearchState.viewing_profiles, F.data == "like")
async def handle_like(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_user_id = callback.from_user.id
    to_user_id = data.get('current_profile_id')
    game = data.get('search_game')

    # Добавляем лайк
    is_match = await db.add_like(from_user_id, to_user_id, game)

    if is_match:
        await callback.answer("💞 ЭТО МЭТЧ! Проверьте раздел 'Мэтчи'", show_alert=True)
    else:
        await callback.answer("❤️ Лайк отправлен!")

    # Показываем следующую анкету
    await callback.message.delete()
    await show_next_profile(callback.message, state)


@router.callback_query(SearchState.viewing_profiles, F.data == "dislike")
async def handle_dislike(callback: CallbackQuery, state: FSMContext):
    await callback.answer("👎")
    await callback.message.delete()
    await show_next_profile(callback.message, state)


@router.callback_query(SearchState.viewing_profiles, F.data == "report")
async def start_report(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=get_report_reasons_kb()
    )
    await state.set_state(ReportState.choosing_reason)
    await callback.answer()


@router.callback_query(ReportState.choosing_reason, F.data.startswith("report_reason:"))
async def handle_report_reason(callback: CallbackQuery, state: FSMContext):
    reason = callback.data.split(":")[1]
    await state.update_data(report_reason=reason)

    if reason == "Другое":
        await callback.message.edit_text(
            "📝 Опишите причину жалобы:",
            reply_markup=None
        )
        await state.set_state(ReportState.entering_comment)
    else:
        # Сохраняем жалобу
        data = await state.get_data()
        from_user_id = callback.from_user.id
        reported_user_id = data.get('current_profile_id')
        game = data.get('search_game')

        await db.add_report(from_user_id, reported_user_id, game, reason)

        await callback.answer("🚩 Жалоба отправлена", show_alert=True)
        await callback.message.delete()
        await show_next_profile(callback.message, state)
        await state.set_state(SearchState.viewing_profiles)

    await callback.answer()


@router.message(ReportState.entering_comment, F.text)
async def process_report_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    from_user_id = message.from_user.id
    reported_user_id = data.get('current_profile_id')
    game = data.get('search_game')
    reason = data.get('report_reason')

    await db.add_report(from_user_id, reported_user_id, game, reason, message.text)

    await message.answer("🚩 Жалоба отправлена")
    await show_next_profile(message, state)
    await state.set_state(SearchState.viewing_profiles)


@router.callback_query(F.data == "reset_viewed")
async def reset_viewed(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    game = data.get('search_game')

    await db.reset_viewed_profiles(user_id, game)

    await callback.answer("🔄 Начинаем сначала!")
    await callback.message.delete()
    await show_next_profile(callback.message, state)


@router.callback_query(ReportState.choosing_reason, F.data == "report_cancel")
async def cancel_report(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.viewing_profiles)

    # Возвращаем кнопки поиска
    await callback.message.edit_reply_markup(
        reply_markup=get_search_kb()
    )
    await callback.answer("Жалоба отменена")