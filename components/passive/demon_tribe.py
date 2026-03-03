class DemonTribe:
    def __init__(self):
        self.tribe_name = "demon"
        self.piece_passives = {
            "pawn":   {"starting_points": 0, "coin_tosses": 2, "max_points": 6, "description": "สมุนปีศาจ: พลังโจมตีที่คาดเดายาก"},
            "knight": {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "อัศวินทมิฬ: พลังที่เสี่ยงดวงเพื่อความรุนแรง"},
            "bishop": {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "จอมเวทย์มนต์ดำ: เน้นการทำลายล้างแบบสุ่ม"},
            "rook":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "ป้อมปราการโลกันตร์: การป้องกันที่พึ่งพาดวง"},
            "queen":  {"starting_points": 0, "coin_tosses": 4, "max_points": 16, "description": "ราชินีปีศาจ: พลังโจมตีสูงสุดเมื่อทอยเหรียญสำเร็จ"},
            "king":   {"starting_points": 0, "coin_tosses": 3, "max_points": 12, "description": "ราชาปีศาจ: ผู้บงการจากเงามืด"}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")