class HeavenTribe:
    def __init__(self):
        self.tribe_name = "heaven"
        self.piece_passives = {
            "pawn":   {"starting_points": 0, "coin_tosses": 3, "max_points": 6},
            "knight": {"starting_points": 0, "coin_tosses": 6, "max_points": 12},
            "bishop": {"starting_points": 0, "coin_tosses": 8, "max_points": 14},
            "rook":   {"starting_points": 0, "coin_tosses": 6, "max_points": 12},
            "queen":  {"starting_points": 0, "coin_tosses": 5, "max_points": 8},
            "king":   {"starting_points": 0, "coin_tosses": 6, "max_points": 12}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)