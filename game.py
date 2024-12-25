# game.py

import pygame
import settings  # Исправлено: импортируем как модуль
from settings import *
from copy import deepcopy
from datetime import datetime
from database import update_game, get_game_by_id
import json  # Добавлен импорт json

# Класс, представляющий ход в игре
class Move:
    def __init__(self, start_pos, end_pos, piece_moved, piece_captured, is_pawn_promotion=False, promotion_choice='Q'):
        """
        Инициализирует объект хода.
        :param start_pos: Начальная позиция хода (строка, столбец).
        :param end_pos: Конечная позиция хода (строка, столбец).
        :param piece_moved: Фигура, которая была передвинута.
        :param piece_captured: Фигура, которая была взята (если есть).
        :param is_pawn_promotion: True, если это ход пешки на последнюю линию и она превращается.
        :param promotion_choice: Выбранная фигура для превращения пешки (по умолчанию 'Q' - ферзь).
        """
        self.start_row, self.start_col = start_pos
        self.end_row, self.end_col = end_pos
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        self.is_pawn_promotion = is_pawn_promotion
        self.promotion_choice = promotion_choice

    def __eq__(self, other):
        """
        Проверяет, равны ли два объекта Move.
        :param other: Другой объект Move.
        :return: True, если объекты равны, иначе False.
        """
        if isinstance(other, Move):
            return (self.start_row == other.start_row and
                    self.start_col == other.start_col and
                    self.end_row == other.end_row and
                    self.end_col == other.end_col and
                    self.piece_moved == other.piece_moved and
                    self.piece_captured == other.piece_captured and
                    self.is_pawn_promotion == other.is_pawn_promotion and
                    self.promotion_choice == other.promotion_choice)
        return False

    def get_chess_notation(self):
        """
        Возвращает шахматную нотацию хода.
        :return: Строка с шахматной нотацией хода.
        """
        cols_to_files = {0: 'a', 1: 'b', 2: 'c', 3: 'd',
                        4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        return cols_to_files[self.start_col] + str(8 - self.start_row) + \
               cols_to_files[self.end_col] + str(8 - self.end_row)

    def to_dict(self):
        """
        Преобразует объект Move в словарь.
        :return: Словарь с данными хода.
        """
        return {
            'start_pos': [self.start_row, self.start_col],
            'end_pos': [self.end_row, self.end_col],
            'piece_moved': self.piece_moved,
            'piece_captured': self.piece_captured,
            'is_pawn_promotion': self.is_pawn_promotion,
            'promotion_choice': self.promotion_choice
        }

    @classmethod
    def from_dict(cls, move_dict):
        """
        Создаёт объект Move из словаря.
        :param move_dict: Словарь с данными хода.
        :return: Объект Move.
        """
        return cls(
            start_pos=tuple(move_dict['start_pos']),
            end_pos=tuple(move_dict['end_pos']),
            piece_moved=move_dict['piece_moved'],
            piece_captured=move_dict['piece_captured'],
            is_pawn_promotion=move_dict['is_pawn_promotion'],
            promotion_choice=move_dict.get('promotion_choice', 'Q')
        )

# Класс, представляющий игру
class Game:
    def __init__(self, white_player='White', black_player='AI', game_id=None):
        """
        Инициализирует объект игры.
        :param white_player: Имя пользователя, играющего за белых.
        :param black_player: Имя пользователя, играющего за чёрных.
        :param game_id: ID игры (если игра загружается из базы данных).
        """
        self.white_player = white_player
        self.black_player = black_player
        self.game_id = game_id
        if game_id:
            self.load_game(game_id)
        else:
            self.board = self.create_initial_board()
            self.white_to_move = True
            self.move_log = []
            self.selected_square = None
            self.valid_moves = []
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()
            self.promotion_choice = 'Q'
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None

    def create_initial_board(self):
        """
        Создаёт начальную доску для игры.
        :return: Двумерный список, представляющий доску.
        """
        board = [['--' for _ in range(8)] for _ in range(8)]
        board[7][4] = 'wK'  # Белый король на e1
        board[6][0] = 'wP'  # Белая пешка на a2
        board[0][4] = 'bK'  # Чёрный король на e8
        board[1][7] = 'bP'  # Чёрная пешка на h7
        return board

    def load_game(self, game_id):
        """
        Загружает игру из базы данных по её ID.
        :param game_id: ID игры.
        """
        game = get_game_by_id(game_id)
        if game:
            _, white_player, black_player, moves, result, start_time, end_time, status = game
            self.white_player = white_player
            self.black_player = black_player
            self.move_log = [Move.from_dict(move_dict) for move_dict in json.loads(moves)]
            self.reconstruct_board()
            self.result = result
            self.start_time = start_time
            self.end_time = end_time
            self.checkmate = status == 'completed' and ('checkmate' in (result.lower()) if result else False)
            self.stalemate = status == 'completed' and ('stalemate' in (result.lower()) if result else False)
            self.white_to_move = len(self.move_log) % 2 == 0
        else:
            print(f"Игра с ID {game_id} не найдена.")
            self.board = self.create_initial_board()
            self.white_to_move = True
            self.move_log = []
            self.selected_square = None
            self.valid_moves = []
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()
            self.promotion_choice = 'Q'
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None

    def reconstruct_board(self):
        """
        Восстанавливает доску на основе списка ходов.
        """
        self.board = self.create_initial_board()
        for move in self.move_log:
            self.board[move.start_row][move.start_col] = '--'
            self.board[move.end_row][move.end_col] = move.piece_moved
            if move.is_pawn_promotion:
                self.board[move.end_row][move.end_col] = move.piece_moved[0] + move.promotion_choice

    def make_move(self, move, update_state=True):
        """
        Выполняет ход на доске.
        :param move: Объект Move, представляющий ход.
        :param update_state: True, если нужно обновлять состояние игры (например, проверять шах и мат).
        """
        self.board[move.start_row][move.start_col] = '--'
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + move.promotion_choice
        if update_state:
            self.check_game_state()
            self.save_current_game()

    def undo_move(self):
        """
        Отменяет последний ход.
        """
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            self.check_game_state()
            self.save_current_game()

    def get_valid_moves(self):
        """
        Возвращает список допустимых ходов для текущего игрока.
        :return: Список объектов Move.
        """
        moves = self.get_all_possible_moves()
        valid_moves = []
        for move in moves:
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move):
                valid_moves.append(move)
        return valid_moves

    def get_all_possible_moves(self):
        """
        Возвращает список всех возможных ходов для текущего игрока.
        :return: Список объектов Move.
        """
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == '--':
                    continue
                if self.white_to_move and piece[0] != 'w':
                    continue
                if not self.white_to_move and piece[0] != 'b':
                    continue
                piece_type = piece[1]
                if piece_type == 'K':
                    self.get_king_moves(r, c, moves)
                elif piece_type == 'P':
                    self.get_pawn_moves(r, c, moves)
                elif piece_type == 'Q':
                    self.get_queen_moves(r, c, moves)
                elif piece_type == 'R':
                    self.get_rook_moves(r, c, moves)
                elif piece_type == 'B':
                    self.get_bishop_moves(r, c, moves)
                elif piece_type == 'N':
                    self.get_knight_moves(r, c, moves)
        return moves

    def get_king_moves(self, r, c, moves):
        """
        Добавляет возможные ходы короля в список ходов.
        :param r: Строка, где находится король.
        :param c: Столбец, где находится король.
        :param moves: Список ходов.
        """
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        enemy_color = 'b' if self.white_to_move else 'w'

        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--' or target[0] != ally_color:
                    # Проверяем, что клетка не находится под ударом пешки противника
                    if not self.is_square_attacked_by_pawn((end_row, end_col), enemy_color):
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def get_pawn_moves(self, r, c, moves):
        """
        Добавляет возможные ходы пешки в список ходов.
        :param r: Строка, где находится пешка.
        :param c: Столбец, где находится пешка.
        :param moves: Список ходов.
        """
        direction = -1 if self.white_to_move else 1
        start_row = 6 if self.white_to_move else 1
        enemy_color = 'b' if self.white_to_move else 'w'

        # Пешка движется вперёд на 1 клетку
        if self.board[r + direction][c] == '--':
            moves.append(Move((r, c), (r + direction, c), self.board[r][c], '--'))
            # Пешка может пойти на 2 клетки из начальной позиции
            if r == start_row and self.board[r + 2 * direction][c] == '--':
                moves.append(Move((r, c), (r + 2 * direction, c), self.board[r][c], '--'))

        # Пешка бьёт по диагонали, но **НЕ** атакует короля
        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                piece_at_target = self.board[r + direction][c + dc]
                if piece_at_target != '--' and piece_at_target[0] == enemy_color and piece_at_target[1] != 'K':  # НЕ бьёт короля
                    moves.append(Move((r, c), (r + direction, c + dc), self.board[r][c], piece_at_target))

    def get_queen_moves(self, r, c, moves):
        """
        Добавляет возможные ходы ферзя в список ходов.
        :param r: Строка, где находится ферзь.
        :param c: Столбец, где находится ферзь.
        :param moves: Список ходов.
        """
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_rook_moves(self, r, c, moves):
        """
        Добавляет возможные ходы ладьи в список ходов.
        :param r: Строка, где находится ладья.
        :param c: Столбец, где находится ладья.
        :param moves: Список ходов.
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            while 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--':
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                else:
                    if target[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                    break
                end_row += dr
                end_col += dc

    def get_bishop_moves(self, r, c, moves):
        """
        Добавляет возможные ходы слона в список ходов.
        :param r: Строка, где находится слон.
        :param c: Столбец, где находится слон.
        :param moves: Список ходов.
        """
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            while 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--':
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                else:
                    if target[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                    break
                end_row += dr
                end_col += dc

    def get_knight_moves(self, r, c, moves):
        """
        Добавляет возможные ходы коня в список ходов.
        :param r: Строка, где находится конь.
        :param c: Столбец, где находится конь.
        :param moves: Список ходов.
        """
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                       (1, -2), (2, -1), (1, 2), (2, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in knight_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--' or target[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def in_check(self, white):
        """
        Проверяет, находится ли король под шахом.
        :param white: True, если проверяем для белых, иначе False.
        :return: True, если король под шахом, иначе False.
        """
        king_pos = None
        ally_color = 'w' if white else 'b'
        enemy_color = 'b' if white else 'w'

        # Находим позицию короля
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == '--':
                    continue
                if piece[0] == ally_color and piece[1] == 'K':
                    king_pos = (r, c)
                    break
            if king_pos:
                break

        if not king_pos:
            return False

        # Проверяем, атакуют ли короля пешки противника
        if self.is_square_attacked_by_pawn(king_pos, enemy_color):
            return True

        # Проверяем атаки других фигур
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == '--' or piece[0] != enemy_color:
                    continue
                piece_type = piece[1]
                if piece_type == 'K':
                    if max(abs(king_pos[0] - r), abs(king_pos[1] - c)) == 1:
                        return True
                elif piece_type == 'N':
                    if self.is_square_attacked_by_knight(king_pos, (r, c)):
                        return True
                elif piece_type == 'B':
                    if self.is_square_attacked_by_bishop(king_pos, (r, c)):
                        return True
                elif piece_type == 'R':
                    if self.is_square_attacked_by_rook(king_pos, (r, c)):
                        return True
                elif piece_type == 'Q':
                    if self.is_square_attacked_by_queen(king_pos, (r, c)):
                        return True
        return False

    def is_square_attacked_by_pawn(self, square, enemy_color):
        """
        Проверяет, атакует ли пешка противника данную клетку.
        :param square: Позиция клетки (строка, столбец).
        :param enemy_color: Цвет пешки противника ('w' или 'b').
        :return: True, если пешка атакует клетку, иначе False.
        """
        r, c = square
        direction = 1 if enemy_color == 'w' else -1  # Направление атаки пешки
        for dc in [-1, 1]:  # Пешка атакует по диагонали
            if 0 <= r + direction < 8 and 0 <= c + dc < 8:
                piece = self.board[r + direction][c + dc]
                if piece == enemy_color + 'P':
                    return True
        return False

    def is_square_attacked_by_knight(self, king_pos, attacker_pos):
        """
        Проверяет, атакует ли конь данную клетку.
        :param king_pos: Позиция клетки, которую проверяем.
        :param attacker_pos: Позиция коня.
        :return: True, если конь атакует клетку, иначе False.
        """
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                       (1, -2), (2, -1), (1, 2), (2, 1)]
        r, c = attacker_pos
        king_r, king_c = king_pos
        for dr, dc in knight_moves:
            if (r + dr, c + dc) == king_pos:
                return True
        return False

    def is_square_attacked_by_bishop(self, king_pos, attacker_pos):
        """
        Проверяет, атакует ли слон данную клетку.
        :param king_pos: Позиция клетки, которую проверяем.
        :param attacker_pos: Позиция слона.
        :return: True, если слон атакует клетку, иначе False.
        """
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self.is_square_attacked_along_directions(king_pos, attacker_pos, directions)

    def is_square_attacked_by_rook(self, king_pos, attacker_pos):
        """
        Проверяет, атакует ли ладья данную клетку.
        :param king_pos: Позиция клетки, которую проверяем.
        :param attacker_pos: Позиция ладьи.
        :return: True, если ладья атакует клетку, иначе False.
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self.is_square_attacked_along_directions(king_pos, attacker_pos, directions)

    def is_square_attacked_by_queen(self, king_pos, attacker_pos):
        """
        Проверяет, атакует ли ферзь данную клетку.
        :param king_pos: Позиция клетки, которую проверяем.
        :param attacker_pos: Позиция ферзя.
        :return: True, если ферзь атакует клетку, иначе False.
        """
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        return self.is_square_attacked_along_directions(king_pos, attacker_pos, directions)

    def is_square_attacked_along_directions(self, king_pos, attacker_pos, directions):
        """
        Проверяет, атакует ли фигура данную клетку вдоль заданных направлений.
        :param king_pos: Позиция клетки, которую проверяем.
        :param attacker_pos: Позиция фигуры.
        :param directions: Список направлений.
        :return: True, если фигура атакует клетку, иначе False.
        """
        r, c = attacker_pos
        king_r, king_c = king_pos
        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            while 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if (end_row, end_col) == king_pos:
                    return True
                if target != '--':
                    break
                end_row += dr
                end_col += dc
        return False

    def check_game_state(self):
        # Проверка на шах и мат
        if self.in_check(self.white_to_move):
            if not self.get_valid_moves():
                self.checkmate = True
                self.stalemate = False
                self.result = 'Black wins by checkmate' if self.white_to_move else 'White wins by checkmate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.checkmate = False
                self.stalemate = False
        else:
            # Проверка на пат
            if not self.get_valid_moves():
                self.stalemate = True
                self.checkmate = False
                self.result = 'Draw by stalemate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                # Проверка, остались ли на доске только короли
                only_kings_left = True
                for row in self.board:
                    for piece in row:
                        if piece != '--' and piece[1] != 'K':  # Если есть фигура, которая не король
                            only_kings_left = False
                            break
                    if not only_kings_left:
                        break

                if only_kings_left:
                    self.stalemate = True
                    self.checkmate = False
                    self.result = 'Draw by insufficient material (only kings left)'
                    self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.update_game_status('completed')
                else:
                    self.stalemate = False
                    self.checkmate = False

    def update_game_status(self, status):
        """
        Обновляет статус игры в базе данных.
        :param status: Новый статус игры ('in_progress' или 'completed').
        """
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status=status
            )

    def save_current_game(self):
        """
        Сохраняет текущее состояние игры в базе данных.
        """
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed' if self.result else 'in_progress'
            )

    def save_game_completion(self):
        """
        Сохраняет завершённую игру в базе данных.
        """
        if self.game_id and self.result:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed'
            )
            # Экспорт в PGN
            self.export_pgn()

    def export_pgn(self):
        """
        Экспортирует игру в формат PGN.
        """
        if not self.game_id:
            return
        pgn_content = f"[Event \"Chess Endgame\"]\n"
        pgn_content += f"[Site \"Local\"]\n"
        pgn_content += f"[Date \"{self.start_time.split(' ')[0]}\"]\n"
        pgn_content += f"[Round \"-\"]\n"
        pgn_content += f"[White \"{self.white_player}\"]\n"
        pgn_content += f"[Black \"{self.black_player}\"]\n"
        pgn_content += f"[Result \"{self.result}\"]\n\n"

        move_text = ''
        for i in range(0, len(self.move_log), 2):
            move_number = i//2 + 1
            white_move = self.move_log[i].get_chess_notation()
            black_move = self.move_log[i+1].get_chess_notation() if i+1 < len(self.move_log) else ''
            move_text += f"{move_number}. {white_move} {black_move} "

        move_text += self.result
        pgn_content += move_text

        # Сохранение в файл PGN
        pgn_filename = f"game_{self.start_time.replace(':', '-').replace(' ', '_')}_id_{self.game_id}.pgn"
        with open(pgn_filename, 'w') as f:
            f.write(pgn_content)

    def draw(self, win, images, selected_square=None, valid_moves=None):
        """
        Отрисовывает текущее состояние игры.
        :param win: Объект окна Pygame.
        :param images: Словарь с изображениями фигур.
        :param selected_square: Выбранная клетка (если есть).
        :param valid_moves: Список допустимых ходов для выбранной фигуры.
        """
        self.draw_board(win, selected_square, valid_moves)
        self.draw_pieces(win, images)
        self.draw_game_state(win)

    def draw_board(self, win, selected_square, valid_moves):
        """
        Отрисовывает доску.
        :param win: Объект окна Pygame.
        :param selected_square: Выбранная клетка (если есть).
        :param valid_moves: Список допустимых ходов для выбранной фигуры.
        """
        colors = [WHITE, GRAY]
        for r in range(8):
            for c in range(8):
                color = colors[(r + c) % 2]
                pygame.draw.rect(win, color, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE))
                if selected_square and (r, c) == selected_square:
                    pygame.draw.rect(win, BLUE, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE), 3)
                if valid_moves:
                    for move in valid_moves:
                        if move.end_row == r and move.end_col == c:
                            center = (c * settings.CELL_SIZE + settings.CELL_SIZE//2, r * settings.CELL_SIZE + settings.CELL_SIZE//2)
                            pygame.draw.circle(win, GREEN, center, 10)

    def draw_pieces(self, win, images):
        """
        Отрисовывает фигуры на доске.
        :param win: Объект окна Pygame.
        :param images: Словарь с изображениями фигур.
        """
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--':
                    img = images.get(piece)
                    if img:
                        win.blit(img, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE))
                    else:
                        print(f"Изображение для {piece} не найдено.")

    def draw_game_state(self, win):
        """
        Отрисовывает состояние игры (шах, мат, пат).
        :param win: Объект окна Pygame.
        """
        if self.checkmate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Шах и мат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH//2 - text.get_width()//2, settings.WINDOW_HEIGHT//2 - text.get_height()//2))
        elif self.stalemate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Пат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH//2 - text.get_width()//2, settings.WINDOW_HEIGHT//2 - text.get_height()//2))
        elif self.in_check(self.white_to_move):
            font = pygame.font.SysFont('Arial', 24)
            text = font.render('Шах!', True, RED)
            win.blit(text, (10, 10))

    def is_move_valid(self, move):
        """
        Проверяет, является ли ход допустимым.
        :param move: Объект Move, представляющий ход.
        :return: True, если ход допустим, иначе False.
        """
        return move in self.get_valid_moves()

    def get_piece_moves(self, r, c):
        """
        Возвращает список допустимых ходов для фигуры на заданной позиции.
        :param r: Строка, где находится фигура.
        :param c: Столбец, где находится фигура.
        :return: Список объектов Move.
        """
        piece = self.board[r][c]
        if piece == '--':
            return []
        if self.white_to_move and piece[0] != 'w':
            return []
        if not self.white_to_move and piece[0] != 'b':
            return []
        moves = []
        piece_type = piece[1]
        if piece_type == 'K':
            self.get_king_moves(r, c, moves)
        elif piece_type == 'P':
            self.get_pawn_moves(r, c, moves)
        elif piece_type == 'Q':
            self.get_queen_moves(r, c, moves)
        elif piece_type == 'R':
            self.get_rook_moves(r, c, moves)
        elif piece_type == 'B':
            self.get_bishop_moves(r, c, moves)
        elif piece_type == 'N':
            self.get_knight_moves(r, c, moves)
        valid_moves = []
        for move in moves:
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move):
                valid_moves.append(move)
        return valid_moves
