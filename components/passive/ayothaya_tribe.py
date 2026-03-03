class AyothayaTribe:
    def __init__(self):
        self.tribe_name = "ayothaya"
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 2, "max_points": 14, "description": "ทหารกล้า: พลังพื้นฐานดีและมีความมุ่งมั่น"},
            "knight": {"starting_points": 2, "coin_tosses": 3, "max_points": 20, "description": "กองอาทมาต: ว่องไวและมีพลังทำลายสูง"},
            "bishop": {"starting_points": 3, "coin_tosses": 2, "max_points": 15, "description": "พระโหราธิบดี: พลังเวทย์มนตร์ที่มั่นคง"},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 8, "description": "ป้อมปราการสยาม: เน้นความแน่นอนในการป้องกัน"},
            "queen":  {"starting_points": 1, "coin_tosses": 7, "max_points": 43, "description": "แม่ทัพหญิง: พลังทลวงฟันด้วยเหรียญ 7 ครั้ง สูงสุดในเกม"},
            "king":   {"starting_points": 3, "coin_tosses": 2, "max_points": 15, "description": "ขุนหลวง: พลังอำนาจที่เปี่ยมด้วยบารมี"}
        }
    def get_piece_passive(self, piece_type): return self.piece_passives.get(piece_type.lower(), {})
    def get_starting_points(self, p): return self.get_piece_passive(p).get("starting_points", 0)
    def get_coin_tosses(self, p): return self.get_piece_passive(p).get("coin_tosses", 0)
    def get_max_points(self, p): return self.get_piece_passive(p).get("max_points", 20)
    def get_description(self, p): return self.get_piece_passive(p).get("description", "")