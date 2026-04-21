# components/passive/ayothaya_tribe.py

class AyothayaTribe:
    def __init__(self):
        self.tribe_name = "the chaos mankind"
        self.piece_passives = {
            # --- Classic Mode ---
            "pawn_classic":   {"starting_points": 5, "coin_tosses": 4, "description": "Brave Soldier: Strong base power and determination."},
            "knight_classic": {"starting_points": 5, "coin_tosses": 4, "description": "Atamat Corps: Agile with high impact power."},
            "bishop_classic": {"starting_points": 6, "coin_tosses": 3, "description": "Royal Astrologer: Consistent mystical power."},
            "rook_classic":   {"starting_points": 6, "coin_tosses": 3, "description": "Siam Fortress: Reliable defensive certainty."},
            "queen_classic":  {"starting_points": 4, "coin_tosses": 7, "description": "Female General: Deadly slashes with 7 tosses."},
            "king_classic":   {"starting_points": 4, "coin_tosses": 5, "description": "Lord King: Absolute power and charisma."},

            # --- Divide and Conquer (DNC) Mode ---
            "praetorian_dnc": {"coin_tosses": 7, "base_ATK": 4, "base_DEF": 3, "description": "Elite Guard: Aggressive onslaught with overwhelming strikes."},
            "royalguard_dnc": {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 5, "description": "Palace Protector: Steadfast defenders of the throne."},
            "menatarm_dnc":   {"coin_tosses": 6, "base_ATK": 3, "base_DEF": 3, "description": "Veteran Swordsman: Balanced combatant with battle-hardened skills."},
            "prince_dnc":     {"coin_tosses": 5, "base_ATK": 4, "base_DEF": 4, "description": "Royal Heir: The future leader with unwavering resolve."},
            "king_dnc":       {"coin_tosses": 5, "base_ATK": 4, "base_DEF": 4, "description": "Garrison Commander: Tactical leader holding the line."},
            "princess_dnc":   {"coin_tosses": 7, "base_ATK": 4, "base_DEF": 4, "description": "Royal Daughter: Swift and deadly elegance on the battlefield."},
            "queen_dnc":      {"coin_tosses": 7, "base_ATK": 4, "base_DEF": 4, "description": "Warrior Queen: Commands fear and respect with lethal precision."},
            "pawn_dnc":       {"coin_tosses": 4, "base_ATK": 5, "base_DEF": 5, "description": "Conscripted Militia: Sturdy frontline soldiers holding their ground."},
            "levies_dnc":     {"coin_tosses": 4, "base_ATK": 5, "base_DEF": 5, "description": "Village Volunteers: Courageous locals fighting for their homeland."},
            "hastati_dnc":    {"coin_tosses": 4, "base_ATK": 3, "base_DEF": 6, "description": "Vanguard Spearmen: High defensive capability to absorb charges."},
            "knight_dnc":     {"coin_tosses": 4, "base_ATK": 5, "base_DEF": 5, "description": "Cavalry Raider: Swift and heavy offensive charges."},
            "bishop_dnc":     {"coin_tosses": 3, "base_ATK": 4, "base_DEF": 6, "description": "War Monk: Provides crucial mystical defense and tactical support."},
            "rook_dnc":       {"coin_tosses": 3, "base_ATK": 6, "base_DEF": 4, "description": "Siege Tower: Devastating firepower capable of breaking enemy lines."}
        }

    def get_piece_passive(self, piece_type, mode="classic"):
        # ค้นหาค่าสเตตัสโดยการใช้ชื่อหมากต่อด้วยโหมดที่กำลังเล่นอยู่
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