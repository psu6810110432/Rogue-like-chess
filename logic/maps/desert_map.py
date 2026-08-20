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
                # โอกาส 50% ที่จะเกิดพายุทราย 
                if random.random() < 0.50:
                    
                    valid_lines = []
                    storm_length = random.choice([3, 4]) # สุ่มความยาวพายุ 3 หรือ 4 ช่อง
                    
                    # ฟังก์ชันช่วยหาพื้นที่ว่างที่เรียงติดกัน
                    def find_contiguous_empty(length):
                        lines = []
                        # 1. ค้นหาแนวนอน
                        for r in range(8):
                            for c in range(8 - length + 1):
                                if all(self.board[r][c+i] is None for i in range(length)):
                                    lines.append([(r, c+i) for i in range(length)])
                        # 2. ค้นหาแนวตั้ง
                        for c in range(8):
                            for r in range(8 - length + 1):
                                if all(self.board[r+i][c] is None for i in range(length)):
                                    lines.append([(r+i, c) for i in range(length)])
                        return lines

                    valid_lines = find_contiguous_empty(storm_length)
                    
                    # ถ้าสุ่มได้ 4 ช่อง แต่กระดานไม่มีที่ว่างติดกัน 4 ช่องเลย ให้ลองหาแบบ 3 ช่องแทน
                    if not valid_lines and storm_length == 4:
                        storm_length = 3
                        valid_lines = find_contiguous_empty(storm_length)

                    # ถ้าเจอพื้นที่ที่ลงได้ ให้ทำการเสกพายุทราย
                    if valid_lines:
                        chosen_line = random.choice(valid_lines)
                        for r, c in chosen_line:
                            # เสกพายุทราย ซึ่งจะคงอยู่เป็นเวลา 3 เทิร์น[cite: 3]
                            self.board[r][c] = Obstacle('Sandstorm', 3)