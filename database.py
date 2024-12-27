# database.py

import sqlite3
import os
from datetime import datetime
import json

DATABASE_FILE = 'chess.db'  # Имя файла базы данных

def get_connection():
    """
    Устанавливает соединение с базой данных.
    
    :return: Объект соединения с базой данных.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def initialize_db():
    """
    Инициализирует базу данных, создавая необходимые таблицы, если они не существуют.
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

def save_user(username, password_hash):
    """
    Сохраняет нового пользователя в базе данных.
    
    :param username: Имя пользователя.
    :param password_hash: Хеш пароля пользователя.
    :return: Кортеж (успех, сообщение).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return True, 'Пользователь успешно зарегистрирован.'
    except sqlite3.IntegrityError:  # Обработка ошибки дублирования пользователя
        return False, 'Пользователь уже существует.'
    finally:
        conn.close()

def get_user(username):
    """
    Получает информацию о пользователе из базы данных.
    
    :param username: Имя пользователя.
    :return: Кортеж с данными пользователя или None, если пользователь не найден.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_new_game(white_player, black_player):
    """
    Создает новую игру в базе данных.
    
    :param white_player: Имя игрока за белых.
    :param black_player: Имя игрока за черных.
    :return: ID созданной игры.
    """
    conn = get_connection()
    cursor = conn.cursor()
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Время начала игры
    moves_json = json.dumps([])  # Инициализация пустого списка ходов
    cursor.execute('''
        INSERT INTO games (white_player, black_player, moves, result, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (white_player, black_player, moves_json, None, start_time, None, 'in_progress'))
    game_id = cursor.lastrowid  # Получение ID созданной игры
    conn.commit()
    conn.close()
    return game_id

def update_game(game_id, moves, result=None, end_time=None, status='in_progress'):
    """
    Обновляет информацию о игре в базе данных.
    
    :param game_id: ID игры.
    :param moves: Список ходов в формате JSON.
    :param result: Результат игры.
    :param end_time: Время окончания игры.
    :param status: Статус игры ('in_progress' или 'completed').
    """
    conn = get_connection()
    cursor = conn.cursor()
    moves_json = json.dumps(moves)  # Сериализация ходов в JSON
    cursor.execute('''
        UPDATE games
        SET moves = ?, result = ?, end_time = ?, status = ?
        WHERE game_id = ?
    ''', (moves_json, result, end_time, status, game_id))
    conn.commit()
    conn.close()

def get_games_by_user(username, status=None):
    """
    Получает список игр для указанного пользователя.
    
    :param username: Имя пользователя.
    :param status: Статус игры ('in_progress' или 'completed').
    :return: Список игр.
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

def get_game_by_id(game_id):
    """
    Получает информацию о игре по её ID.
    
    :param game_id: ID игры.
    :return: Кортеж с данными игры или None, если игра не найдена.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id,))
    game = cursor.fetchone()
    conn.close()
    return game
