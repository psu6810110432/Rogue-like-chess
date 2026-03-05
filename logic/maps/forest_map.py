# logic/maps/forest_map.py
import random
from logic.board import ChessBoard
from logic.pieces import Obstacle

class ForestMap(ChessBoard):
    def __init__(self, white_tribe='medieval', black_tribe='medieval'):
        super().__init__(white_tribe, black_tribe, 'Enchanted Forest')
        self.bg_image = 'assets/boards/forest.png'

    def apply_map_effects(self):
        # โอกาส 15% ที่จะเกิด Event หนาม
        if random.random() < 0.15:
            empty_squares = []
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] is None:
                        empty_squares.append((r, c))

            # สุ่มช่องว่าง 3 ถึง 6 ช่อง
            if len(empty_squares) >= 3:
                num_thorns = random.randint(3, min(6, len(empty_squares)))
                chosen_squares = random.sample(empty_squares, num_thorns)
                for (r, c) in chosen_squares:
                    self.board[r][c] = Obstacle('Thorn', 5) # หนามอยู่ 5 เทิร์น