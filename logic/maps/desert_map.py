# logic/maps/desert_map.py
import random
from logic.board import ChessBoard
from logic.pieces import Obstacle

class DesertMap(ChessBoard):
    def __init__(self, white_tribe='medieval', black_tribe='medieval'):
        super().__init__(white_tribe, black_tribe, 'Desert Ruins')
        self.bg_image = 'assets/boards/desert.png'
        # ตัวนับเทิร์นสำหรับด่านทะเลทราย
        self.desert_turn_count = 0

    def apply_map_effects(self):
        # นับเทิร์นเมื่อกำลังจะเริ่มรอบใหม่ (ตาของสีขาว)
        if self.current_turn == 'white':
            self.desert_turn_count += 1
            
            # พายุจะทำงานทุกๆ 3 เทิร์น (เทิร์น 3, 6, 9, ...)
            if self.desert_turn_count > 0 and self.desert_turn_count % 3 == 0:
                # โอกาส 50% ที่จะเกิดพายุทราย (เพิ่มจาก 25% เพราะไม่ได้เกิดทุกเทิร์นแล้ว)
                if random.random() < 0.50:
                    
                    # หาช่องว่างทั้งหมดบนกระดาน
                    empty_squares = []
                    for r in range(8):
                        for c in range(8):
                            if self.board[r][c] is None:
                                empty_squares.append((r, c))
                    
                    # สุ่มเกิดพายุ 2-4 ช่อง เพื่อไม่ให้เกะกะการเดินมากเกินไป
                    if empty_squares:
                        # หาจำนวนที่จะเสก โดยไม่เกินจำนวนช่องว่างที่มี
                        num_storms = min(random.randint(2, 4), len(empty_squares))
                        storm_locations = random.sample(empty_squares, num_storms)
                        
                        for r, c in storm_locations:
                            # เสกพายุทราย ซึ่งจะคงอยู่เป็นเวลา 3 เทิร์น
                            self.board[r][c] = Obstacle('Sandstorm', 3)