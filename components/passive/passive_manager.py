# components/passive/passive_manager.py
from .medieval_tribe import MedievalTribe
from .demon_tribe import DemonTribe
from .heaven_tribe import HeavenTribe
from .ayothaya_tribe import AyothayaTribe

class PassiveManager:
    # Pre-loading instances to avoid re-creation
    _instances = {
        'the knight company': MedievalTribe(),
        'the deep anomaly': DemonTribe(),
        'the ancient runes': HeavenTribe(),
        'the chaos mankind': AyothayaTribe(),
        'bandit': AyothayaTribe() # ใช้ระบบทอยแบบ ayothaya ไปก่อน
    }
    
    @classmethod
    def get_passive_handler(cls, piece_type, tribe):
        handler = cls._instances.get(tribe.lower())
        if not handler: return None
        return {
            'get_piece_stats': lambda: {
                'dice': handler.get_starting_points(piece_type),
                'coins': handler.get_coin_tosses(piece_type),
                'max': handler.get_max_points(piece_type),
                'desc': handler.get_description(piece_type)
            }
        }