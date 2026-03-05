# logic/board.py
import copy 
import random
from logic.pieces import Rook, Knight, Bishop, Queen, King, Pawn, Obstacle
from logic.history_logic import HistoryManager
from logic.item_logic import ITEM_DATABASE
from logic.item_effects import apply_post_crash_effects # นำเข้า Logic ของ Item

class ChessBoard:
    def __init__(self, white_tribe='medieval', black_tribe='medieval', map_name='Classic Board'):
        self.white_tribe = white_tribe
        self.black_tribe = black_tribe
        self.board = self.create_initial_board()
        self.current_turn = 'white'
        self.last_move = None
        self.en_passant_target = None 
        self.game_result = None
        self.history = HistoryManager() 
        self.bg_image = '' 
        self.freeze_timer = 0  
        self.inventory_white = [] 
        self.inventory_black = [] 
        
        # ตั้งค่าธีมด่าน
        self.set_map_theme(map_name)

    def set_map_theme(self, map_name):
        map_assets = {
            'Classic Board': 'assets/boards/classic.png',
            'Enchanted Forest': 'assets/boards/forest.png',
            'Desert Ruins': 'assets/boards/desert.png',
            'Frozen Tundra': 'assets/boards/tundra.png'
        }
        self.bg_image = map_assets.get(map_name, 'assets/boards/classic.png')

    # ✨ อัปเดต: ระบบการแจกไอเทมตามเงื่อนไขใหม่
    def handle_item_drop(self, winner, is_defender=False):
        """จัดการการได้รับไอเทมเมื่อชนะการปะทะ (Crash)"""
        piece_type = winner.__class__.__name__.lower()
        should_receive = False
        
        if not is_defender:
            # ⚔️ ฝ่ายรุก (Attacker): เฉพาะ Rook, Bishop, Knight เท่านั้นที่ได้ไอเทม
            if piece_type in ['rook', 'bishop', 'knight']:
                should_receive = True
        else:
            # 🛡️ ฝ่ายรับ (Defender): Knight, Rook, Bishop จะ *ไม่ได้* ไอเทม
            if piece_type not in ['knight', 'rook', 'bishop', 'queen', 'king']:
                should_receive = True
        
        if should_receive:
            target_inv = self.inventory_white if winner.color == 'white' else self.inventory_black
            
            if len(target_inv) < 5:
                # สุ่มไอเทมจากคลัง (ID 1-10)
                random_item_id = random.randint(1, 10)
                item = ITEM_DATABASE[random_item_id]
                target_inv.append(item)
                print(f"DEBUG: {winner.color} {piece_type} received {item.name} from {'Defense' if is_defender else 'Attack'}!")

    def create_initial_board(self):
        b = [[None for _ in range(8)] for _ in range(8)]
        b[0] = [Rook('black', self.black_tribe), Knight('black', self.black_tribe), Bishop('black', self.black_tribe), Queen('black', self.black_tribe), King('black', self.black_tribe), Bishop('black', self.black_tribe), Knight('black', self.black_tribe), Rook('black', self.black_tribe)]
        b[1] = [Pawn('black', self.black_tribe) for _ in range(8)]
        b[6] = [Pawn('white', self.white_tribe) for _ in range(8)]
        b[7] = [Rook('white', self.white_tribe), Knight('white', self.white_tribe), Bishop('white', self.white_tribe), Queen('white', self.white_tribe), King('white', self.white_tribe), Bishop('white', self.white_tribe), Knight('white', self.white_tribe), Rook('white', self.white_tribe)]
        return b

    def simulate_move(self, sr, sc, er, ec, color):
        p, t = self.board[sr][sc], self.board[er][ec]
        self.board[sr][sc], self.board[er][ec] = None, p
        check = self.is_in_check(color)
        self.board[sr][sc], self.board[er][ec] = p, t
        return check

    def get_legal_moves(self, pos):
        sr, sc = pos
        piece = self.board[sr][sc]
        if not piece: return []
        if getattr(piece, 'freeze_timer', 0) > 0: return []

        moves = []
        for r in range(8):
            for c in range(8):
                target = self.board[r][c]
                if target and (target.color == piece.color or getattr(target, 'color', '') == 'neutral'): 
                    continue
                valid = piece.is_valid_move((sr, sc), (r, c), self.board, self.en_passant_target) if isinstance(piece, Pawn) else piece.is_valid_move((sr, sc), (r, c), self.board)
                if valid and not self.simulate_move(sr, sc, r, c, piece.color):
                    moves.append((r, c))
        if isinstance(piece, King) and not piece.has_moved and not self.is_in_check(piece.color):
            for tc in [2, 6]:
                if self.check_castling_logic(sr, sc, sr, tc): moves.append((sr, tc))
        return moves

    def check_castling_logic(self, sr, sc, er, ec):
        p = self.board[sr][sc]
        rc = 0 if ec == 2 else 7
        rook = self.board[sr][rc]
        if not rook or not isinstance(rook, Rook) or rook.has_moved: return False
        step = 1 if ec == 6 else -1
        for col in range(sc + step, rc, step):
            if self.board[sr][col]: return False
        for col in [sc + step, sc + 2*step]:
            if self.simulate_move(sr, sc, sr, col, p.color): return False
        return True

    def move_piece(self, sr, sc, er, ec, resolve_crash=False, crash_won=True):
        p = self.board[sr][sc]
        if not p or p.color != self.current_turn or self.game_result: return False
            
        is_castle = isinstance(p, King) and abs(sc-ec) == 2
        is_ep = isinstance(p, Pawn) and (er, ec) == self.en_passant_target
        legal_moves = self.get_legal_moves((sr, sc))
        
        if (er, ec) not in legal_moves: return False
            
        target = self.board[er][ec]
        is_capture = (target is not None) or is_ep
        captured_piece = target if not is_ep else self.board[sr][ec]

        # --- อัปเดต: ระบบ CRASH พร้อมการแจกไอเทมตามเงื่อนไขใหม่ ---
        if is_capture and not resolve_crash:
            return ("crash", p, captured_piece)
            
        if is_capture and resolve_crash:
            if crash_won == "died": # 🛡️ ฝ่ายรับ (Defender) ชนะการปะทะ
                effect_result = apply_post_crash_effects(self, p, captured_piece, True, sr, sc, er, ec)
                p.has_moved = True
                
                # ✨ เรียกใช้การแจกไอเทมให้ฝ่ายรับ (หมากที่ยืนอยู่ที่ช่องเป้าหมาย)
                self.handle_item_drop(captured_piece, is_defender=True)
                
                if effect_result != "survived":
                    self.board[sr][sc] = None
                self.history.save_state(self, f"{p.name} attacked but died against {captured_piece.name}")
                self.complete_turn()
                return "survived" if effect_result == "survived" else "died"
            elif not crash_won:
                return False
            else: # ⚔️ ฝ่ายรุก (Attacker) ชนะการปะทะ
                effect_result = apply_post_crash_effects(self, p, captured_piece, False, sr, sc, er, ec)
                
                # ✨ เรียกใช้การแจกไอเทมให้ฝ่ายรุก
                self.handle_item_drop(p, is_defender=False)
                
                if effect_result == "defender_survived":
                    p.has_moved = True
                    self.history.save_state(self, f"{p.name} attacked but {captured_piece.name} survived")
                    self.complete_turn()
                    return True 
        # ---------------------------------------------------
        
        move_text = self.history.generate_move_text(p, sr, sc, er, ec, is_capture, is_castle)
        self.history.save_state(self, move_text)
        
        if is_ep: self.board[sr][ec] = None 
        if is_castle:
            rc, nrc = (0, 3) if ec == 2 else (7, 5)
            self.board[sr][nrc], self.board[sr][rc] = self.board[sr][rc], None
            self.board[sr][nrc].has_moved = True
            
        if isinstance(p, Pawn) and abs(sr - er) == 2: 
            self.en_passant_target = ((sr + er) // 2, sc)
        else: self.en_passant_target = None
            
        self.last_move = ((sr, sc), (er, ec))
        self.board[er][ec] = p
        if self.board[sr][sc] == p: self.board[sr][sc] = None
        p.has_moved = True
        
        if isinstance(p, Pawn) and (er == 0 or er == 7): return "promote"
            
        self.complete_turn()
        return True

    def undo_move(self):
        state = self.history.pop_state()
        if not state: return False
        self.board = state['board']
        self.current_turn = state['current_turn']
        self.last_move = state['last_move']
        self.en_passant_target = state['en_passant_target']
        self.game_result = state['game_result']
        self.inventory_white = state.get('inventory_white', [])
        self.inventory_black = state.get('inventory_black', [])
        return True

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and isinstance(p, King) and p.color == color: return (r, c)
        return None

    def is_in_check(self, color):
        kp = self.find_king(color)
        if not kp: return False
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.color != color and p.is_valid_move((r, c), kp, self.board): return True
        return False

    def check_insufficient_material(self):
        pieces = []
        for row in self.board:
            for p in row:
                if p: pieces.append(p.__class__.__name__)
        if len(pieces) <= 2: return True 
        if len(pieces) == 3 and ('Bishop' in pieces or 'Knight' in pieces): return True
        return False

    def complete_turn(self):
        if not self.find_king('white'):
            self.game_result = "BLACK WINS! (WHITE KING DESTROYED)"
            return
        if not self.find_king('black'):
            self.game_result = "WHITE WINS! (BLACK KING DESTROYED)"
            return
            
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        self.update_map_events()

        has_moves = False
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.color == self.current_turn:
                    if self.get_legal_moves((r, c)): 
                        has_moves = True
                        break
            if has_moves: break
            
        is_check = self.is_in_check(self.current_turn)
        if not has_moves:
            is_frozen_locked = any(getattr(p, 'freeze_timer', 0) > 0 for row in self.board for p in row if p and getattr(p, 'color', '') == self.current_turn)
            if is_frozen_locked and not is_check:
                self.complete_turn()
                return
            elif is_check:
                winner = 'black' if self.current_turn == 'white' else 'white'
                self.game_result = f"CHECKMATE! {winner.upper()} WINS"
                self.history.add_suffix_to_last_move("#") 
            else: self.game_result = "DRAW - STALEMATE" 
        elif self.check_insufficient_material(): self.game_result = "DRAW - INSUFFICIENT MATERIAL"
        elif is_check: self.history.add_suffix_to_last_move("+")

    def update_map_events(self):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p:
                    if getattr(p, 'color', '') == 'neutral' and hasattr(p, 'lifespan'):
                        p.lifespan -= 1
                        if p.lifespan <= 0: self.board[r][c] = None 
                    if getattr(p, 'freeze_timer', 0) > 0: p.freeze_timer -= 1

    def promote_pawn(self, r, c, cls):
        color = self.board[r][c].color
        self.board[r][c] = cls(color)
        self.history.add_suffix_to_last_move(f"={self.board[r][c].name.upper()}")
        self.complete_turn()