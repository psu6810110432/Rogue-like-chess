class MedievalTribe:
    def __init__(self):
        self.tribe_name = "medieval"
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "อัศวินฝึกหัด: พลังพื้นฐานที่มั่นคง"},
            "knight": {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "อัศวินม้า: เคลื่อนที่รวดเร็วและสมดุล"},
            "bishop": {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "นักบวช: พลังโจมตีแนวทแยงที่สม่ำเสมอ"},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 12, "description": "ป้อมปราการ: การป้องกันและพลังทำลายที่แน่นอน"},
            "queen":  {"starting_points": 3, "coin_tosses": 1, "max_points": 13, "description": "ราชินีเหล็ก: มีแต้มตั้งต้นสูงสุดในเผ่า"},
            "king":   {"starting_points": 1, "coin_tosses": 2, "max_points": 21, "description": "กษัตริย์: พลังป้องกันสูงสุดเมื่อเข้าตาจน"}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")