# logic/maps/tundra_map.py
import random
from logic.board import ChessBoard
from logic.pieces import King, Obstacle 

class TundraMap(ChessBoard):
    def __init__(self, white_tribe='medieval', black_tribe='medieval'):
        super().__init__(white_tribe, black_tribe, 'Frozen Tundra')
        self.bg_image = 'assets/boards/tundra.png'
        self.tundra_turn_count = 0  

    def apply_map_effects(self):
        # --- 1. Event แช่แข็งหมาก ---
        # นำ if self.current_turn == 'white': ออก เพื่อให้นับทุกๆ 1 เฟส (การเดินของใครก็ได้)
        self.tundra_turn_count += 1
        
        # ทำงานทุกๆ 5 เฟส
        if self.tundra_turn_count % 5 == 0:
            white_pieces = []
            black_pieces = []
            
            # รวบรวมหมากที่สามารถแช่แข็งได้
            for r in range(8):
                for c in range(8):
                    p = self.board[r][c]
                    if p and getattr(p, 'color', '') != 'neutral' and not isinstance(p, King):
                        if getattr(p, 'freeze_timer', 0) <= 0:
                            if p.color == 'white':
                                white_pieces.append(p)
                            elif p.color == 'black':
                                black_pieces.append(p)
                                
            # สุ่มแช่แข็งฝ่ายละ 2 ตัว 
            if white_pieces:
                num_to_freeze = min(2, len(white_pieces))
                for p in random.sample(white_pieces, num_to_freeze):
                    p.freeze_timer = 3  # เปลี่ยนเป็นแช่แข็งนาน 3 เฟส
                    
            if black_pieces:
                num_to_freeze = min(2, len(black_pieces))
                for p in random.sample(black_pieces, num_to_freeze):
                    p.freeze_timer = 3  # เปลี่ยนเป็นแช่แข็งนาน 3 เฟส

        # --- 2. Event ก้อนน้ำแข็ง (Ice) กีดขวางทาง ---
        if random.random() < 0.08:
            empty_squares = []
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] is None:
                        empty_squares.append((r, c))

            if len(empty_squares) >= 1:
                num_ice = random.randint(1, min(3, len(empty_squares)))
                chosen_squares = random.sample(empty_squares, num_ice)
                for (r, c) in chosen_squares:
                    # ปรับลดความนานของ Ice obstacle ตามโครงสร้างของเฟสให้สัมพันธ์กันได้ตามต้องการ
                    self.board[r][c] = Obstacle('Ice', 4)