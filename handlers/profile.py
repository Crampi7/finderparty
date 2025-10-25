from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from states import ProfileCreation
from config import GAMES, POSITIONS
import re

router = Router()
db = Database()


@router.callback_query(ProfileCreation.choosing_game, F.data.startswith("game:"))
async def game_selected(callback: CallbackQuery, state: FSMContext):
    game = callback.data.split(":")[1]
    await state.update_data(game=game, positions=[], goals=[])

    game_name = GAMES.get(game)

    text = (
        f"🎮 Вы выбрали: {game_name}\n\n"
        "📎 Отправьте ссылку на ваш Steam профиль\n"
        "(например: https://steamcommunity.com/id/username)"
    )

    await callback.message.edit_text(text, reply_markup=get_skip_kb())
    await state.set_state(ProfileCreation.entering_steam_link)
    await callback.answer()


@router.message(ProfileCreation.entering_steam_link)
async def process_steam_link(message: Message, state: FSMContext):
    if message.text and "steam" in message.text.lower():
        await state.update_data(steam_link=message.text)
    else:
        await state.update_data(steam_link=None)

    data = await state.get_data()
    game = data.get('game')

    if game == 'cs2':
        await message.answer(
            "📎 Отправьте ссылку на ваш FaceIT профиль\n"
            "(например: https://www.faceit.com/ru/players/nickname)",
            reply_markup=get_skip_kb()
        )
        await state.set_state(ProfileCreation.entering_faceit_link)
    elif game == 'dota2':
        await message.answer(
            "📎 Отправьте ссылку на ваш Dotabuff/OpenDota профиль",
            reply_markup=get_skip_kb()
        )
        await state.set_state(ProfileCreation.entering_dotabuff_link)


