# components/passive/ayothaya_tribe.py

class AyothayaTribe:
    """Ayothaya tribe passive configuration (อิงตาม Stats ของเพื่อน)"""
    
    def __init__(self):
        self.tribe_name = "ayothaya"
        # ✨ นำค่า Starting Points และ Coin Tosses มาจากโค้ดของเพื่อนทั้งหมด
        # พร้อมเพิ่ม Max Points เพื่อให้ระบบ Crash ทำงานได้อย่างสมบูรณ์
        self.piece_passives = {
            "pawn":   {"starting_points": 2, "coin_tosses": 2, "max_points": 14},
            "knight": {"starting_points": 2, "coin_tosses": 3, "max_points": 20},
            "bishop": {"starting_points": 3, "coin_tosses": 2, "max_points": 15},
            "rook":   {"starting_points": 2, "coin_tosses": 1, "max_points": 8},
            "queen":  {"starting_points": 1, "coin_tosses": 7, "max_points": 43}, # ✨ โหดมาก ทอย 7 เหรียญ
            "king":   {"starting_points": 3, "coin_tosses": 2, "max_points": 15}
        }
    
    def get_piece_passive(self, piece_type):
        return self.piece_passives.get(piece_type.lower(), {})
    
    def get_starting_points(self, piece_type):
        passive = self.get_piece_passive(piece_type)
        return passive.get("starting_points", 0)
    
    def get_coin_tosses(self, piece_type):
        passive = self.get_piece_passive(piece_type)
        return passive.get("coin_tosses", 0)

    def get_max_points(self, piece_type):
        """ดึงค่าแต้มสูงสุดสำหรับใช้ในระบบ Crash"""
        passive = self.get_piece_passive(piece_type)
        return passive.get("max_points", 20)