from .medieval_tribe import MedievalTribe
from .demon_tribe import DemonTribe

class PassiveManager:
    """Manager for handling passive abilities of different tribes"""
    
    def __init__(self):
        self.tribes = {
            'medieval': MedievalTribe(),
            'demon': DemonTribe()
        }
    
    @classmethod
    def get_passive_handler(cls, piece_type, tribe):
        """Get passive handler for specific piece and tribe"""
        instance = cls()
        tribe_handler = instance.tribes.get(tribe.lower())
        
        if not tribe_handler:
            return None
            
        return {
            'get_piece_stats': lambda: {
                'dice': tribe_handler.get_starting_points(piece_type),
                'coins': tribe_handler.get_coin_tosses(piece_type)
            },
            'get_valid_moves': None  # สำหรับ future implementation
        }
    
    @classmethod
    def get_default_stats(cls, piece_type, tribe):
        """Get default stats when tribe is not implemented yet"""
        # ยังไม่มีการ implement เผ่าอื่นๆ ให้คืนค่า None
        return None