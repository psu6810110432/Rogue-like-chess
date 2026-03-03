# components/passive/ayothaya_tribe.py
class AyothayaTribe:
    def __init__(self):
        self.tribe_name = "ayothaya"
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 2, "max_points": 14, "description": "Brave Soldier: Strong base power and determination."},
            "knight": {"starting_points": 2, "coin_tosses": 3, "max_points": 20, "description": "Atamat Corps: Agile with high impact power."},
            "bishop": {"starting_points": 3, "coin_tosses": 2, "max_points": 15, "description": "Royal Astrologer: Consistent mystical power."},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 8, "description": "Siam Fortress: Reliable defensive certainty."},
            "queen":  {"starting_points": 1, "coin_tosses": 7, "max_points": 43, "description": "Female General: Deadly slashes with 7 tosses."},
            "king":   {"starting_points": 3, "coin_tosses": 2, "max_points": 15, "description": "Lord King: Absolute power and charisma."}
        }
    def get_piece_passive(self, piece_type): return self.piece_passives.get(piece_type.lower(), {})
    def get_starting_points(self, p): return self.get_piece_passive(p).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.get_piece_passive(p).get("coin_tosses", 0)
    def get_max_points(self, p): return self.get_piece_passive(p).get("max_points", 20)
    def get_description(self, p): return self.get_piece_passive(p).get("description", "")