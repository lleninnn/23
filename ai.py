# ai.py

import math
import random
from game import Move

def find_best_move(game, depth):
    """
    Находит лучший ход для текущего игрока с использованием алгоритма минимакс.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина поиска в дереве ходов.
    :return: Лучший ход (объект Move) или None, если ходов нет.
    """
    best_move = None
    if game.white_to_move:
        best_value = -math.inf  # Инициализация лучшего значения для белых
        for move in game.get_valid_moves():  # Перебор всех возможных ходов
            game.make_move(move, update_state=False)  # Временное выполнение хода
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)  # Оценка хода
            game.undo_move()  # Отмена хода
            if move_value > best_value:  # Обновление лучшего хода
                best_value = move_value
                best_move = move
    else:
        best_value = math.inf  # Инициализация лучшего значения для черных
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)  # Оценка хода
            game.undo_move()
            if move_value < best_value:  # Обновление лучшего хода
                best_value = move_value
                best_move = move
    print(f"AI выбрал ход: {best_move.get_chess_notation() if best_move else 'Нет доступных ходов'}")
    return best_move

def minimax(game, depth, alpha, beta, is_maximizing):
    """
    Реализует алгоритм минимакс с альфа-бета отсечением для оценки ходов.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина поиска в дереве ходов.
    :param alpha: Лучшее значение для максимизирующего игрока.
    :param beta: Лучшее значение для минимизирующего игрока.
    :param is_maximizing: Флаг, указывающий, максимизирует ли текущий игрок оценку.
    :return: Оценка текущего состояния игры.
    """
    if depth == 0 or game.checkmate or game.stalemate:  # Условие выхода из рекурсии
        return evaluate_game(game)  # Оценка текущей позиции

    if is_maximizing:
        max_eval = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, False)  # Рекурсивный вызов для минимизации
            game.undo_move()
            max_eval = max(max_eval, eval)  # Обновление максимального значения
            alpha = max(alpha, eval)  # Обновление альфа
            if beta <= alpha:  # Отсечение
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, True)  # Рекурсивный вызов для максимизации
            game.undo_move()
            min_eval = min(min_eval, eval)  # Обновление минимального значения
            beta = min(beta, eval)  # Обновление бета
            if beta <= alpha:  # Отсечение
                break
        return min_eval

def evaluate_game(game):
    """
    Оценивает текущее состояние игры на основе материального баланса и случайного фактора.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :return: Оценка текущей позиции.
    """
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}  # Веса фигур
    white_score = 0
    black_score = 0

    for row in game.board:
        for piece in row:
            if piece != '--':
                value = piece_values.get(piece[1], 0)  # Используем реальные значения
                if piece[0] == 'w':  # Подсчет очков для белых
                    white_score += value
                else:  # Подсчет очков для черных
                    black_score += value

    # Добавление случайного фактора для разнообразия ходов
    random_factor = random.uniform(-0.5, 0.5)
    evaluation = (white_score - black_score) + random_factor
    print(f"Оценка позиции: {evaluation} (Белые: {white_score}, Черные: {black_score})")
    return evaluation
