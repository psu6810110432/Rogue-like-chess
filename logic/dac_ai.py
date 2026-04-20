# logic/dac_ai.py
import random
# อนาคตเราจะเขียน AI ประเมินกระดานใหม่ที่นี่ ตอนนี้ขอยืมคลาสเดิมมาประคองระบบก่อน
from logic.ai_logic import ChessAI 

class DACBot:
    @staticmethod
    def decide_item_usage(game, ai_color, difficulty):
        """
        ให้ AI ตัดสินใจว่าจะใช้ไอเทมที่มีในกระเป๋าหรือไม่
        คืนค่ากลับเป็น (ออบเจกต์หมากเป้าหมาย, ออบเจกต์ไอเทม) หากตัดสินใจใช้
        ถ้าไม่ใช้ คืนค่า (None, None)
        """
        inv = getattr(game, f'inventory_{ai_color}', [])
        if not inv:
            return None, None

        use_chance = 0.6 if difficulty == 'hard' else 0.4 if difficulty == 'normal' else 0.25
        
        # ถ้าของเต็มกระเป๋า (5 ชิ้น) บังคับใช้เลย หรือสุ่มติดโอกาสใช้
        if len(inv) >= 5 or random.random() < use_chance:
            item_to_use = random.choice(inv)
            
            # หาหมากฝ่ายตัวเองที่ยังไม่มีไอเทม
            valid_pieces = []
            for row in game.board:
                for p in row:
                    if p and p.color == ai_color and getattr(p, 'item', None) is None:
                        valid_pieces.append(p)
            
            if not valid_pieces:
                return None, None

            candidates = []
            item_id = item_to_use.id
            
            # เลือกเป้าหมายตามประเภทไอเทม
            if item_id == 10: # เฉพาะ Pawn
                candidates = [p for p in valid_pieces if p.__class__.__name__.lower() == 'pawn']
            elif item_id == 9: # ห้าม Knight
                candidates = [p for p in valid_pieces if p.__class__.__name__.lower() != 'knight']
            elif item_id in [1, 2, 4, 8]: # เน้นให้ตัวใหญ่
                candidates = [p for p in valid_pieces if p.__class__.__name__.lower() in ['king', 'queen', 'rook', 'prince', 'princess']]
                if not candidates: candidates = valid_pieces
            elif item_id in [5, 7]: # เน้นให้ตัวเล็ก/ม้า
                candidates = [p for p in valid_pieces if p.__class__.__name__.lower() in ['pawn', 'knight', 'hastati', 'levies']]
                if not candidates: candidates = valid_pieces
            else: # ไม่ให้ King
                candidates = [p for p in valid_pieces if p.__class__.__name__.lower() not in ['king']]
                if not candidates: candidates = valid_pieces

            if candidates:
                if difficulty == 'easy': 
                    chosen_piece = random.choice(candidates)
                elif difficulty == 'normal':
                    # เรียงความเก่ง เลือก 1 ใน 3 ตัวท็อป
                    candidates.sort(key=lambda p: ChessAI.get_piece_value(p), reverse=True)
                    chosen_piece = random.choice(candidates[:min(3, len(candidates))])
                else:
                    # เลือก 1 ใน 2 ตัวท็อป
                    candidates.sort(key=lambda p: ChessAI.get_piece_value(p), reverse=True)
                    chosen_piece = random.choice(candidates[:min(2, len(candidates))])
                
                return chosen_piece, item_to_use

        return None, None

    @staticmethod
    def get_best_move(game, ai_color):
        """
        ตรงนี้คือที่ที่เราจะมาเขียนลอจิกการเดินเฉพาะของ DAC ในอนาคต
        เช่น บังคับ Hastati เดินหน้าชน, บังคับกบฏพุ่งตีตัวสำคัญ ฯลฯ
        """
        # TODO: เขียนระบบประเมินกระดานแบบ DAC (เน้นรักษาจุดยุทธศาสตร์ / ปกป้อง Garrison Commander)
        
        # ตอนนี้เรียกใช้ของเก่าไปก่อนเพื่อให้เกมเดินได้
        return ChessAI.get_best_move(game, ai_color=ai_color)