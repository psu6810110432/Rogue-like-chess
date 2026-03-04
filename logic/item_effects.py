# logic/item_effects.py
import random

def apply_equip_effect(piece):
    """เรียกใช้ทันทีเมื่อหมากสวมใส่ไอเทม (ใช้ตอนกดใช้ไอเทมจากกระเป๋า)"""
    if not piece or not getattr(piece, 'item', None):
        return
    
    # Item 6: Gambler's Coin (+1 Coin, -2 Base Point)
    if piece.item.id == 6:
        piece.coins += 1
        piece.base_points = max(0, piece.base_points - 2)
        
    # Item 10: Crown of the Usurper (สำหรับเบี้ยเท่านั้น เปลี่ยน Base=5, Coin=3)
    elif piece.item.id == 10 and piece.__class__.__name__.lower() == 'pawn':
        piece.base_points = 5
        piece.coins = 3

def get_pre_crash_modifiers(attacker, defender):
    """คำนวณเอฟเฟกต์ที่ส่งผลต่อจำนวนเหรียญ หรือบล็อกการโจมตี ก่อนเริ่มทอยเหรียญ"""
    a_coins_mod = 0
    d_coins_mod = 0
    is_blocked = False

    # Item 4: Mirage Shield (ป้องกันการโจมตี 100%)
    if getattr(defender, 'item', None) and defender.item.id == 4:
        is_blocked = True
        return a_coins_mod, d_coins_mod, is_blocked # บล็อกแล้วจบเลย ไม่ต้องคำนวณต่อ
        
    # Item 8: Aura of Misfortune (ลดเหรียญศัตรู 1 เหรียญ)
    if getattr(defender, 'item', None) and defender.item.id == 8:
        a_coins_mod -= 1
    if getattr(attacker, 'item', None) and attacker.item.id == 8:
        d_coins_mod -= 1
        
    # Item 2: Clutch Protection (ลบล้างเหรียญฝ่ายรุกทั้งหมด)
    if getattr(defender, 'item', None) and defender.item.id == 2:
        a_coins_mod = -999 # บังคับให้เหลือ 0 แน่นอน
        defender.item = None # ใช้แล้วทิ้ง

    return a_coins_mod, d_coins_mod, is_blocked

def apply_post_crash_effects(board_obj, attacker, defender, attacker_died, sr, sc, er, ec):
    """คำนวณเอฟเฟกต์หลังจากรู้ผลแพ้ชนะแล้ว (เช่น ตายเกิดใหม่, หักแต้มถาวร, โบนัสชนะ)"""
    from logic.pieces import Pawn
    import random
    
    # ✨ ฟังก์ชันย่อยสำหรับสุ่มหาช่องว่างบนกระดาน (ไม่เอาช่องที่กำลังตีกัน)
    def get_random_empty_square():
        empty_squares = []
        for r in range(8):
            for c in range(8):
                if board_obj.board[r][c] is None and (r, c) not in [(sr, sc), (er, ec)]:
                    empty_squares.append((r, c))
        return random.choice(empty_squares) if empty_squares else None

    # --- กรณีฝ่ายรุกตาย (Attacker died) ---
    if attacker_died:
        board_obj.handle_item_drop(defender, attacker)
        
        # Item 3: Bloodlust Emblem (ฝ่ายรับชนะ ได้ Base Point +5 ถาวร)
        if getattr(defender, 'item', None) and defender.item.id == 3:
            defender.base_points += 5
            defender.item = None
            
        # Item 7: Armor of Thorns (ฝ่ายรุกตาย ฝ่ายรับโดนหัก Coin ถาวร)
        if getattr(attacker, 'item', None) and attacker.item.id == 7:
            defender.coins = max(0, defender.coins - 1)
            
        # Item 1: Totem of Hollow Life (รอดตาย แต่ Base Point เหลือ 0)
        if getattr(attacker, 'item', None) and attacker.item.id == 1:
            attacker.item = None
            attacker.base_points = 0
            return "survived"
            
        # Item 5: Scythe of the Substitute (ตายแล้วทิ้งเบี้ยตัวแทนไว้ในพื้นที่ว่าง)
        elif getattr(attacker, 'item', None) and attacker.item.id == 5:
            attacker.item = None
            rand_pos = get_random_empty_square()
            if rand_pos:
                rr, rc = rand_pos
                board_obj.board[rr][rc] = Pawn(attacker.color, getattr(attacker, 'tribe', 'medieval'))
            return "died"
        else:
            board_obj.board[sr][sc] = None # ตายปกติ
            return "died"
            
    # --- กรณีฝ่ายรุกชนะ (Defender died) ---
    else:
        board_obj.handle_item_drop(attacker, defender)
        
        # Item 3: Bloodlust Emblem
        if getattr(attacker, 'item', None) and attacker.item.id == 3:
            attacker.base_points += 5
            attacker.item = None
            
        # Item 7: Armor of Thorns 
        if getattr(defender, 'item', None) and defender.item.id == 7:
            attacker.coins = max(0, attacker.coins - 1)

        # Item 1: Totem of Hollow Life
        if getattr(defender, 'item', None) and defender.item.id == 1:
            defender.item = None
            defender.base_points = 0
            return "defender_survived" 
            
        # Item 5: Scythe of the Substitute (ตายแล้วทิ้งเบี้ยตัวแทนไว้ในพื้นที่ว่าง)
        elif getattr(defender, 'item', None) and defender.item.id == 5:
            defender.item = None
            rand_pos = get_random_empty_square()
            if rand_pos:
                rr, rc = rand_pos
                board_obj.board[rr][rc] = Pawn(defender.color, getattr(defender, 'tribe', 'medieval')) 
            return "defender_died"
        else:
            return "defender_died"