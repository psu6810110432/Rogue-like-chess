class MedievalTribe:
    """Medieval tribe passive configuration"""
    
    def __init__(self):
        self.tribe_name = "medieval"
        self.piece_passives = {
            "pawn": {
                "starting_points": 2,
                "coin_tosses": 1
            },
            "knight": {
                "starting_points": 2,
                "coin_tosses": 1
            }
        }
    
    def get_piece_passive(self, piece_type):
        """Get passive configuration for specific piece"""
        return self.piece_passives.get(piece_type.lower(), {})
    
    def get_starting_points(self, piece_type):
        """Get starting points for specific piece"""
        passive = self.get_piece_passive(piece_type)
        return passive.get("starting_points", 0)
    
    def get_coin_tosses(self, piece_type):
        """Get number of coin tosses for specific piece"""
        passive = self.get_piece_passive(piece_type)
        return passive.get("coin_tosses", 0)