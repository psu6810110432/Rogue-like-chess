# components/passive/demon_tribe.py
class DemonTribe:
    def __init__(self):
        self.tribe_name = "the deep anomaly"
        self.piece_passives = {
            "pawn":   {"starting_points": 0, "coin_tosses": 3, "max_points": 6, "description": "Demon Minion: Unpredictable attack power."},
            "knight": {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "Dark Knight: Risk-taker for massive damage."},
            "bishop": {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "Dark Mage: Focuses on random destruction."},
            "rook":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "Infernal Fortress: Luck-based defense."},
            "queen":  {"starting_points": 2, "coin_tosses": 4, "max_points": 16, "description": "Demon Queen: Peak power upon successful tosses."},
            "king":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "Demon King: Mastermind from the shadows."}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return 999  # ปิดการใช้งาน max point
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")
