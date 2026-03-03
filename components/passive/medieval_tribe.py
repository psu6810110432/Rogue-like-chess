# components/passive/medieval_tribe.py
class MedievalTribe:
    def __init__(self):
        self.tribe_name = "medieval"
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "Apprentice Knight: Stable base power."},
            "knight": {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "Cavalry Knight: Fast and balanced movement."},
            "bishop": {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "Priest: Consistent diagonal attack power."},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "Fortress: Reliable defense and impact."},
            "queen":  {"starting_points": 3, "coin_tosses": 1, "max_points": 13, "description": "Iron Queen: Highest starting points in the tribe."},
            "king":   {"starting_points": 1, "coin_tosses": 2, "max_points": 21, "description": "King: Ultimate defense when cornered."}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")