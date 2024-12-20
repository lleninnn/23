# ai.py

import math
from game import Move

# Функция для поиска лучшего хода для текущей игры
def find_best_move(game, depth):
    """
    Функция ищет лучший ход для текущей игры с использованием алгоритма минимакс с альфа-бета отсечениями.
    :param game: Экземпляр класса Game, представляющий текущую игру.
    :param depth: Глубина поиска в дереве ходов.
    :return: Лучший ход для текущей игры.
    """
    best_move = None
    if game.white_to_move:
        # Если ход белых, ищем максимальное значение
        best_value = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)
            game.undo_move()
            if move_value > best_value:
                best_value = move_value
                best_move = move
    else:
        # Если ход чёрных, ищем минимальное значение
        best_value = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)
            game.undo_move()
            if move_value < best_value:
                best_value = move_value
                best_move = move
    return best_move

# Алгоритм минимакс с альфа-бета отсечениями
def minimax(game, depth, alpha, beta, is_maximizing):
    """
    Алгоритм минимакс с альфа-бета отсечениями для оценки лучшего хода.
    :param game: Экземпляр класса Game, представляющий текущую игру.
    :param depth: Глубина поиска в дереве ходов.
    :param alpha: Лучшая (максимальная) оценка для максимизирующего игрока.
    :param beta: Лучшая (минимальная) оценка для минимизирующего игрока.
    :param is_maximizing: True, если текущий игрок максимизирует оценку, иначе False.
    :return: Оценка текущего состояния игры.
    """
    # Если достигнута максимальная глубина или игра завершена, возвращаем оценку
    if depth == 0 or game.checkmate or game.stalemate:
        return evaluate_game(game)

    if is_maximizing:
        max_eval = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, False)
            game.undo_move()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            # Если beta меньше или равно alpha, отсекаем ветвь
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, True)
            game.undo_move()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            # Если beta меньше или равно alpha, отсекаем ветвь
            if beta <= alpha:
                break
        return min_eval

# Функция для оценки текущего состояния игры
def evaluate_game(game):
    """
    Оценивает текущее состояние игры на основе разницы в количестве фигур.
    :param game: Экземпляр класса Game, представляющий текущую игру.
    :return: Оценка текущего состояния игры.
    """
    # Простая оценка: разница в количестве фигур
    piece_values = {'K': 1000, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    white_score = 0
    black_score = 0
    for row in game.board:
        for piece in row:
            if piece != '--':
                value = piece_values.get(piece[1], 0)
                if piece[0] == 'w':
                    white_score += value
                else:
                    black_score += value
    return white_score - black_score
