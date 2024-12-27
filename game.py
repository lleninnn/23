# game.py

import pygame
import settings  # Импортируем как модуль
from settings import *
from copy import deepcopy
from datetime import datetime
from database import update_game, get_game_by_id
import json  # Импортируем json для сериализации ходов

class Move:
    def __init__(self, start_pos, end_pos, piece_moved, piece_captured, is_pawn_promotion=False, promotion_choice='Q'):
        """
        Инициализирует объект хода.
        
        :param start_pos: Начальная позиция (строка, столбец).
        :param end_pos: Конечная позиция (строка, столбец).
        :param piece_moved: Фигура, которая делает ход.
        :param piece_captured: Фигура, которая была взята.
        :param is_pawn_promotion: Флаг превращения пешки.
        :param promotion_choice: Выбор фигуры для превращения.
        """
        self.start_row, self.start_col = start_pos  # Начальная позиция
        self.end_row, self.end_col = end_pos  # Конечная позиция
        self.piece_moved = piece_moved  # Фигура, которая делает ход
        self.piece_captured = piece_captured  # Фигура, которая была взята
        self.is_pawn_promotion = is_pawn_promotion  # Флаг превращения пешки
        self.promotion_choice = promotion_choice  # Выбор фигуры для превращения

    def __eq__(self, other):
        """
        Сравнивает два хода на равенство.
        
        :param other: Другой объект Move.
        :return: True, если ходы равны, иначе False.
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
        Возвращает ход в шахматной нотации.
        
        :return: Строка с шахматной нотацией хода.
        """
        cols_to_files = {0: 'a', 1: 'b', 2: 'c', 3: 'd',
                        4: 'e', 5: 'f', 6: 'g', 7: 'h'}  # Преобразование столбцов в буквы
        return cols_to_files[self.start_col] + str(8 - self.start_row) + \
               cols_to_files[self.end_col] + str(8 - self.end_row)  # Шахматная нотация

    def to_dict(self):
        """
        Преобразует ход в словарь для сериализации.
        
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
        Создает объект Move из словаря.
        
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

class Game:
    def __init__(self, white_player='White', black_player='AI', game_id=None):
        """
        Инициализирует объект игры.
        
        :param white_player: Имя игрока за белых.
        :param black_player: Имя игрока за черных.
        :param game_id: ID игры, если она загружается из базы данных.
        """
        self.white_player = white_player  # Игрок за белых
        self.black_player = black_player  # Игрок за черных
        self.game_id = game_id  # ID игры
        if game_id:
            self.load_game(game_id)  # Загрузка игры, если указан ID
        else:
            self.board = self.create_initial_board()  # Создание начальной доски
            self.white_to_move = True  # Флаг хода белых
            self.move_log = []  # Лог ходов
            self.selected_square = None  # Выбранная клетка
            self.valid_moves = []  # Допустимые ходы
            self.checkmate = False  # Флаг мата
            self.stalemate = False  # Флаг пата
            self.en_passant_possible = ()  # Возможность взятия на проходе
            self.promotion_choice = 'Q'  # Выбор фигуры для превращения
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Время начала игры
            self.end_time = None  # Время окончания игры
            self.result = None  # Результат игры

    def create_initial_board(self):
        """
        Создает начальную доску с фигурами.
        
        :return: Двумерный список, представляющий доску.
        """
        board = [['--' for _ in range(8)] for _ in range(8)]  # Создание пустой доски
        # Расстановка фигур по умолчанию
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
            self.move_log = [Move.from_dict(move_dict) for move_dict in json.loads(moves)]  # Загрузка ходов
            self.reconstruct_board()  # Восстановление доски
            self.result = result
            self.start_time = start_time
            self.end_time = end_time
            self.checkmate = status == 'completed' and ('checkmate' in (result.lower()) if result else False)
            self.stalemate = status == 'completed' and ('stalemate' in (result.lower()) if result else False)
            self.white_to_move = len(self.move_log) % 2 == 0  # Определение, чей ход
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
        Восстанавливает доску на основе лога ходов.
        """
        self.board = self.create_initial_board()
        for move in self.move_log:
            self.board[move.start_row][move.start_col] = '--'
            self.board[move.end_row][move.end_col] = move.piece_moved
            if move.is_pawn_promotion:
                self.board[move.end_row][move.end_col] = move.piece_moved[0] + move.promotion_choice
                print(f"Пешка превращена в {self.board[move.end_row][move.end_col]} на позиции {(move.end_row, move.end_col)}")

    def make_move(self, move, update_state=True):
        """
        Выполняет ход на доске.
        
        :param move: Объект Move, представляющий ход.
        :param update_state: Флаг, указывающий, нужно ли обновлять состояние игры.
        """
        self.board[move.start_row][move.start_col] = '--'
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        if move.is_pawn_promotion:
            # Используйте выбранную фигуру
            promotion_choice = move.promotion_choice if move.promotion_choice else 'Q'
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promotion_choice
            print(f"Пешка превращена в {self.board[move.end_row][move.end_col]} на позиции {(move.end_row, move.end_col)}")
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
        Возвращает все возможные ходы для текущего игрока без учета шаха.
        
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

    def get_pawn_moves(self, r, c, moves):
        """
        Возвращает все возможные ходы для пешки на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
        """
        piece = self.board[r][c]
        direction = -1 if piece[0] == 'w' else 1  # Направление движения пешки
        start_row = 6 if piece[0] == 'w' else 1  # Начальная позиция пешки
        enemy_color = 'b' if piece[0] == 'w' else 'w'

        # Пешка движется вперед на 1 клетку
        if 0 <= r + direction < 8 and self.board[r + direction][c] == '--':
            # Проверка на достижение последнего ряда
            if (piece[0] == 'w' and r + direction == 0) or (piece[0] == 'b' and r + direction == 7):
                # Добавляем все возможные превращения
                for promotion_choice in ['Q', 'R', 'B', 'N']:
                    moves.append(Move((r, c), (r + direction, c), piece, '--', is_pawn_promotion=True,
                                      promotion_choice=promotion_choice))
            else:
                moves.append(Move((r, c), (r + direction, c), piece, '--'))

            # Пешка может пойти на 2 клетки из начальной позиции
            if r == start_row and self.board[r + 2 * direction][c] == '--':
                moves.append(Move((r, c), (r + 2 * direction, c), piece, '--'))

        # Пешка бьет по диагонали
        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                target = self.board[r + direction][c + dc]
                if target != '--' and target[0] == enemy_color:
                    # Если пешка достигает последнего ряда
                    if (piece[0] == 'w' and r + direction == 0) or (piece[0] == 'b' and r + direction == 7):
                        # Добавляем все возможные превращения при взятии
                        for promotion_choice in ['Q', 'R', 'B', 'N']:
                            moves.append(Move((r, c), (r + direction, c + dc), piece, target, is_pawn_promotion=True,
                                              promotion_choice=promotion_choice))
                    else:
                        moves.append(Move((r, c), (r + direction, c + dc), piece, target))

    def get_king_moves(self, r, c, moves):
        """
        Возвращает все возможные ходы для короля на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
        """
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        enemy_color = 'b' if ally_color == 'w' else 'w'

        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]

                # Проверка, чтобы король не двигался на клетку под атакой пешки
                if not self.is_attacked_by_pawn(end_row, end_col, enemy_color) and \
                        (target == '--' or target[0] != ally_color) and \
                        not self.is_square_under_attack(end_row, end_col, ally_color):
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def is_attacked_by_pawn(self, row, col, enemy_color):
        """
        Проверяет, находится ли клетка под атакой пешки.
        
        :param row: Строка на доске.
        :param col: Столбец на доске.
        :param enemy_color: Цвет вражеских пешек.
        :return: True, если клетка под атакой пешки, иначе False.
        """
        direction = -1 if enemy_color == 'w' else 1
        for dc in [-1, 1]:
            r = row + direction
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece == f"{enemy_color}P":  # Проверка, является ли фигура пешкой врага
                    return True
        return False

    def get_queen_moves(self, r, c, moves):
        """
        Возвращает все возможные ходы для ферзя на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
        """
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_rook_moves(self, r, c, moves):
        """
        Возвращает все возможные ходы для ладьи на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
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
        Возвращает все возможные ходы для слона на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
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
        Возвращает все возможные ходы для коня на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
        :param moves: Список, в который добавляются ходы.
        """
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                       (1, -2), (2, -1), (1, 2), (2, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in knight_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--' or target[0] != ally_color:
                    # Проверка, не находится ли конечная клетка под атакой противника
                    if not self.is_square_under_attack(end_row, end_col, ally_color):
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def is_square_under_attack(self, row, col, ally_color):
        """
        Проверяет, находится ли клетка под атакой вражеских фигур.
        
        :param row: Строка на доске.
        :param col: Столбец на доске.
        :param ally_color: Цвет союзных фигур.
        :return: True, если клетка под атакой, иначе False.
        """
        enemy_color = 'b' if ally_color == 'w' else 'w'

        # Проверка атакующих пешек
        direction = -1 if enemy_color == 'w' else 1
        for dc in [-1, 1]:
            r = row + direction
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != '--' and piece[0] == enemy_color and piece[1] == 'P':
                    return True

        # Проверка атакующих коней
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                        (1, -2), (2, -1), (1, 2), (2, 1)]
        for dr, dc in knight_moves:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != '--' and piece[0] == enemy_color and piece[1] == 'N':
                    return True

        # Проверка атакующих ладей и ферзей (по горизонтали и вертикали)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == enemy_color:
                    if piece[1] in ['R', 'Q']:
                        return True
                    else:
                        break
                else:
                    break

        # Проверка атакующих слонов и ферзей (по диагонали)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == enemy_color:
                    if piece[1] in ['B', 'Q']:
                        return True
                    else:
                        break
                else:
                    break

        # Проверка атакующего короля
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != '--' and piece[0] == enemy_color and piece[1] == 'K':
                    return True

        return False

    def in_check(self, white_to_move):
        """
        Проверяет, находится ли король текущего игрока под шахом.
        
        :param white_to_move: Флаг, указывающий, чей ход (белые или черные).
        :return: True, если король под шахом, иначе False.
        """
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--' and piece[0] == ('w' if white_to_move else 'b') and piece[1] == 'K':
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if king_pos is None:
            return False  # Король отсутствует на доске
        return self.is_square_under_attack(king_pos[0], king_pos[1], 'w' if white_to_move else 'b')

    def check_game_state(self):
        """
        Проверяет состояние игры (мат, пат или ничья) и обновляет соответствующие флаги.
        """
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
            if not self.get_valid_moves():
                self.stalemate = True
                self.checkmate = False
                self.result = 'Draw by stalemate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            elif self.is_only_kings():
                self.stalemate = True
                self.result = 'Draw by insufficient material'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.stalemate = False
                self.checkmate = False

    def is_only_kings(self):
        """
        Проверяет, остались ли на доске только короли.
        
        :return: True, если на доске только короли, иначе False.
        """
        return all(piece == '--' or piece[1] == 'K' for row in self.board for piece in row)

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
        Сохраняет завершенную игру в базе данных и экспортирует её в PGN.
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
        Экспортирует игру в формат PGN (Portable Game Notation).
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
            move_number = i // 2 + 1
            white_move = self.move_log[i].get_chess_notation()
            black_move = self.move_log[i + 1].get_chess_notation() if i + 1 < len(self.move_log) else ''
            move_text += f"{move_number}. {white_move} {black_move} "

        move_text += self.result
        pgn_content += move_text

        # Сохранение в файл PGN
        pgn_filename = f"game_{self.start_time.replace(':', '-').replace(' ', '_')}_id_{self.game_id}.pgn"
        with open(pgn_filename, 'w') as f:
            f.write(pgn_content)

    def draw(self, win, images, selected_square=None, valid_moves=None):
        """
        Отрисовывает доску, фигуры и состояние игры.
        
        :param win: Окно Pygame, в котором происходит отрисовка.
        :param images: Словарь с изображениями фигур.
        :param selected_square: Выбранная клетка (строка, столбец).
        :param valid_moves: Список допустимых ходов для выбранной фигуры.
        """
        self.draw_board(win, selected_square, valid_moves)
        self.draw_pieces(win, images)
        self.draw_game_state(win)

    def draw_board(self, win, selected_square, valid_moves):
        """
        Отрисовывает шахматную доску.
        
        :param win: Окно Pygame, в котором происходит отрисовка.
        :param selected_square: Выбранная клетка (строка, столбец).
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
                            center = (c * settings.CELL_SIZE + settings.CELL_SIZE // 2, r * settings.CELL_SIZE + settings.CELL_SIZE // 2)
                            pygame.draw.circle(win, GREEN, center, 10)

    def draw_pieces(self, win, images):
        """
        Отрисовывает фигуры на доске.
        
        :param win: Окно Pygame, в котором происходит отрисовка.
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
                        print(f"Изображение для {piece} не найдено. Проверьте наличие файла и правильность названия.")

    def draw_game_state(self, win):
        """
        Отрисовывает состояние игры (мат, пат или шах).
        
        :param win: Окно Pygame, в котором происходит отрисовка.
        """
        if self.checkmate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Шах и мат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2, settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
        elif self.stalemate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Пат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2, settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
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
        Возвращает все допустимые ходы для фигуры на указанной позиции.
        
        :param r: Строка на доске.
        :param c: Столбец на доске.
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
