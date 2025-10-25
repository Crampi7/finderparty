from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import get_main_menu_kb, get_games_kb
from states import ProfileCreation
from config import GAMES

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Добавляем пользователя в БД
    await db.add_user(user_id, username)

    # Проверяем наличие профилей
    games = await db.get_user_games(user_id)

    if games:
        await message.answer(
            f"👋 С возвращением, {message.from_user.first_name}!\n\n"
            "Выберите действие в меню:",
            reply_markup=get_main_menu_kb(has_profile=True)
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в TeamFinder!\n\n"
            "🎮 Это бот для поиска тиммейтов в CS2 и Dota 2.\n\n"
            "Для начала создайте анкету:",
            reply_markup=get_main_menu_kb(has_profile=False)
        )


@router.message(F.text == "📝 Создать анкету")
async def create_profile(message: Message, state: FSMContext):
    await message.answer(
        "🎮 Выберите игру для создания анкеты:",
        reply_markup=get_games_kb()
    )
    await state.set_state(ProfileCreation.choosing_game)


@router.message(F.text == "🎮 Сменить игру")
async def change_game(message: Message, state: FSMContext):
    user_id = message.from_user.id
    games = await db.get_user_games(user_id)

    text = "🎮 Выберите игру:\n\n"
    if games:
        for game in games:
            text += f"✅ {GAMES.get(game, game)} - анкета создана\n"

    await message.answer(text, reply_markup=get_games_kb())
    await state.set_state(ProfileCreation.choosing_game)


@router.callback_query(F.data == "to_menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    games = await db.get_user_games(user_id)

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu_kb(has_profile=bool(games))
    )
    await callback.answer()