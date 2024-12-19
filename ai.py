# ai.py

import math
from game import Move

def find_best_move(game, depth):
    """
    Найти лучший ход для текущей позиции с заданной глубиной поиска.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина поиска в дереве ходов.
    :return: Лучший ход.
    """
    best_move = None
    if game.white_to_move:
        best_value = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)
            game.undo_move()
            if move_value > best_value:
                best_value = move_value
                best_move = move
    else:
        best_value = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)
            game.undo_move()
            if move_value < best_value:
                best_value = move_value
                best_move = move
    return best_move

def minimax(game, depth, alpha, beta, is_maximizing):
    """
    Минимаксный алгоритм с枝еножением (alpha-beta pruning) для оценки ходов.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :param depth: Глубина рекурсии.
    :param alpha: Параметр alpha для枝еножения.
    :param beta: Параметр beta для枝еножения.
    :param is_maximizing: Флаг, указывающий, является ли текущий уровень maximize или minimize.
    :return: Оценка позиции.
    """
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
            if beta <= alpha:
                break
        return min_eval

def evaluate_game(game):
    """
    Оценить текущую позицию на доске.
    
    :param game: Объект игры, содержащий текущее состояние доски.
    :return: Оценка позиции (разница в стоимости фигур).
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
