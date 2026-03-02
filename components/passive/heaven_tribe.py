class HeavenTribe:
    """Heaven tribe passive configuration"""
    
    def __init__(self):
        self.tribe_name = "heaven"
        self.piece_passives = {
            "pawn": {
                "starting_points": 0,
                "coin_tosses": 3
            },
            "knight": {
                "starting_points": 0,
                "coin_tosses": 6
            },
            "bishop": {
                "starting_points": 0,
                "coin_tosses": 8
            },
            "rook": {
                "starting_points": 0,
                "coin_tosses": 6
            },
            "queen": {
                "starting_points": 0,
                "coin_tosses": 5
            },
            "king": {
                "starting_points": 0,
                "coin_tosses": 6
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
