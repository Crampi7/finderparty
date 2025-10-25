import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Игры
GAMES = {
    'cs2': 'Counter-Strike 2',
    'dota2': 'Dota 2'
}

# Страны
COUNTRIES = [
    'Россия', 'Беларусь', 'Украина',
    'Казахстан', 'Узбекистан', 'Другое'
]

# Позиции/роли
POSITIONS = {
    'cs2': ['Support', 'Sniper', 'Lurker', 'Entry-Fragger', 'IGL'],
    'dota2': ['Carry', 'Midlaner', 'Offlaner', 'Soft Support', 'Hard Support']
}

# Цели
GOALS = [
    'Публики', 'Рейтинговые игры',
    'Турниры', 'Общение'
]

# Причины жалоб
REPORT_REASONS = [
    'Оскорбления/токсичность',
    'Мошенничество',
    'Неадекватное поведение',
    'Спам/реклама',
    'Фейковая анкета',
    'Другое'
]