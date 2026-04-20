# components/passive/heaven_tribe.py
class HeavenTribe:
    def __init__(self):
        self.tribe_name = "the ancient runes"
        self.piece_passives = {
            "pawn":   {"starting_points": 3, "coin_tosses": 6, "max_points": 6, "description": "Messenger: Relies on faith for coin tosses."},
            "knight": {"starting_points": 1, "coin_tosses": 8, "max_points": 12, "description": "Heavenly Guardian: Highly variable fate (6 tosses)."},
            "bishop": {"starting_points": 0, "coin_tosses": 11, "max_points": 14, "description": "Saint: Up to 8 coin tosses for miracle power."},
            "rook":   {"starting_points": 1, "coin_tosses": 8, "max_points": 12, "description": "Heavenly Pillar: Stable with high coin count."},
            "queen":  {"starting_points": 3, "coin_tosses": 6, "max_points": 8, "description": "Goddess: Focuses on precision over destruction."},
            "king":   {"starting_points": 3, "coin_tosses": 6, "max_points": 12, "description": "God King: Fate rests entirely on faith."}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return 999  # ปิดการใช้งาน max point
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")
