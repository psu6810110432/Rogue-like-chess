# components/passive/passive_manager.py
from .medieval_tribe import MedievalTribe
from .demon_tribe import DemonTribe
from .heaven_tribe import HeavenTribe
from .ayothaya_tribe import AyothayaTribe

class PassiveManager:
    @staticmethod
    def get_passive_handler(piece_type, tribe_name):
        handlers = {
            "the knight company": MedievalTribe(),
            "the deep anomaly": DemonTribe(),
            "the ancient runes": HeavenTribe(),
            "the chaos mankind": AyothayaTribe()
        }
        
        handler = handlers.get(tribe_name)
        if handler:
            return {
                # เปลี่ยนให้รองรับการส่งค่าโหมดเข้ามา แต่ถ้าไม่มีจะให้เป็น classic
                'get_piece_stats': lambda mode="classic": {
                    'dice': handler.get_starting_points(piece_type, mode) if hasattr(handler, 'get_starting_points') else 0,
                    'coins': handler.get_coin_tosses(piece_type, mode) if hasattr(handler, 'get_coin_tosses') else 0,
                    'max': 999, # ✨ นำ get_max_points ออก แล้วใส่ 999 ไปเลยเพื่อไม่ให้จำกัดคะแนนสูงสุด
                    'desc': handler.get_description(piece_type, mode) if hasattr(handler, 'get_description') else "",
                    # เสริมการดึงค่า ATK/DEF สำหรับโหมด Divide and Conquer
                    'base_atk': handler.get_base_atk(piece_type, "dnc") if hasattr(handler, 'get_base_atk') else 0,
                    'base_def': handler.get_base_def(piece_type, "dnc") if hasattr(handler, 'get_base_def') else 0
                }
            }
        return None