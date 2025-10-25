import aiosqlite
import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "teamfinder.db"):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица профилей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game TEXT,
                    steam_link TEXT,
                    faceit_link TEXT,
                    dotabuff_link TEXT,
                    country TEXT,
                    positions TEXT,
                    goals TEXT,
                    about_text TEXT,
                    rating_screenshot TEXT,
                    avg_rating REAL DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, game)
                )
            ''')

            # Таблица лайков
            await db.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    like_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    game TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id, game)
                )
            ''')

            # Таблица мэтчей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    game TEXT,
                    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id, game)
                )
            ''')

            # Таблица отзывов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    game TEXT,
                    rating INTEGER,
                    comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id, game)
                )
            ''')

            # Таблица жалоб
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    reported_user_id INTEGER,
                    game TEXT,
                    reason TEXT,
                    comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица просмотренных анкет
            await db.execute('''
                CREATE TABLE IF NOT EXISTS viewed_profiles (
                    view_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    viewer_id INTEGER,
                    viewed_id INTEGER,
                    game TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(viewer_id, viewed_id, game)
                )
            ''')

            await db.commit()

    async def add_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            await db.commit()

    async def create_or_update_profile(self, user_id: int, game: str, data: Dict[str, Any]):
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем существование профиля
            cursor = await db.execute(
                'SELECT profile_id FROM profiles WHERE user_id = ? AND game = ?',
                (user_id, game)
            )
            existing = await cursor.fetchone()

            if existing:
                # Обновляем существующий профиль
                await db.execute('''
                    UPDATE profiles SET
                        steam_link = ?,
                        faceit_link = ?,
                        dotabuff_link = ?,
                        country = ?,
                        positions = ?,
                        goals = ?,
                        about_text = ?,
                        rating_screenshot = ?
                    WHERE user_id = ? AND game = ?
                ''', (
                    data.get('steam_link'),
                    data.get('faceit_link'),
                    data.get('dotabuff_link'),
                    data.get('country'),
                    json.dumps(data.get('positions', [])),
                    json.dumps(data.get('goals', [])),
                    data.get('about_text'),
                    data.get('rating_screenshot'),
                    user_id,
                    game
                ))
            else:
                # Создаем новый профиль
                await db.execute('''
                    INSERT INTO profiles (
                        user_id, game, steam_link, faceit_link, 
                        dotabuff_link, country, positions, goals, 
                        about_text, rating_screenshot
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    game,
                    data.get('steam_link'),
                    data.get('faceit_link'),
                    data.get('dotabuff_link'),
                    data.get('country'),
                    json.dumps(data.get('positions', [])),
                    json.dumps(data.get('goals', [])),
                    data.get('about_text'),
                    data.get('rating_screenshot')
                ))

            await db.commit()

    async def get_profile(self, user_id: int, game: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT p.*, u.username 
                FROM profiles p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.user_id = ? AND p.game = ? AND p.is_active = 1
            ''', (user_id, game))
            row = await cursor.fetchone()

            if row:
                profile = dict(row)
                profile['positions'] = json.loads(profile['positions']) if profile['positions'] else []
                profile['goals'] = json.loads(profile['goals']) if profile['goals'] else []
                return profile
            return None

    async def get_next_profile(self, viewer_id: int, game: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Получаем непросмотренные профили
            cursor = await db.execute('''
                SELECT p.*, u.username
                FROM profiles p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.game = ? 
                AND p.user_id != ?
                AND p.is_active = 1
                AND p.user_id NOT IN (
                    SELECT viewed_id FROM viewed_profiles 
                    WHERE viewer_id = ? AND game = ?
                )
                ORDER BY RANDOM()
                LIMIT 1
            ''', (game, viewer_id, viewer_id, game))

            row = await cursor.fetchone()
            if row:
                profile = dict(row)
                profile['positions'] = json.loads(profile['positions']) if profile['positions'] else []
                profile['goals'] = json.loads(profile['goals']) if profile['goals'] else []

                # Помечаем как просмотренный
                await db.execute('''
                    INSERT OR IGNORE INTO viewed_profiles (viewer_id, viewed_id, game)
                    VALUES (?, ?, ?)
                ''', (viewer_id, profile['user_id'], game))
                await db.commit()

                return profile
            return None

    async def add_like(self, from_user_id: int, to_user_id: int, game: str) -> bool:
        """Добавляет лайк и возвращает True если это мэтч"""
        async with aiosqlite.connect(self.db_path) as db:
            # Добавляем лайк
            await db.execute('''
                INSERT OR IGNORE INTO likes (from_user_id, to_user_id, game)
                VALUES (?, ?, ?)
            ''', (from_user_id, to_user_id, game))

            # Проверяем взаимный лайк
            cursor = await db.execute('''
                SELECT * FROM likes 
                WHERE from_user_id = ? AND to_user_id = ? AND game = ?
            ''', (to_user_id, from_user_id, game))

            mutual_like = await cursor.fetchone()

            if mutual_like:
                # Создаем мэтч
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)

                await db.execute('''
                    INSERT OR IGNORE INTO matches (user1_id, user2_id, game)
                    VALUES (?, ?, ?)
                ''', (user1_id, user2_id, game))

                await db.commit()
                return True

            await db.commit()
            return False

    async def get_matches(self, user_id: int, game: str) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute('''
                SELECT 
                    CASE 
                        WHEN m.user1_id = ? THEN m.user2_id
                        ELSE m.user1_id
                    END as matched_user_id,
                    m.match_date,
                    u.username,
                    p.*
                FROM matches m
                JOIN users u ON u.user_id = 
                    CASE 
                        WHEN m.user1_id = ? THEN m.user2_id
                        ELSE m.user1_id
                    END
                JOIN profiles p ON p.user_id = u.user_id AND p.game = m.game
                WHERE (m.user1_id = ? OR m.user2_id = ?) AND m.game = ?
                ORDER BY m.match_date DESC
            ''', (user_id, user_id, user_id, user_id, game))

            matches = []
            for row in await cursor.fetchall():
                match = dict(row)
                match['positions'] = json.loads(match['positions']) if match['positions'] else []
                match['goals'] = json.loads(match['goals']) if match['goals'] else []
                matches.append(match)

            return matches

    async def get_incoming_likes(self, user_id: int, game: str) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute('''
                SELECT l.*, u.username, p.*
                FROM likes l
                JOIN users u ON u.user_id = l.from_user_id
                JOIN profiles p ON p.user_id = l.from_user_id AND p.game = l.game
                WHERE l.to_user_id = ? AND l.game = ?
                AND NOT EXISTS (
                    SELECT 1 FROM likes 
                    WHERE from_user_id = ? AND to_user_id = l.from_user_id AND game = ?
                )
                ORDER BY l.timestamp DESC
            ''', (user_id, game, user_id, game))

            likes = []
            for row in await cursor.fetchall():
                like = dict(row)
                like['positions'] = json.loads(like['positions']) if like['positions'] else []
                like['goals'] = json.loads(like['goals']) if like['goals'] else []
                likes.append(like)

            return likes

    async def add_review(self, from_user_id: int, to_user_id: int, game: str, rating: int, comment: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            # Добавляем отзыв
            await db.execute('''
                INSERT OR REPLACE INTO reviews (from_user_id, to_user_id, game, rating, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (from_user_id, to_user_id, game, rating, comment))

            # Обновляем средний рейтинг
            cursor = await db.execute('''
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM reviews
                WHERE to_user_id = ? AND game = ?
            ''', (to_user_id, game))

            result = await cursor.fetchone()
            avg_rating = result[0] if result[0] else 0
            review_count = result[1] if result[1] else 0

            await db.execute('''
                UPDATE profiles 
                SET avg_rating = ?, review_count = ?
                WHERE user_id = ? AND game = ?
            ''', (avg_rating, review_count, to_user_id, game))

            await db.commit()

    async def add_report(self, from_user_id: int, reported_user_id: int, game: str, reason: str, comment: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO reports (from_user_id, reported_user_id, game, reason, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (from_user_id, reported_user_id, game, reason, comment))
            await db.commit()

    async def reset_viewed_profiles(self, user_id: int, game: str):
        """Сбрасывает просмотренные анкеты для повторного просмотра"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'DELETE FROM viewed_profiles WHERE viewer_id = ? AND game = ?',
                (user_id, game)
            )
            await db.commit()

    async def get_user_games(self, user_id: int) -> List[str]:
        """Получает список игр, для которых у пользователя есть профили"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT game FROM profiles WHERE user_id = ? AND is_active = 1',
                (user_id,)
            )
            games = [row[0] for row in await cursor.fetchall()]
            return games