class MedievalTribe:
    def __init__(self):
        self.tribe_name = "medieval"
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12},
            "knight": {"starting_points": 2, "coin_tosses": 1, "max_points": 12},
            "bishop": {"starting_points": 2, "coin_tosses": 1, "max_points": 12},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12},
            "queen":  {"starting_points": 3, "coin_tosses": 1, "max_points": 13},
            "king":   {"starting_points": 1, "coin_tosses": 2, "max_points": 21}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)