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
from kivy.uix.widget import Widget

# ✨ 1. Import PassiveManager เข้ามาเพื่อดึงข้อมูล Base Stats และ Passive
from components.passive.passive_manager import PassiveManager

class PieceCard(ButtonBehavior, FloatLayout):
    # ✨ 2. เพิ่มพารามิเตอร์ game_mode และ tribe_name
    def __init__(self, piece, image_path, on_select, game_mode="classic", tribe_name="the knight company", is_deployed=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(140), dp(200))
        
        self.piece = piece
        self.on_select_callback = on_select
        self.is_selected = False
        
        # 🎨 พื้นหลังการ์ด
        with self.canvas.before:
            if piece.color == 'white':
                Color(0.9, 0.9, 0.9, 0.95)
                self.text_color = (0.1, 0.1, 0.1, 1)
            else:
                Color(0.15, 0.15, 0.15, 0.95)
                self.text_color = (0.9, 0.9, 0.9, 1)
                
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            # ✨ เก็บตัวแปรสีขอบเอาไว้ เพื่อให้แก้สีตอนคลิกได้
            self.border_color = Color(0.83, 0.68, 0.21, 1) 
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=dp(1.5))
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # 🖼️ รูปตัวละคร
        self.piece_img = Image(source=image_path, size_hint=(0.7, 0.45), pos_hint={'center_x': 0.5, 'top': 0.95})
        self.add_widget(self.piece_img)
        
        # 🎒 3. ไอคอนมุมขวาบน (เรียงเป็นคอลัมน์: Passive -> Hidden -> Item)
        # ใช้ BoxLayout แนวตั้ง (vertical) เพื่อให้ภาพต่อกันลงมาเรื่อยๆ
        import os # อย่าลืม import os ไว้ด้านบนสุดของไฟล์ด้วยนะครับ
        icon_box = BoxLayout(orientation='vertical', size_hint=(0.25, 0.6), pos_hint={'right': 0.95, 'top': 0.95}, spacing=dp(5))
        
        # 3.1 ไอคอนประจำเผ่า
        if getattr(piece, 'passive_icon', None) and os.path.exists(piece.passive_icon):
            icon_box.add_widget(Image(source=piece.passive_icon, size_hint_y=None, height=dp(25)))
            
        # 3.2 ไอคอน Hidden Passive
        hidden_passive = getattr(piece, 'hidden_passive', None)
        if hidden_passive and getattr(hidden_passive, 'passive_type', None):
            # ✨ แปลงชื่อให้ตรงกับไฟล์ในโฟลเดอร์ icon_effect
            desc = hidden_passive.description.lower().replace(" ", "_")
            hp_icon = f"assets/icon_effect/{desc}.png"
            
            if os.path.exists(hp_icon):
                icon_box.add_widget(Image(source=hp_icon, size_hint_y=None, height=dp(25)))
                
        # 3.3 ไอคอน Item
        item_obj = getattr(piece, 'item', None)
        if item_obj and hasattr(item_obj, 'image_path') and os.path.exists(item_obj.image_path):
            icon_box.add_widget(Image(source=item_obj.image_path, size_hint_y=None, height=dp(25)))
            
        # ใส่กล่องเปล่าด้านล่างสุด ดันให้ไอคอนทั้งหมดไปชิดขอบบน
        icon_box.add_widget(Widget(size_hint_y=1))
        self.add_widget(icon_box)
        
        # ==========================================
        # 📊 สเตตัสและข้อมูล (ดึงแยกตามโหมด DNC / Classic)
        # ==========================================
        info_box = BoxLayout(orientation='vertical', size_hint=(0.9, 0.45), pos_hint={'center_x': 0.5, 'y': 0.02})
        
        class_name = piece.__class__.__name__.upper()
        info_box.add_widget(Label(
            text=f"[b]{class_name}[/b]", markup=True, color=self.text_color, 
            font_size='14sp', size_hint_y=0.25
        ))
        
        piece_type = piece.__class__.__name__.lower()
        handler = PassiveManager.get_passive_handler(piece_type, tribe_name)
        mode_key = "dnc" if game_mode == 'Divide_Conquer' else "classic"
        stats_dict = handler['get_piece_stats'](mode_key) if handler else {}
        
        current_coins = getattr(piece, 'coins', stats_dict.get('coins', 0)) 
        
        if mode_key == "dnc":
            current_atk = getattr(piece, 'atk', stats_dict.get('base_atk', 0))
            current_def = getattr(piece, 'hp', stats_dict.get('base_def', 0))
            # ✨ เพิ่มสถานะกำกับในการ์ด ว่าทหารลงสนามไปหรือยัง
            status_txt = "[color=44ff44]DEPLOYED[/color]" if is_deployed else "[color=ffaa00]STANDBY[/color]"
            stats_text = f"ATK: {current_atk} | DEF: {current_def}\n{status_txt}"
        else:
            current_pts = getattr(piece, 'hp', stats_dict.get('dice', 0))
            stats_text = f"Points: {current_pts} | Coins: {current_coins}"
            
        info_box.add_widget(Label(
            text=stats_text, color=self.text_color, 
            font_size='11sp', size_hint_y=0.3, markup=True
        ))
        
        # 3. ความสามารถพิเศษ (Passive Description)
        passive_desc = stats_dict.get('desc', "No passive skill")
        
        # ✨ เพิ่มข้อความบอก Hidden Passive ลงในการ์ด[cite: 12]
        hidden_text = ""
        if hidden_passive and hidden_passive.passive_type:
            hp_info = hidden_passive.get_passive_info()
            # ใช้สีเขียวสำหรับคำว่า buff และแดงสำหรับคำว่า debuff
            color_hex = "44FF44" if "buff" in hidden_passive.passive_type else "ff4444"
            modifier = hp_info.get('modifier', '')
            hidden_text = f"\n[color={color_hex}][Hidden] {hp_info['description']} ({modifier})[/color]"
            
        info_box.add_widget(Label(
            text=passive_desc + hidden_text, 
            color=self.text_color, font_size='9sp', 
            text_size=(dp(120), None), halign='center', valign='top', size_hint_y=0.55,
            markup=True # จำเป็นต้องเปิด markup เพื่อรองรับการทำสีข้อความ
        ))
        
        self.add_widget(info_box)

        # ผูกระบบ Hover เมาส์ชี้แล้วการ์ดเด้ง
        Window.bind(mouse_pos=self.on_mouse_hover)
        self.base_y = 0 

    def update_graphics(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(12))

    def on_mouse_hover(self, window, pos):
        if not self.get_root_window() or self.is_selected: return
        is_hovering = self.collide_point(*self.to_widget(*pos))
        if is_hovering:
            Animation(y=self.base_y + dp(15), duration=0.1).start(self)
            self.border.width = dp(2.5)
        else:
            Animation(y=self.base_y, duration=0.1).start(self)
            self.border.width = dp(1.5)

    def on_release(self):
        self.is_selected = True
        Animation(y=self.base_y + dp(30), duration=0.15, transition='out_bounce').start(self)
        self.border.width = dp(3.0)
        self.border_color.rgba = (0.2, 0.9, 0.2, 1)
        if self.on_select_callback:
            self.on_select_callback(self)
            
    def deselect(self):
        self.is_selected = False
        Animation(y=self.base_y, duration=0.15).start(self)
        self.border.width = dp(1.5)
        self.border_color.rgba = (0.83, 0.68, 0.21, 1)

    def set_selected_visuals(self):
        """ตั้งค่าให้การ์ดเรืองแสงสีเขียวและลอยขึ้นทันทีเมื่อถูกสร้างใหม่"""
        self.is_selected = True
        self.border.width = dp(3.0)
        self.border_color.rgba = (0.2, 0.9, 0.2, 1) # เปลี่ยนเป็นขอบสีเขียว
        Animation(y=self.base_y + dp(30), duration=0.0).start(self)