# components/passive/demon_tribe.py
class DemonTribe:
    def __init__(self):
        self.tribe_name = "the deep anomaly"
        self.piece_passives = {
            # --- Classic Mode ---
            "pawn_classic":   {"starting_points": 0, "coin_tosses": 3, "description": "Demon Minion: Unpredictable attack power."},
            "knight_classic": {"starting_points": 0, "coin_tosses": 3, "description": "Dark Knight: Risk-taker for massive damage."},
            "bishop_classic": {"starting_points": 0, "coin_tosses": 3, "description": "Dark Mage: Focuses on random destruction."},
            "rook_classic":   {"starting_points": 2, "coin_tosses": 4, "description": "Infernal Fortress: Luck-based defense."},
            "queen_classic":  {"starting_points": 0, "coin_tosses": 3, "description": "Demon Queen: Peak power upon successful tosses."},
            "king_classic":   {"starting_points": 0, "coin_tosses": 3, "description": "Demon King: Mastermind from the shadows."},

            # --- Divide and Conquer (DNC) Mode ---
            "praetorian_dnc": {"coin_tosses": 4, "base_ATK": 2, "base_DEF": 0, "description": "Void Elite: High variance with an aggressive edge."},
            "royalguard_dnc": {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 2, "description": "Abyssal Sentinel: Relies on dark anomalies to defend."},
            "menatarm_dnc":   {"coin_tosses": 3, "base_ATK": 1, "base_DEF": 0, "description": "Chaos Vanguard: Sacrifices defense for unpredictable strikes."},
            "prince_dnc":     {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Heir of the Anomaly: A chaotic shadow waiting to emerge."},
            "king_dnc":       {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Demon Sovereign: True power lies entirely in the abyss."},
            "princess_dnc":   {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Daughter of Void: Fragile but capable of sudden, dark bursts."},
            "queen_dnc":      {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Empress of Despair: Pure anomaly, her wrath is unpredictable."},
            "pawn_dnc":       {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Abyssal Crawler: A lowly fiend bound by the whims of fate."},
            "levies_dnc":     {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Corrupted Soul: Formless and completely erratic in combat."},
            "hastati_dnc":    {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 3, "description": "Hellish Phalanx: Uses anomalies to form a sudden dark shield."},
            "knight_dnc":     {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Nightmare Rider: High risk, high reward abyssal cavalry."},
            "bishop_dnc":     {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Void Cultist: Channels the anomaly for erratic dark magic."},
            "rook_dnc":       {"coin_tosses": 3, "base_ATK": 0, "base_DEF": 0, "description": "Pillar of Chaos: An imposing structure fueled by volatile energy."}
        }

    def get_piece_passive(self, piece_type, mode="classic"):
        key = f"{piece_type.lower()}_{mode.lower()}"
        return self.piece_passives.get(key, {})

    def get_starting_points(self, p, mode="classic"): 
        return self.get_piece_passive(p, mode).get("starting_points", 0)

    def get_coin_tosses(self, p, mode="classic"): 
        return self.get_piece_passive(p, mode).get("coin_tosses", 0)

    def get_base_atk(self, p, mode="dnc"):
        return self.get_piece_passive(p, mode).get("base_ATK", 0)

    def get_base_def(self, p, mode="dnc"):
        return self.get_piece_passive(p, mode).get("base_DEF", 0)

    def get_description(self, p, mode="classic"): 
        return self.get_piece_passive(p, mode).get("description", "")