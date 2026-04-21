# components/passive/medieval_tribe.py
class MedievalTribe:
    def __init__(self):
        self.tribe_name = "the knight company"
        self.piece_passives = {
            # --- Classic Mode ---
            "pawn_classic":   {"starting_points": 2, "coin_tosses": 1, "description": "Apprentice Knight: Stable base power."},
            "knight_classic": {"starting_points": 1, "coin_tosses": 2, "description": "Cavalry Knight: Fast and balanced movement."},
            "bishop_classic": {"starting_points": 2, "coin_tosses": 1, "description": "Priest: Consistent diagonal attack power."},
            "rook_classic":   {"starting_points": 2, "coin_tosses": 1, "description": "Fortress: Reliable defense and impact."},
            "queen_classic":  {"starting_points": 3, "coin_tosses": 1, "description": "Iron Queen: Highest starting points in the tribe."},
            "king_classic":   {"starting_points": 2, "coin_tosses": 1, "description": "King: Ultimate defense when cornered."},

            # --- Divide and Conquer (DNC) Mode ---
            "praetorian_dnc": {"coin_tosses": 2, "base_ATK": 2, "base_DEF": 1, "description": "Veteran Elite: Disciplined and highly consistent in offense."},
            "royalguard_dnc": {"coin_tosses": 2, "base_ATK": 0, "base_DEF": 2, "description": "Tower Guard: Heavily armored, prioritizing reliable defense."},
            "menatarm_dnc":   {"coin_tosses": 1, "base_ATK": 3, "base_DEF": 3, "description": "Seasoned Fighter: Perfectly balanced and completely dependable."},
            "prince_dnc":     {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Noble Commander: Leads with calculated and stable tactics."},
            "king_dnc":       {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Liege Lord: A steadfast ruler anchoring the company's morale."},
            "princess_dnc":   {"coin_tosses": 1, "base_ATK": 3, "base_DEF": 3, "description": "Warrior Princess: Highly trained, delivering precise strikes."},
            "queen_dnc":      {"coin_tosses": 1, "base_ATK": 3, "base_DEF": 3, "description": "Grand Strategist: The most reliable and powerful force."},
            "pawn_dnc":       {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Trained Footman: Standard, reliable infantry of the company."},
            "levies_dnc":     {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Conscripted Guard: Basic but dependable local defenders."},
            "hastati_dnc":    {"coin_tosses": 1, "base_ATK": 1, "base_DEF": 4, "description": "Iron Shield: Forms an impenetrable, consistent defensive line."},
            "knight_dnc":     {"coin_tosses": 2, "base_ATK": 2, "base_DEF": 1, "description": "Armored Cavalry: Swift strikes with a slight tactical variance."},
            "bishop_dnc":     {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Company Cleric: Provides steady, calculated support."},
            "rook_dnc":       {"coin_tosses": 1, "base_ATK": 2, "base_DEF": 2, "description": "Stone Bastion: A rock-solid defensive structure."}
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