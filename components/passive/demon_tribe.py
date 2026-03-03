class DemonTribe:
    def __init__(self):
        self.tribe_name = "demon"
        self.piece_passives = {
            "pawn":   {"starting_points": 0, "coin_tosses": 2, "max_points": 6},
            "knight": {"starting_points": 0, "coin_tosses": 3, "max_points": 12},
            "bishop": {"starting_points": 0, "coin_tosses": 3, "max_points": 12},
            "rook":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12},
            "queen":  {"starting_points": 0, "coin_tosses": 4, "max_points": 16},
            "king":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)