# components/passive/heaven_tribe.py
class HeavenTribe:
    def __init__(self):
        self.tribe_name = "the ancient runes"
        self.piece_passives = {
            # --- Classic Mode ---
            "pawn_classic":   {"starting_points": 3, "coin_tosses": 6, "description": "Messenger: Relies on faith for coin tosses."},
            "knight_classic": {"starting_points": 1, "coin_tosses": 8, "description": "Heavenly Guardian: Highly variable fate (6 tosses)."},
            "bishop_classic": {"starting_points": 0, "coin_tosses": 11, "description": "Saint: Up to 8 coin tosses for miracle power."},
            "rook_classic":   {"starting_points": 1, "coin_tosses": 8, "description": "Heavenly Pillar: Stable with high coin count."},
            "queen_classic":  {"starting_points": 3, "coin_tosses": 6, "description": "Goddess: Focuses on precision over destruction."},
            "king_classic":   {"starting_points": 3, "coin_tosses": 6, "description": "God King: Fate rests entirely on faith."},

            # --- Divide and Conquer (DNC) Mode ---
            "praetorian_dnc": {"coin_tosses": 11, "base_ATK": 3, "base_DEF": 1, "description": "Runic Champion: Unleashes massive divine energy (11 tosses)."},
            "royalguard_dnc": {"coin_tosses": 9, "base_ATK": 1, "base_DEF": 3, "description": "Aegis of the Gods: Heavily blessed defender drawing on miracles."},
            "menatarm_dnc":   {"coin_tosses": 7, "base_ATK": 2, "base_DEF": 2, "description": "Holy Crusader: Balanced stats amplified by runic blessings."},
            "prince_dnc":     {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Divine Scion: Strong leadership backed by ancient runes."},
            "king_dnc":       {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Ruler of the Heavens: Commands the field with steady divine grace."},
            "princess_dnc":   {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Sacred Maiden: Graceful and deadly, guided by the heavens."},
            "queen_dnc":      {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Goddess of War: Dominates with high stats and celestial power."},
            "pawn_dnc":       {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Faithful Zealot: Unusually strong conscript empowered by belief."},
            "levies_dnc":     {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Chosen Militia: Commoners blessed with unnatural divine strength."},
            "hastati_dnc":    {"coin_tosses": 6, "base_ATK": 1, "base_DEF": 5, "description": "Celestial Bulwark: An unbreakable wall forged from runic light."},
            "knight_dnc":     {"coin_tosses": 8, "base_ATK": 1, "base_DEF": 1, "description": "Pegasus Lancer: Sweeps the field, relying on divine favor."},
            "bishop_dnc":     {"coin_tosses": 11, "base_ATK": 0, "base_DEF": 0, "description": "High Priest: Pure miracle caster. Fate decides everything."},
            "rook_dnc":       {"coin_tosses": 8, "base_ATK": 1, "base_DEF": 1, "description": "Temple of Light: A grand bastion surging with heavenly magic."}
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