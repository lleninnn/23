# database.py

import sqlite3
import os
from datetime import datetime
import json

DATABASE_FILE = 'chess.db'

# Функция для получения соединения с базой данных
def get_connection():
    """
    Возвращает соединение с базой данных.
    :return: Объект соединения с базой данных.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

# Функция для инициализации базы данных
def initialize_db():
    """
    Инициализирует базу данных, создавая таблицы пользователей и игр, если они ещё не существуют.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Создание таблицы пользователей (если еще не существует)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создание таблицы партий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            white_player TEXT NOT NULL,
            black_player TEXT NOT NULL,
            moves TEXT NOT NULL,  -- Сохранение ходов в формате JSON
            result TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT NOT NULL,  -- 'in_progress' или 'completed'
            FOREIGN KEY (white_player) REFERENCES users(username),
            FOREIGN KEY (black_player) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()

# Функция для сохранения пользователя в базе данных
def save_user(username, password_hash):
    """
    Сохраняет нового пользователя в базе данных.
    :param username: Имя пользователя.
    :param password_hash: Хеш пароля пользователя.
    :return: Кортеж (успех, сообщение), где успех - True, если сохранение прошло успешно, иначе False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return True, 'Пользователь успешно зарегистрирован.'
    except sqlite3.IntegrityError:
        return False, 'Пользователь уже существует.'
    finally:
        conn.close()

# Функция для получения пользователя из базы данных
def get_user(username):
    """
    Получает пользователя из базы данных по имени пользователя.
    :param username: Имя пользователя.
    :return: Кортеж с данными пользователя или None, если пользователь не найден.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Функция для создания новой игры
def create_new_game(white_player, black_player):
    """
    Создаёт новую игру в базе данных.
    :param white_player: Имя пользователя, играющего за белых.
    :param black_player: Имя пользователя, играющего за чёрных.
    :return: ID новой игры.
    """
    conn = get_connection()
    cursor = conn.cursor()
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    moves_json = json.dumps([])
    cursor.execute('''
        INSERT INTO games (white_player, black_player, moves, result, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (white_player, black_player, moves_json, None, start_time, None, 'in_progress'))
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id

# Функция для обновления игры в базе данных
def update_game(game_id, moves, result=None, end_time=None, status='in_progress'):
    """
    Обновляет информацию о игре в базе данных.
    :param game_id: ID игры.
    :param moves: Список ходов в формате JSON.
    :param result: Результат игры (например, 'White wins', 'Black wins', 'Draw').
    :param end_time: Время окончания игры.
    :param status: Статус игры ('in_progress' или 'completed').
    """
    conn = get_connection()
    cursor = conn.cursor()
    moves_json = json.dumps(moves)
    cursor.execute('''
        UPDATE games
        SET moves = ?, result = ?, end_time = ?, status = ?
        WHERE game_id = ?
    ''', (moves_json, result, end_time, status, game_id))
    conn.commit()
    conn.close()

# Функция для получения списка игр пользователя
def get_games_by_user(username, status=None):
    """
    Получает список игр пользователя по его имени.
    :param username: Имя пользователя.
    :param status: Статус игры ('in_progress' или 'completed'). Если None, возвращает все игры.
    :return: Список игр пользователя.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute('''
            SELECT * FROM games 
            WHERE (white_player = ? OR black_player = ?) AND status = ?
            ORDER BY start_time DESC
        ''', (username, username, status))
    else:
        cursor.execute('''
            SELECT * FROM games 
            WHERE white_player = ? OR black_player = ?
            ORDER BY start_time DESC
        ''', (username, username))
    games = cursor.fetchall()
    conn.close()
    return games

# Функция для получения игры по её ID
def get_game_by_id(game_id):
    """
    Получает игру по её ID.
    :param game_id: ID игры.
    :return: Кортеж с данными игры или None, если игра не найдена.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id,))
    game = cursor.fetchone()
    conn.close()
    return game
