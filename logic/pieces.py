# logic/pieces.py
import random
from components.passive.passive_manager import PassiveManager
from components.hidden_passive import HiddenPassive

class Piece:
    def __init__(self, color, name):
        self.color, self.name, self.item, self.has_moved = color, name, None, False
        self.hidden_passive = HiddenPassive()

    def is_path_clear(self, start, end, board):
        sr, sc, er, ec = start[0], start[1], end[0], end[1]
        step_r = 0 if sr == er else (1 if er > sr else -1)
        step_c = 0 if sc == ec else (1 if ec > sc else -1)
        cr, cc = sr + step_r, sc + step_c
        while (cr, cc) != (er, ec):
            if board[cr][cc] is not None: return False
            cr, cc = cr + step_r, cc + step_c
        return True

    def setup_stats(self, piece_type, tribe):
        passive = PassiveManager.get_passive_handler(piece_type, tribe)
        stats = passive['get_piece_stats']() if passive else {'dice': 0, 'coins': 0, 'max': 12}
        self.base_points, self.coins = self.hidden_passive.apply_passive(stats['dice'], stats['coins'])
        self.max_stats = stats['max'] # ✨ ดึงค่า Max จากเผ่า

    def check_knight_move(self, s, e):
        rd, cd = abs(s[0]-e[0]), abs(s[1]-e[1])
        return (rd == 2 and cd == 1) or (rd == 1 and cd == 2)

class Rook(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'R' if color == 'white' else 'r')
        self.setup_stats('rook', tribe)
    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e): return True
        return (s[0] == e[0] or s[1] == e[1]) and self.is_path_clear(s, e, b)

class Knight(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'N' if color == 'white' else 'n')
        self.setup_stats('knight', tribe)
    def is_valid_move(self, s, e, b):
        if s == e: return False
        target = b[e[0]][e[1]]
        return self.check_knight_move(s, e) and (target is None or target.color != self.color)

class Bishop(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'B' if color == 'white' else 'b')
        self.setup_stats('bishop', tribe)
    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e): return True
        return abs(s[0]-e[0]) == abs(s[1]-e[1]) and self.is_path_clear(s, e, b)

class Queen(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'Q' if color == 'white' else 'q')
        self.setup_stats('queen', tribe)
    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e): return True
        return (s[0] == e[0] or s[1] == e[1] or abs(s[0]-e[0]) == abs(s[1]-e[1])) and self.is_path_clear(s, e, b)

class King(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'K' if color == 'white' else 'k')
        self.setup_stats('king', tribe)
    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e): return True
        return max(abs(s[0]-e[0]), abs(s[1]-e[1])) == 1

class Pawn(Piece):
    def __init__(self, color, tribe='medieval'):
        super().__init__(color, 'P' if color == 'white' else 'p')
        self.setup_stats('pawn', tribe)
        self.variant = random.randint(6, 9)
    def is_valid_move(self, s, e, b, ep_target=None):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e): return True
        sr, sc, er, ec, dr = s[0], s[1], e[0], e[1], (-1 if self.color == 'white' else 1)
        target = b[er][ec]
        if sc == ec and er == sr + dr and not target: return True
        if sc == ec and sr == (6 if self.color == 'white' else 1) and er == sr + 2*dr and not target and not b[sr+dr][sc]: return True
        if abs(sc - ec) == 1 and er == sr + dr and (target or (ep_target and (er, ec) == ep_target)): return True
        return False

class Obstacle(Piece):
    def __init__(self, n, l):
        self.color, self.name, self.item, self.lifespan, self.base_points, self.coins, self.has_moved = 'neutral', n, None, l, 0, 0, False
    def is_valid_move(self, s, e, b): return False