# Passive Manager - จัดการ passive abilities ของทุกเผ่า
from components.passive.medieval_tribe import medieval_knight_passive

class PassiveManager:
    """จัดการ passive abilities ของแต่ละเผ่า"""
    
    @staticmethod
    def get_passive_handler(piece_type, tribe):
        """คืนค่า passive handler สำหรับ piece และ tribe ที่กำหนด"""
        passive_map = {
            ('knight', 'medieval'): medieval_knight_passive
        }
        
        key = (piece_type.lower(), tribe.lower())
        passive_func = passive_map.get(key)
        
        if passive_func:
            return passive_func()
        else:
            return None
    
    @staticmethod
    def get_default_stats(piece_type, tribe):
        """คืนค่าสถานะเริ่มต้นสำหรับ piece และ tribe ที่กำหนด"""
        passive = PassiveManager.get_passive_handler(piece_type, tribe)
        if passive:
            return passive['get_piece_stats']()
        else:
            # ค่าเริ่มต้นสำหรับ piece ทั่วไป
            return {
                'dice': 2,
                'coins': 2
            }
