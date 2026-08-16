# components/piece_card.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window

class PieceCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece, image_path, on_select, **kwargs):
        super().__init__(**kwargs)
        # กำหนดขนาดของการ์ด
        self.size_hint = (None, None)
        self.size = (dp(140), dp(200))
        
        self.piece = piece
        self.on_select_callback = on_select
        self.is_selected = False
        
        # 🎨 1. พื้นหลังการ์ด (Background)
        with self.canvas.before:
            if piece.color == 'white':
                Color(0.9, 0.9, 0.9, 0.95) # สีขาวสว่าง
                self.text_color = (0.1, 0.1, 0.1, 1)
            else:
                Color(0.15, 0.15, 0.15, 0.95) # สีดำเข้ม
                self.text_color = (0.9, 0.9, 0.9, 1)
                
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            
            # เส้นขอบการ์ด (Border)
            Color(0.83, 0.68, 0.21, 1) # สีขอบทองๆ
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=dp(1.5))
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # 🖼️ 2. รูปตัวละคร (Center Image)
        self.piece_img = Image(source=image_path, size_hint=(0.7, 0.45), pos_hint={'center_x': 0.5, 'top': 0.95})
        self.add_widget(self.piece_img)
        
        # 🎒 3. ไอเทมมุมขวาบน (Item Slot Top-Right)
        item_obj = getattr(piece, 'item', None)
        if item_obj and hasattr(item_obj, 'image_path'):
            self.item_img = Image(source=item_obj.image_path, size_hint=(0.25, 0.25), pos_hint={'right': 0.95, 'top': 0.95})
            self.add_widget(self.item_img)
        
        # 📊 4. สเตตัสและข้อมูล (Bottom Info)
        info_box = BoxLayout(orientation='vertical', size_hint=(0.9, 0.45), pos_hint={'center_x': 0.5, 'y': 0.02})
        
        # ชื่อตัวหมาก
        name = getattr(piece, 'name', piece.__class__.__name__)
        info_box.add_widget(Label(
            text=f"[b]{name}[/b]", markup=True, color=self.text_color, 
            font_size='14sp', size_hint_y=0.25
        ))
        
        # ค่าสถานะ (ถ้ามี)
        hp = getattr(piece, 'hp', 1)
        coins = getattr(piece, 'coins', 0)
        stats_text = f"Points: {hp} | Coins: {coins}"
        info_box.add_widget(Label(
            text=stats_text, color=self.text_color, 
            font_size='11sp', size_hint_y=0.2
        ))
        
        # ความสามารถพิเศษ (Passive)
        passive = getattr(piece, 'passive_desc', "No passive skill")
        info_box.add_widget(Label(
            text=passive, color=self.text_color, font_size='9sp', 
            text_size=(dp(120), None), halign='center', valign='top', size_hint_y=0.55
        ))
        
        self.add_widget(info_box)

        # ผูกระบบ Hover เมาส์ชี้แล้วการ์ดเด้ง
        Window.bind(mouse_pos=self.on_mouse_hover)
        self.base_y = 0 # ตำแหน่งตั้งต้นของการ์ด

    def update_graphics(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(12))

    # 🖱️ ระบบ Hover เมาส์
    def on_mouse_hover(self, window, pos):
        if not self.get_root_window() or self.is_selected: 
            return
        
        # เช็คว่าเมาส์อยู่ในกรอบของการ์ดใบนี้ไหม
        is_hovering = self.collide_point(*self.to_widget(*pos))
        
        if is_hovering:
            Animation(y=self.base_y + dp(15), duration=0.1).start(self)
            self.border.width = dp(2.5) # ขอบหนาขึ้นตอนชี้
        else:
            Animation(y=self.base_y, duration=0.1).start(self)
            self.border.width = dp(1.5)

    # 👆 ระบบเมื่อคลิกการ์ด
    def on_release(self):
        self.is_selected = True
        Animation(y=self.base_y + dp(30), duration=0.15, transition='out_bounce').start(self)
        self.border.width = dp(3.0)
        if self.on_select_callback:
            self.on_select_callback(self)
            
    # สั่งยกเลิกการเลือก
    def deselect(self):
        self.is_selected = False
        Animation(y=self.base_y, duration=0.15).start(self)
        self.border.width = dp(1.5)