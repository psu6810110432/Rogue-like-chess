# logic/pieces.py
import random
from components.passive.passive_manager import PassiveManager
from components.hidden_passive import HiddenPassive

class Piece:
    def __init__(self, color, name):
        self.color, self.name, self.item, self.has_moved = color, name, None, False
        self.hidden_passive = HiddenPassive()
        self.passive_desc = "" 
        self.tribe = "the knight company" 

    def is_path_clear(self, start, end, board):
        sr, sc, er, ec = start[0], start[1], end[0], end[1]
        step_r = 0 if sr == er else (1 if er > sr else -1)
        step_c = 0 if sc == ec else (1 if ec > sc else -1)
        
        cr, cc = sr + step_r, sc + step_c
        while (cr, cc) != (er, ec):
            if board[cr][cc] is not None: 
                return False
            cr, cc = cr + step_r, cc + step_c
        return True

    def setup_stats(self, piece_type, tribe):
        if not tribe:
            tribe = 'the knight company'
        self.tribe = tribe 
        
        passive = PassiveManager.get_passive_handler(piece_type, tribe)
        if passive:
            stats = passive['get_piece_stats']()
            self.base_points, self.coins = self.hidden_passive.apply_passive(stats['dice'], stats['coins'])
            self.max_stats = stats['max']
            self.passive_desc = stats['desc']
        else:
            self.base_points, self.coins, self.max_stats, self.passive_desc = 5, 3, 12, ""

    def check_knight_move(self, s, e):
        rd, cd = abs(s[0]-e[0]), abs(s[1]-e[1])
        return (rd == 2 and cd == 1) or (rd == 1 and cd == 2)

class Rook(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'R' if color == 'white' else 'r')
        self.setup_stats('rook', tribe)

    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e):
            return True
        return (s[0] == e[0] or s[1] == e[1]) and self.is_path_clear(s, e, b)

class Knight(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'N' if color == 'white' else 'n')
        self.setup_stats('knight', tribe)

    def is_valid_move(self, s, e, b):
        if s == e: return False
        target = b[e[0]][e[1]]
        if self.check_knight_move(s, e):
            return target is None or target.color != self.color
        return False

class Bishop(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'B' if color == 'white' else 'b')
        self.setup_stats('bishop', tribe)

    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e):
            return True
        return abs(s[0]-e[0]) == abs(s[1]-e[1]) and self.is_path_clear(s, e, b)

class Queen(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'Q' if color == 'white' else 'q')
        self.setup_stats('queen', tribe)

    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e):
            return True
        is_straight = (s[0] == e[0] or s[1] == e[1])
        is_diagonal = (abs(s[0]-e[0]) == abs(s[1]-e[1]))
        return (is_straight or is_diagonal) and self.is_path_clear(s, e, b)

class King(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'K' if color == 'white' else 'k')
        self.setup_stats('king', tribe)

    def is_valid_move(self, s, e, b):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e):
            return True
        return max(abs(s[0]-e[0]), abs(s[1]-e[1])) == 1

class Pawn(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'P' if color == 'white' else 'p')
        self.setup_stats('pawn', tribe)
        self.variant = random.randint(1, 4)

    def is_valid_move(self, s, e, b, ep_target=None):
        if s == e: return False
        if getattr(self, 'item', None) and self.item.id == 9 and self.check_knight_move(s, e):
            return True
            
        sr, sc, er, ec, dr = s[0], s[1], e[0], e[1], (-1 if self.color == 'white' else 1)
        target = b[er][ec]
        
        if sc == ec and er == sr + dr and not target: return True
        if sc == ec and sr == (6 if self.color == 'white' else 1) and er == sr + 2*dr and not target and not b[sr+dr][sc]: return True
        if abs(sc - ec) == 1 and er == sr + dr:
            if target: return True
            if ep_target and (er, ec) == ep_target:
                ep_pawn = b[sr][ec]
                if ep_pawn and getattr(ep_pawn, 'color', None) != self.color and isinstance(ep_pawn, Pawn):
                    return True
        return False

class Princess(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'PR' if color == 'white' else 'pr')
        self.setup_stats('princess', tribe)

    def get_valid_moves(self, board):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for d in directions:
            for step in range(1, 4): 
                r = self.row + d[0] * step
                c = self.col + d[1] * step
                if 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    elif board[r][c].color != self.color:
                        moves.append((r, c))
                        break
                    else:
                        break
                else:
                    break
        return moves

class Menatarm(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'M' if color == 'white' else 'm')
        self.setup_stats('menatarm', tribe)

    def get_valid_moves(self, board):
        moves = []
        fwd = -1 if self.color == 'white' else 1
        directions = [(fwd, 0), (fwd, 1), (fwd, -1), (0, 1), (0, -1), (-fwd, 1), (-fwd, -1)]
        for d in directions:
            r = self.row + d[0]
            c = self.col + d[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None or board[r][c].color != self.color:
                    moves.append((r, c))
        return moves

class Praetorian(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'PT' if color == 'white' else 'pt')
        self.setup_stats('praetorian', tribe)

    def get_valid_moves(self, board):
        moves = []
        for d in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for step in range(1, 3):
                r = self.row + d[0] * step
                c = self.col + d[1] * step
                if 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if board[r][c].color != self.color:
                            moves.append((r, c))
                        break
        
        knight_moves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
        for d in knight_moves:
            r = self.row + d[0]
            c = self.col + d[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None or board[r][c].color != self.color:
                    moves.append((r, c))
        return moves

class Royalguard(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'RG' if color == 'white' else 'rg')
        self.setup_stats('royalguard', tribe)

    def get_valid_moves(self, board):
        moves = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1), 
            (-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)  
        ]
        for d in directions:
            r = self.row + d[0]
            c = self.col + d[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None or board[r][c].color != self.color:
                    moves.append((r, c))
        return moves

class Hastati(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'H' if color == 'white' else 'h')
        self.setup_stats('hastati', tribe)
        self.variant = random.randint(1, 4)

    def get_valid_moves(self, board):
        moves = []
        fwd = -1 if self.color == 'white' else 1
        for step in range(1, 4): 
            r = self.row + fwd * step
            c = self.col
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None:
                    moves.append((r, c))
                elif board[r][c].color != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
        return moves

class Levies(Piece):
    def __init__(self, color, tribe='the knight company'):
        super().__init__(color, 'L' if color == 'white' else 'l')
        self.setup_stats('levies', tribe)
        self.variant = random.randint(1, 4)

    def get_valid_moves(self, board):
        moves = []
        fwd = -1 if self.color == 'white' else 1
        r = self.row + fwd
        c = self.col
        if 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] is None or board[r][c].color != self.color:
                moves.append((r, c))
        return moves

class Obstacle(Piece):
    def __init__(self, n, l):
        self.color, self.name, self.item, self.lifespan, self.base_points, self.coins, self.has_moved = 'neutral', n, None, l, 0, 0, False
        self.tribe = "neutral" 

    def is_valid_move(self, s, e, b):
        return False