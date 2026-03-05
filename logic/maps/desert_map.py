# logic/maps/desert_map.py
import random
from logic.board import ChessBoard
from logic.pieces import Obstacle

class DesertMap(ChessBoard):
    def __init__(self, white_tribe='medieval', black_tribe='medieval'):
        super().__init__(white_tribe, black_tribe, 'Desert Ruins')
        self.bg_image = 'assets/boards/desert.png'
        # ✨ FIX: เพิ่มตัวนับเทิร์นสำหรับด่านทะเลทราย
        self.desert_turn_count = 0

    def apply_map_effects(self):
        # ✨ FIX: นับเทิร์นเมื่อวนกลับมาที่ตาของสีขาว
        if self.current_turn == 'white':
            self.desert_turn_count += 1
            
        # ✨ FIX: ตรวจสอบว่าถึงเทิร์นที่ 3 หรือยังก่อนจะเริ่มสุ่มพายุทราย
        if self.desert_turn_count >= 3:
            # โอกาส 25% ที่จะเกิดพายุทราย
            if random.random() < 0.25:
                # หาแถวแนวนอนที่ว่าง 100%
                empty_rows = []
                for r in range(8):
                    if all(self.board[r][c] is None for c in range(8)):
                        empty_rows.append(r)
                
                # หาแถวแนวตั้งที่ว่าง 100%
                empty_cols = []
                for c in range(8):
                    if all(self.board[r][c] is None for r in range(8)):
                        empty_cols.append(c)

                # สุ่มวางพายุทราย 1 แถวแนวนอน และ 1 แถวแนวตั้ง (ถ้ามีแถวว่าง)
                if empty_rows:
                    r = random.choice(empty_rows)
                    for c in range(8):
                        self.board[r][c] = Obstacle('Sandstorm', 3) # พายุอยู่ 3 เทิร์น

                if empty_cols:
                    c = random.choice(empty_cols)
                    for row in range(8):
                        # กันไม่ให้ทับพายุแนวนอนที่เพิ่งวางไป
                        if self.board[row][c] is None: 
                            self.board[row][c] = Obstacle('Sandstorm', 3)