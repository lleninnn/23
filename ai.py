# ai.py

import math
import random
from game import Move

def find_best_move(game, depth):
    """
    Находит лучший ход для текущего игрока (человека или ИИ) с использованием алгоритма минимакс.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина поиска для алгоритма минимакс.
    :return: Лучший ход (объект Move) или None, если ходов нет.
    """
    best_move = None
    if game.white_to_move:
        best_value = -math.inf  # Инициализация для максимизации (ход белых)
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)  # Рекурсивный вызов минимакс
            game.undo_move()
            if move_value > best_value:
                best_value = move_value
                best_move = move
    else:
        best_value = math.inf  # Инициализация для минимизации (ход черных)
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)  # Рекурсивный вызов минимакс
            game.undo_move()
            if move_value < best_value:
                best_value = move_value
                best_move = move
    print(f"AI выбрал ход: {best_move.get_chess_notation() if best_move else 'Нет доступных ходов'}")
    return best_move

def minimax(game, depth, alpha, beta, is_maximizing):
    """
    Реализация алгоритма минимакс с альфа-бета отсечением для поиска лучшего хода.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина поиска.
    :param alpha: Лучшее значение для максимизирующего игрока.
    :param beta: Лучшее значение для минимизирующего игрока.
    :param is_maximizing: Флаг, указывающий, максимизирует ли текущий игрок оценку.
    :return: Оценка позиции.
    """
    if depth == 0 or game.checkmate or game.stalemate:
        return evaluate_game(game)  # Оценка позиции, если достигнута глубина 0 или игра завершена

    if is_maximizing:
        max_eval = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, False)  # Рекурсивный вызов для минимизации
            game.undo_move()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:  # Альфа-бета отсечение
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, True)  # Рекурсивный вызов для максимизации
            game.undo_move()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:  # Альфа-бета отсечение
                break
        return min_eval

def evaluate_game(game):
    """
    Оценивает текущую позицию на доске, учитывая материал и случайный фактор для разнообразия ходов.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :return: Оценка позиции.
    """
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}  # Значения фигур
    white_score = 0
    black_score = 0

    for row in game.board:
        for piece in row:
            if piece != '--':
                value = piece_values.get(piece[1], 0)  # Используем реальные значения фигур
                if piece[0] == 'w':
                    white_score += value
                else:
                    black_score += value

    # Добавление случайного фактора для разнообразия ходов
    random_factor = random.uniform(-0.5, 0.5)
    evaluation = (white_score - black_score) + random_factor
    print(f"Оценка позиции: {evaluation} (Белые: {white_score}, Черные: {black_score})")
    return evaluation
