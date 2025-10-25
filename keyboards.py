from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Optional
from config import GAMES, COUNTRIES, POSITIONS, GOALS, REPORT_REASONS


def get_main_menu_kb(has_profile: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()

    if has_profile:
        builder.row(
            KeyboardButton(text="🔍 Поиск"),
            KeyboardButton(text="📋 Моя анкета")
        )
        builder.row(
            KeyboardButton(text="❤️ Лайки"),
            KeyboardButton(text="💞 Мэтчи")
        )
        builder.row(
            KeyboardButton(text="🎮 Сменить игру"),
            KeyboardButton(text="⭐ Отзывы")
        )
    else:
        builder.row(
            KeyboardButton(text="📝 Создать анкету")
        )

    return builder.as_markup(resize_keyboard=True)


def get_games_kb() -> InlineKeyboardMarkup:
    """Выбор игры"""
    builder = InlineKeyboardBuilder()
    for game_key, game_name in GAMES.items():
        builder.button(text=game_name, callback_data=f"game:{game_key}")
    builder.adjust(1)
    return builder.as_markup()


def get_skip_kb() -> InlineKeyboardMarkup:
    """Кнопка пропустить"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="skip")
    return builder.as_markup()


def get_countries_kb() -> InlineKeyboardMarkup:
    """Выбор страны"""
    builder = InlineKeyboardBuilder()
    for country in COUNTRIES:
        builder.button(text=country, callback_data=f"country:{country}")
    builder.button(text="🌍 Не указывать", callback_data="country:none")
    builder.adjust(2)
    return builder.as_markup()


def get_positions_kb(game: str, selected: List[str] = None) -> InlineKeyboardMarkup:
    """Выбор позиций/ролей"""
    selected = selected or []
    builder = InlineKeyboardBuilder()

    positions = POSITIONS.get(game, [])
    for position in positions:
        if position in selected:
            builder.button(text=f"✅ {position}", callback_data=f"pos_remove:{position}")
        else:
            builder.button(text=position, callback_data=f"pos_add:{position}")

    builder.adjust(2)

    if selected:
        builder.row(
            InlineKeyboardButton(text="✔️ Готово", callback_data="positions_done")
        )

    builder.row(
        InlineKeyboardButton(text="⏭ Не указывать", callback_data="positions_skip")
    )

    return builder.as_markup()


def get_goals_kb(selected: List[str] = None) -> InlineKeyboardMarkup:
    """Выбор целей"""
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for goal in GOALS:
        if goal in selected:
            builder.button(text=f"✅ {goal}", callback_data=f"goal_remove:{goal}")
        else:
            builder.button(text=goal, callback_data=f"goal_add:{goal}")

    builder.adjust(2)

    if selected:
        builder.row(
            InlineKeyboardButton(text="✔️ Готово", callback_data="goals_done")
        )

    return builder.as_markup()


def get_profile_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение анкеты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="profile_save"),
        InlineKeyboardButton(text="🔄 Изменить", callback_data="profile_edit")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отменить", callback_data="profile_cancel")
    )
    return builder.as_markup()


def get_search_kb() -> InlineKeyboardMarkup:
    """Кнопки для поиска"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❤️ Лайк", callback_data="like"),
        InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike")
    )
    builder.row(
        InlineKeyboardButton(text="🚩 Жалоба", callback_data="report")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")
    )
    return builder.as_markup()


def get_report_reasons_kb() -> InlineKeyboardMarkup:
    """Причины жалоб"""
    builder = InlineKeyboardBuilder()
    for reason in REPORT_REASONS:
        builder.button(text=reason, callback_data=f"report_reason:{reason}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="report_cancel")
    )
    return builder.as_markup()


def get_rating_kb() -> InlineKeyboardMarkup:
    """Выбор рейтинга"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text="⭐" * i, callback_data=f"rating:{i}")
    builder.adjust(1)
    return builder.as_markup()


def get_back_to_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В главное меню", callback_data="to_menu")
    return builder.as_markup()