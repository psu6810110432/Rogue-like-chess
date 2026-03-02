# components/chess_square.py
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Ellipse

class ChessSquare(Button):
    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row, self.col = row, col
        
        # ปิดการแสดงสีพื้นหลังแบบปุ่มปกติของ Kivy ทิ้งไป
        self.background_normal = '' 
        self.background_down = ''
        
        # เตรียมตัวแสดงรูปหมาก
        self.piece_img = Image(fit_mode='contain', opacity=0)
        self.add_widget(self.piece_img)
        
        # เตรียมตัวแสดง passive แฝง
        self.passive_indicator = Label(
            font_size='12sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(22, 22),
            opacity=0
        )
        self.add_widget(self.passive_indicator)
        
        self.is_last_move = False
        self.is_legal = False
        
        # ตั้งค่าสีเริ่มต้น (จะกลายเป็นช่องใส)
        self.update_square_style()
        
        self.bind(pos=self.sync_layout, size=self.sync_layout)

    def sync_layout(self, *args):
        """จัดตำแหน่งรูปหมากและวาดเส้นขอบนีออน (Neon UI)"""
        self.piece_img.size = (self.width * 0.85, self.height * 0.85)
        self.piece_img.center = self.center
        
        # จัดตำแหน่ง passive indicator
        if hasattr(self, 'passive_indicator'):
            self.passive_indicator.pos = (self.x + self.width - 26, self.y + self.height - 26)
            # เพิ่มเงาให้ passive indicator
            self.passive_indicator.canvas.before.clear()
            with self.passive_indicator.canvas.before:
                Color(0, 0, 0, 0.5)
                Ellipse(pos=(self.passive_indicator.x - 1, self.passive_indicator.y - 1), 
                       size=(self.passive_indicator.width + 2, self.passive_indicator.height + 2))
        
        self.canvas.after.clear()
        with self.canvas.after:
            if self.is_legal:
                Color(0.1, 1, 0.1, 1) 
                Line(rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2), width=3)
            elif self.is_last_move:
                Color(1, 0.5, 0, 1) 
                Line(rectangle=(self.x, self.y, self.width, self.height), width=2.5)

    def update_square_style(self, highlight=False, is_legal=False, is_check=False, is_last=False):
        """อัปเดตสีพื้นหลังและสถานะของช่อง"""
        self.is_last_move = is_last
        self.is_legal = is_legal
        
        # ✨ เปลี่ยนสีพื้นหลังปกติให้เป็น "สีใส" (Alpha = 0)
        if is_check: 
            self.background_color = (1, 0.2, 0.2, 0.8) # ราชาโดนรุก (แดงโปร่งแสง)
        elif highlight: 
            self.background_color = (1, 1, 0, 0.6) # เลือกหมาก (เหลืองโปร่งแสง)
        else:
            # ไม่ได้เลือกอะไรเลย ให้โปร่งใส 100% เพื่อโชว์รูปภาพพื้นหลังด่าน
            self.background_color = (0, 0, 0, 0) 
            
        self.sync_layout()

    # ✨ ฟังก์ชันนี้คือจุดที่มีปัญหา แก้ไขให้รับค่า is_frozen แล้ว
    def set_piece_icon(self, path, is_frozen=False, piece=None):
        """แสดงรูปภาพหมากตาม Path ที่ส่งมา และปรับเป็นสีฟ้าถ้าโดนแช่แข็ง"""
        if path:
            self.piece_img.source = path
            self.piece_img.opacity = 1
            
            # แสดง passive แฝงถ้ามี
            self.show_hidden_passive(piece)
            
            # ✨ ถ้าติดแช่แข็งให้ปรับสีตัวหมากให้เข้มขึ้น และใส่สีพื้นหลังช่อง
            if is_frozen:
                # เปลี่ยนตัวหมากให้เป็นสีน้ำเงินเข้ม/ฟ้าเข้ม 
                self.piece_img.color = (0.2, 0.6, 1, 1)  
                
                # ซ้อนสีพื้นหลังช่องให้เป็นสีฟ้าโปร่งแสง เพื่อให้สังเกตง่ายขึ้น
                if self.background_color == [0, 0, 0, 0]: # ถ้าช่องปกติ (ไม่ได้ถูกเลือกหรือโดนรุก)
                    self.background_color = (0, 0.5, 1, 0.4) 
            else:
                self.piece_img.color = (1, 1, 1, 1) # หมากสีปกติ
                # คืนค่าพื้นหลังช่องกลับเป็นโปร่งใส (ถ้าไม่ได้ติด highlight หรือ check)
                if self.background_color == [0, 0.5, 1, 0.4]: 
                    self.background_color = (0, 0, 0, 0)
        else: 
            self.piece_img.opacity = 0
            self.piece_img.color = (1, 1, 1, 1)
            # ซ่อน passive indicator เมื่อไม่มีหมาก
            if hasattr(self, 'passive_indicator'):
                self.passive_indicator.opacity = 0
            # รีเซ็ตสีพื้นหลังกรณีหมากตาย/หายไปจากช่อง
            if self.background_color == [0, 0.5, 1, 0.4]: 
                self.background_color = (0, 0, 0, 0)
    
    def show_hidden_passive(self, piece):
        """แสดง passive แฝงของหมาก"""
        if not piece or not hasattr(piece, 'hidden_passive'):
            if hasattr(self, 'passive_indicator'):
                self.passive_indicator.opacity = 0
            return
            
        passive_info = piece.hidden_passive.get_passive_info()
        
        if passive_info['type'] is None:
            # ไม่มี passive แฝง
            self.passive_indicator.opacity = 0
            return
        
        # กำหนดสีและข้อความตามประเภท passive
        if 'buff' in passive_info['type']:
            self.passive_indicator.color = (0.1, 0.9, 0.1, 1)  # เขียวเข้มสำหรับ buff
            if passive_info['type'] == 'buff1':
                self.passive_indicator.text = '+C'  # Coin buff
            else:  # buff2
                self.passive_indicator.text = '+P'  # Point buff
        else:  # debuff - ทำให้โดดเงามากขึ้น
            self.passive_indicator.color = (1, 0.1, 0.1, 1)  # แดงเข้มมากสำหรับ debuff
            if passive_info['type'] == 'debuff1':
                self.passive_indicator.text = '-C'  # Coin debuff
            else:  # debuff2
                self.passive_indicator.text = '-P'  # Point debuff
        
        self.passive_indicator.opacity = 1