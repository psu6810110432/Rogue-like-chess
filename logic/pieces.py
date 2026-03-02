# logic/pieces.py
import random
from components.passive.passive_manager import PassiveManager
from components.hidden_passive import HiddenPassive

class Piece:
    def __init__(self, color, name):
        self.color = color
        self.name = name
        self.item = None

        # --- เพิ่ม 2 บรรทัดนี้สำหรับระบบ Crash ---
        self.base_points = 5  # ค่าพลังตั้งต้นชั่วคราว (แก้ได้ตามใจชอบ)
        self.coins = 3        # จำนวนเหรียญที่มีชั่วคราว (แก้ได้ตามใจชอบ)
        # ----------------------------------

        self.has_moved = False
        
        # เพิ่มระบบ passive แฝง
        self.hidden_passive = HiddenPassive()
        # ปรับค่าพลังตาม passive แฝง
        default_points, default_coins = 5, 3
        self.base_points, self.coins = self.hidden_passive.apply_passive(default_points, default_coins)

    def is_path_clear(self, start, end, board):
        sr, sc, er, ec = start[0], start[1], end[0], end[1]
        step_r = 0 if sr == er else (1 if er > sr else -1)
        step_c = 0 if sc == ec else (1 if ec > sc else -1)
        
        # เริ่มเช็คจากช่องถัดไป
        cr, cc = sr + step_r, sc + step_c
        
        while (cr, cc) != (er, ec):
            if board[cr][cc] is not None: 
                return False
            # 
            cr += step_r
            cc += step_c
            
        return True

class Rook(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'R' if color == 'white' else 'r')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities
        passive = PassiveManager.get_passive_handler('rook', tribe)
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ Rook
        
    def is_valid_move(self, start, end, board):
        #  9: Pegasus Boots
        if getattr(self, 'item', None) and self.item.id == 9:
            rd, cd = abs(start[0]-end[0]), abs(start[1]-end[1])
            if (rd == 2 and cd == 1) or (rd == 1 and cd == 2): return True

        if start[0] == end[0] or start[1] == end[1]: 
            return self.is_path_clear(start, end, board)
        return False

class Knight(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'N' if color == 'white' else 'n')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities
        passive = PassiveManager.get_passive_handler('knight', tribe)
        
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ Knight
        
    def is_valid_move(self, start, end, board):
        # Knight มาตรฐาน: เดินแบบ L-shape (ไม่ใช้ passive)
        sr, sc, er, ec = start[0], start[1], end[0], end[1]
        
        # คำนวณระยะทาง
        row_diff = abs(sr - er)
        col_diff = abs(sc - ec)
        
        # ตรวจสอบการเดินแบบ L-shape: 2 ช่องในแนวหนึ่ง + 1 ช่องในอีกแนวหนึ่ง
        is_l_shape = (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
        
        if not is_l_shape:
            return False
            
        # ตรวจสอบว่าช่องเป้าหมายไม่มีหมากฝ่ายเดียวกัน
        target = board[er][ec]
        if target and target.color == self.color:
            return False
            
        return True

class Bishop(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'B' if color == 'white' else 'b')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities
        passive = PassiveManager.get_passive_handler('bishop', tribe)
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ Bishop
        
    def is_valid_move(self, start, end, board):
        #  9: Pegasus Boots
        if getattr(self, 'item', None) and self.item.id == 9:
            rd, cd = abs(start[0]-end[0]), abs(start[1]-end[1])
            if (rd == 2 and cd == 1) or (rd == 1 and cd == 2): return True
        if abs(start[0]-end[0]) == abs(start[1]-end[1]): 
            return self.is_path_clear(start, end, board)
        return False

class Queen(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'Q' if color == 'white' else 'q')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities
        passive = PassiveManager.get_passive_handler('queen', tribe)
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ Queen
        
    def is_valid_move(self, start, end, board):
        # ✨ Item 9: เดินทะลุ
        if getattr(self, 'item', None) and self.item.id == 9:
            return True # อนุญาตให้ทะลุตัวขวางได้เลยประหนึ่งว่าเป็นม้า
        return Rook(self.color).is_valid_move(start, end, board) or Bishop(self.color).is_valid_move(start, end, board)


class King(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'K' if color == 'white' else 'k')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities
        passive = PassiveManager.get_passive_handler('king', tribe)
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ King
        
    def is_valid_move(self, start, end, board):
        #  9: Pegasus Boots
        if getattr(self, 'item', None) and self.item.id == 9:
            rd, cd = abs(start[0]-end[0]), abs(start[1]-end[1])
            if (rd == 2 and cd == 1) or (rd == 1 and cd == 2): return True
        return max(abs(start[0]-end[0]), abs(start[1]-end[1])) == 1

class Pawn(Piece):
    def __init__(self, color, tribe='medieval'): 
        super().__init__(color, 'P' if color == 'white' else 'p')
        self.tribe = tribe
        
        # ใช้ PassiveManager จัดการ passive abilities (สำหรับ future tribes)
        passive = PassiveManager.get_passive_handler('pawn', tribe)
        if passive:
            stats = passive['get_piece_stats']()
            tribe_points, tribe_coins = stats['dice'], stats['coins']
        else:
            tribe_points, tribe_coins = 0, 0
        
        # ใช้ passive แฝงปรับค่า
        self.base_points, self.coins = self.hidden_passive.apply_passive(tribe_points, tribe_coins)
        self.max_stats = 12  # ค่าคงที่สำหรับ Pawn
        
        self.variant = random.randint(6, 9)
        
    def is_valid_move(self, start, end, board, ep_target=None):
        # การเดินแบบปกติ (สำหรับเผ่าอื่นๆ ที่ยังไม่ implement)
        if getattr(self, 'item', None) and self.item.id == 9:
            rd, cd = abs(start[0]-end[0]), abs(start[1]-end[1])
            if (rd == 2 and cd == 1) or (rd == 1 and cd == 2): return True
        sr, sc, er, ec = start[0], start[1], end[0], end[1]
        dir = -1 if self.color == 'white' else 1
        target = board[er][ec]
        
        # เดินตรง 1 ช่อง
        if sc == ec and er == sr + dir and not target: 
            return True
        # เดินตรง 2 ช่องจากจุดเริ่มต้น
        if sc == ec and sr == (6 if self.color == 'white' else 1) and er == sr + 2*dir and not target and not board[sr+dir][sc]: 
            return True
        # กินเฉียง
        if abs(sc - ec) == 1 and er == sr + dir and target: 
            return True
        # กิน En Passant
        if ep_target and (er, ec) == ep_target and abs(sc - ec) == 1 and er == sr + dir: 
            return True
            
        return False

class Obstacle(Piece):
    def __init__(self, name, lifespan):
        # สิ่งกีดขวางไม่มี passive แฝง - ไม่เรียก super().__init__
        self.color = 'neutral'  # เป็นกลางเพื่อไม่ให้ถูกมองว่าเป็นหมากของฝ่ายใดฝ่ายหนึ่ง
        self.name = name
        self.item = None
        self.lifespan = lifespan # อายุของสิ่งกีดขวาง (จำนวนเทิร์น)
        self.base_points = 0
        self.coins = 0
        self.has_moved = False
        # ไม่สร้าง hidden_passive สำหรับ Obstacle

    def is_valid_move(self, start, end, board):
        # สิ่งกีดขวางไม่สามารถเดินได้
        return False