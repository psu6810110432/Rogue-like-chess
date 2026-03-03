class HeavenTribe:
    def __init__(self):
        self.tribe_name = "heaven"
        self.piece_passives = {
            "pawn":   {"starting_points": 0, "coin_tosses": 3, "max_points": 6, "description": "ผู้นำสาร: พึ่งพาแรงศรัทธาในการทอยเหรียญ"},
            "knight": {"starting_points": 0, "coin_tosses": 6, "max_points": 12, "description": "ผู้พิทักษ์สวรรค์: โชคชะตาแปรผันสูงด้วยเหรียญ 6 ครั้ง"},
            "bishop": {"starting_points": 0, "coin_tosses": 8, "max_points": 14, "description": "นักบุญ: ทอยเหรียญสูงสุด 8 ครั้งเพื่อพลังปาฏิหาริย์"},
            "rook":   {"starting_points": 0, "coin_tosses": 6, "max_points": 12, "description": "เสาหลักสวรรค์: มั่นคงด้วยจำนวนเหรียญที่มาก"},
            "queen":  {"starting_points": 0, "coin_tosses": 5, "max_points": 8, "description": "เทวี: เน้นความแม่นยำมากกว่าพลังทำลาย"},
            "king":   {"starting_points": 0, "coin_tosses": 6, "max_points": 12, "description": "เทพราชา: ชะตากรรมขึ้นอยู่กับศรัทธาล้วนๆ"}
        }
    def get_starting_points(self, p): return self.piece_passives.get(p.lower(), {}).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.piece_passives.get(p.lower(), {}).get("coin_tosses", 0)
    def get_max_points(self, p): return self.piece_passives.get(p.lower(), {}).get("max_points", 12)
    def get_description(self, p): return self.piece_passives.get(p.lower(), {}).get("description", "")