@router.callback_query(F.data == "skip")
async def skip_step(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    game = data.get('game')

    if current_state == ProfileCreation.entering_steam_link.state:
        await state.update_data(steam_link=None)
        if game == 'cs2':
            await callback.message.edit_text(
                "📎 Отправьте ссылку на ваш FaceIT профиль",
                reply_markup=get_skip_kb()
            )
            await state.set_state(ProfileCreation.entering_faceit_link)
        else:
            await callback.message.edit_text(
                "📎 Отправьте ссылку на ваш Dotabuff/OpenDota профиль",
                reply_markup=get_skip_kb()
            )
            await state.set_state(ProfileCreation.entering_dotabuff_link)

    elif current_state in [ProfileCreation.entering_faceit_link.state, ProfileCreation.entering_dotabuff_link.state]:
        await callback.message.edit_text(
            "🌍 Выберите вашу страну:",
            reply_markup=get_countries_kb()
        )
        await state.set_state(ProfileCreation.choosing_country)

    elif current_state == ProfileCreation.entering_about.state:
        await state.update_data(about_text=None)
        await callback.message.edit_text(
            "📸 Отправьте скриншот с вашим рейтингом/рангом\n"
            "(это поможет другим игрокам лучше понять ваш уровень)",
            reply_markup=get_skip_kb()
        )
        await state.set_state(ProfileCreation.uploading_screenshot)

    elif current_state == ProfileCreation.uploading_screenshot.state:
        await state.update_data(rating_screenshot=None)
        await show_profile_preview(callback.message, state)

    await callback.answer()


@router.message(ProfileCreation.entering_faceit_link)
async def process_faceit_link(message: Message, state: FSMContext):
    if message.text and "faceit" in message.text.lower():
        await state.update_data(faceit_link=message.text)
    else:
        await state.update_data(faceit_link=None)

    await message.answer(
        "🌍 Выберите вашу страну:",
        reply_markup=get_countries_kb()
    )
    await state.set_state(ProfileCreation.choosing_country)


@router.message(ProfileCreation.entering_dotabuff_link)
async def process_dotabuff_link(message: Message, state: FSMContext):
    if message.text and ("dotabuff" in message.text.lower() or "opendota" in message.text.lower()):
        await state.update_data(dotabuff_link=message.text)
    else:
        await state.update_data(dotabuff_link=None)

    await message.answer(
        "🌍 Выберите вашу страну:",
        reply_markup=get_countries_kb()
    )
    await state.set_state(ProfileCreation.choosing_country)


@router.callback_query(ProfileCreation.choosing_country, F.data.startswith("country:"))
async def country_selected(callback: CallbackQuery, state: FSMContext):
    country = callback.data.split(":")[1]
    if country == "none":
        country = None

    await state.update_data(country=country)

    data = await state.get_data()
    game = data.get('game')

    await callback.message.edit_text(
        f"🎯 Выберите ваши позиции/роли в игре:\n"
        f"(можно выбрать несколько)",
        reply_markup=get_positions_kb(game, [])
    )
    await state.set_state(ProfileCreation.choosing_positions)
    await callback.answer()


@router.callback_query(ProfileCreation.choosing_positions, F.data.startswith("pos_"))
async def handle_position(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    positions = data.get('positions', [])
    game = data.get('game')

    if callback.data.startswith("pos_add:"):
        position = callback.data.split(":")[1]
        if position not in positions:
            positions.append(position)
    elif callback.data.startswith("pos_remove:"):
        position = callback.data.split(":")[1]
        if position in positions:
            positions.remove(position)

    await state.update_data(positions=positions)

    await callback.message.edit_reply_markup(
        reply_markup=get_positions_kb(game, positions)
    )
    await callback.answer()


@router.callback_query(ProfileCreation.choosing_positions, F.data.in_(["positions_done", "positions_skip"]))
async def positions_done(callback: CallbackQuery, state: FSMContext):
    if callback.data == "positions_skip":
        await state.update_data(positions=[])

    await callback.message.edit_text(
        "🎯 Выберите ваши цели:\n(можно выбрать несколько)",
        reply_markup=get_goals_kb([])
    )
    await state.set_state(ProfileCreation.choosing_goals)
    await callback.answer()


@router.callback_query(ProfileCreation.choosing_goals, F.data.startswith("goal_"))
async def handle_goal(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    goals = data.get('goals', [])

    if callback.data.startswith("goal_add:"):
        goal = callback.data.split(":")[1]
        if goal not in goals:
            goals.append(goal)
    elif callback.data.startswith("goal_remove:"):
        goal = callback.data.split(":")[1]
        if goal in goals:
            goals.remove(goal)

    await state.update_data(goals=goals)

    await callback.message.edit_reply_markup(
        reply_markup=get_goals_kb(goals)
    )
    await callback.answer()


@router.callback_query(ProfileCreation.choosing_goals, F.data == "goals_done")
async def goals_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ Расскажите о себе:\n\n"
        "Например:\n"
        "• Ваш опыт игры и максимальный ранг\n"
        "• Время, когда вы обычно играете\n"
        "• Предпочитаемый стиль игры\n"
        "• Discord или другие контакты для связи\n\n"
        "Отправьте текст сообщением:"
    )
    await callback.message.delete()
    await state.set_state(ProfileCreation.entering_about)
    await callback.answer()


@router.message(ProfileCreation.entering_about, F.text)
async def process_about(message: Message, state: FSMContext):
    await state.update_data(about_text=message.text)

    await message.answer(
        "📸 Отправьте скриншот с вашим рейтингом/рангом\n"
        "(это поможет другим игрокам лучше понять ваш уровень)",
        reply_markup=get_skip_kb()
    )
    await state.set_state(ProfileCreation.uploading_screenshot)


@router.message(ProfileCreation.uploading_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(rating_screenshot=photo_id)

    await show_profile_preview(message, state)


async def show_profile_preview(message: Message, state: FSMContext):
    """Показывает превью анкеты"""
    data = await state.get_data()
    game_name = GAMES.get(data.get('game'))

    text = f"📋 <b>Ваша анкета для {game_name}</b>\n\n"

    if data.get('country'):
        text += f"🌍 Страна: {data['country']}\n"

    if data.get('positions'):
        text += f"🎯 Позиции: {', '.join(data['positions'])}\n"

    if data.get('goals'):
        text += f"🎮 Цели: {', '.join(data['goals'])}\n"

    if data.get('steam_link'):
        text += f"📎 Steam: {data['steam_link']}\n"

    if data.get('faceit_link'):
        text += f"📎 FaceIT: {data['faceit_link']}\n"

    if data.get('dotabuff_link'):
        text += f"📎 Dotabuff: {data['dotabuff_link']}\n"

    if data.get('about_text'):
        text += f"\n📝 О себе:\n{data['about_text']}\n"

    if data.get('rating_screenshot'):
        await message.answer_photo(
            photo=data['rating_screenshot'],
            caption=text,
            reply_markup=get_profile_confirm_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_profile_confirm_kb(),
            parse_mode="HTML"
        )

    await state.set_state(ProfileCreation.confirming)


@router.callback_query(ProfileCreation.confirming, F.data == "profile_save")
async def save_profile(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    game = data.get('game')

    # Сохраняем в БД
    await db.create_or_update_profile(user_id, game, data)

    # Получаем список игр пользователя
    games = await db.get_user_games(user_id)

    await callback.message.answer(
        "✅ Анкета успешно сохранена!\n\n"
        "Теперь вы можете начать поиск тиммейтов.",
        reply_markup=get_main_menu_kb(has_profile=True)
    )

    await callback.message.delete()
    await state.clear()
    await callback.answer()


@router.callback_query(ProfileCreation.confirming, F.data == "profile_cancel")
async def cancel_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    user_id = callback.from_user.id
    games = await db.get_user_games(user_id)

    await callback.message.answer(
        "❌ Создание анкеты отменено",
        reply_markup=get_main_menu_kb(has_profile=bool(games))
    )
    await callback.message.delete()
    await callback.answer()


@router.message(F.text == "📋 Моя анкета")
async def show_my_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    games = await db.get_user_games(user_id)

    if not games:
        await message.answer("У вас пока нет анкет. Создайте первую!")
        return

    # Если есть несколько игр, нужно выбрать
    if len(games) > 1:
        await message.answer(
            "Выберите игру для просмотра анкеты:",
            reply_markup=get_games_kb()
        )
        # Тут нужно будет добавить обработчик для просмотра конкретной анкеты
    else:
        game = games[0]
        profile = await db.get_profile(user_id, game)

        if profile:
            game_name = GAMES.get(game)
            text = f"📋 <b>Ваша анкета для {game_name}</b>\n\n"

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

            if profile.get('rating_screenshot'):
                await message.answer_photo(
                    photo=profile['rating_screenshot'],
                    caption=text,
                    parse_mode="HTML"
                )
            else:
                await message.answer(text, parse_mode="HTML")