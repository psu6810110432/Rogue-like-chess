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
        # --- 1. Event แช่แข็งหมาก (ปรับให้เกิดยากขึ้นและแช่น้อยลง) ---
        if self.current_turn == 'white':
            self.tundra_turn_count += 1
            
            # ✨ FIX: ปรับระยะเวลาจาก "ทุกๆ 3 เทิร์น" เป็น "ทุกๆ 5 เทิร์น"
            if self.tundra_turn_count % 5 == 0:
                white_pieces = []
                black_pieces = []
                
                # รวบรวมหมากที่สามารถแช่แข็งได้ (ไม่ใช่ King, ไม่ใช่สิ่งกีดขวาง, และยังไม่โดนแช่แข็งซ้ำ)
                for r in range(8):
                    for c in range(8):
                        p = self.board[r][c]
                        if p and getattr(p, 'color', '') != 'neutral' and not isinstance(p, King):
                            if getattr(p, 'freeze_timer', 0) <= 0:
                                if p.color == 'white':
                                    white_pieces.append(p)
                                elif p.color == 'black':
                                    black_pieces.append(p)
                                    
                # ✨ FIX: ลดจำนวนการสุ่มแช่แข็งเหลือแค่ 1 ตัวจากทีมสีขาว (จากเดิม 2)
                if white_pieces:
                    num_to_freeze = min(1, len(white_pieces))
                    for p in random.sample(white_pieces, num_to_freeze):
                        p.freeze_timer = 6  # ใส่ค่า 6 เท่ากับแช่ 3 เทิร์นเต็มเหมือนเดิม
                        
                # ✨ FIX: ลดจำนวนการสุ่มแช่แข็งเหลือแค่ 1 ตัวจากทีมสีดำ (จากเดิม 2)
                if black_pieces:
                    num_to_freeze = min(1, len(black_pieces))
                    for p in random.sample(black_pieces, num_to_freeze):
                        p.freeze_timer = 6

        # --- 2. Event ก้อนน้ำแข็ง (Ice) กีดขวางทาง ---
        # ✨ FIX: ลดโอกาสเกิดก้อนน้ำแข็งขวางทางจาก 15% เหลือ 8%
        if random.random() < 0.08:
            empty_squares = []
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] is None:
                        empty_squares.append((r, c))

            # ✨ FIX: ลดจำนวนก้อนน้ำแข็งที่จะโผล่มา จากเดิม 3-6 ก้อน เหลือ 1-3 ก้อน
            if len(empty_squares) >= 1:
                num_ice = random.randint(1, min(3, len(empty_squares)))
                chosen_squares = random.sample(empty_squares, num_ice)
                for (r, c) in chosen_squares:
                    self.board[r][c] = Obstacle('Ice', 4) # ✨ FIX: ปรับให้อยู่ 4 เทิร์น (ละลายเร็วขึ้นนิดนึง)