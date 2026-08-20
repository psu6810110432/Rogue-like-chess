# components/map_banner.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Mesh, Line
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window

class MapBanner(ButtonBehavior, FloatLayout):
    def __init__(self, node, city_name, map_screen_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(160)
        self.node = node
        self.city_name = city_name
        self.map_screen = map_screen_ref
        self.is_selected = False
        
        with self.canvas.before:
            # ✨ กำหนดสีตามเงื่อนไข: ขาวขอบดำ, แดงไม่มีขอบ, ดำขอบขาว
            if node.faction == 'white':
                self.bg_color = (0.9, 0.9, 0.9, 0.95)
                text_color = "111111"
                self.border_color = (0.1, 0.1, 0.1, 1)
            elif node.faction == 'black':
                self.bg_color = (0.15, 0.15, 0.15, 0.95)
                text_color = "EEEEEE"
                self.border_color = (0.9, 0.9, 0.9, 1)
            else: # Red (ศัตรู/กบฏ)
                self.bg_color = (0.6, 0.1, 0.15, 0.95) # แดงเลือดหมู
                text_color = "FFFFFF"
                self.border_color = None
            
            self.mesh_color = Color(*self.bg_color)
            self.mesh = Mesh(mode='triangles')
            
            self.line_color = Color(*(self.border_color if self.border_color else (0,0,0,0)))
            self.line = Line(width=dp(1.5)) if self.border_color else None

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # 📝 ข้อมูลเมืองในธง
        info_box = BoxLayout(orientation='vertical', size_hint=(0.9, 0.85), pos_hint={'center_x': 0.5, 'top': 0.95})
        info_box.add_widget(Label(text=f"[b][color={text_color}]{self.city_name}[/color][/b]", markup=True, font_size='15sp', size_hint_y=0.25))
        info_box.add_widget(Label(text=f"[color={text_color}]({node.node_type.upper()})[/color]", markup=True, font_size='11sp', size_hint_y=0.15))
        
        addons_text = ""
        if hasattr(node, 'addons'):
            for k, v in node.addons.items():
                if k == 'special' and isinstance(v, str):
                    lvl = node.addons.get('special_lvl', 1)
                    addons_text += f"- {v.capitalize()} Lv.{lvl}\n"
                elif isinstance(v, int) and k != 'special_lvl' and v > 0:
                    addons_text += f"- {k.capitalize()} Lv.{v}\n"
                    
        if not addons_text.strip(): addons_text = "No Addons"
        
        info_box.add_widget(Label(text=f"[color={text_color}]{addons_text}[/color]", markup=True, font_size='11sp', halign='center', valign='top', size_hint_y=0.6))
        self.add_widget(info_box)

        # ผูก Hover Effect
        Window.bind(mouse_pos=self.on_mouse_hover)

    def update_graphics(self, *args):
        # 🚩 วาดรูปธงปลายแฉก (Swallowtail Flag)
        x, y, w, h = self.x, self.y, self.width, self.height
        cut = dp(25) # ความลึกของแฉกด้านล่าง
        
        # ✨ แก้ไข vertices ให้ส่งแค่ 4 ค่าต่อจุด (x, y, u, v)
        vertices = [
            x, y+h, 0, 0,        # จุด 0: บนซ้าย
            x+w, y+h, 0, 0,      # จุด 1: บนขวา
            x+w, y, 0, 0,        # จุด 2: ล่างขวา
            x+w/2, y+cut, 0, 0,  # จุด 3: แฉกเว้าตรงกลาง
            x, y, 0, 0           # จุด 4: ล่างซ้าย
        ]
        
        # ✨ แก้ไขการโยงสามเหลี่ยม (indices) เพื่อไม่ให้วาดทะลุช่องว่างตรงกลาง
        # สามเหลี่ยม 3 ชิ้น: (บนซ้าย-บนขวา-กลาง) + (บนซ้าย-กลาง-ล่างซ้าย) + (บนขวา-ล่างขวา-กลาง)
        indices = [0, 1, 3,  0, 3, 4,  1, 2, 3]
        
        self.mesh.vertices = vertices
        self.mesh.indices = indices
        
        if self.line:
            self.line.points = [x, y+h, x+w, y+h, x+w, y, x+w/2, y+cut, x, y, x, y+h]

    def on_mouse_hover(self, window, pos):
        if not self.get_root_window() or self.is_selected: return
        is_hovering = self.collide_point(*self.to_widget(*pos))
        if is_hovering:
            if self.line: self.line.width = dp(3.0)
        else:
            if self.line: self.line.width = dp(1.5)

    def on_release(self):
        if self.map_screen:
            self.map_screen.on_banner_click(self)

    def destroy(self):
        """คลายการผูกเมาส์เมื่อรีเฟรชธงทิ้ง"""
        Window.unbind(mouse_pos=self.on_mouse_hover)

    def update_faction_state(self):
        """อัปเดตสีพื้นหลังและขอบตาม Faction ปัจจุบันของ Node"""
        if self.node.faction == 'white':
            bg_color = (0.9, 0.9, 0.9, 0.95)
            border_color = (0.1, 0.1, 0.1, 1)
        elif self.node.faction == 'black':
            bg_color = (0.15, 0.15, 0.15, 0.95)
            border_color = (0.9, 0.9, 0.9, 1)
        else: # Red
            bg_color = (0.6, 0.1, 0.15, 0.95)
            border_color = (0, 0, 0, 0) # โปร่งใสแทน None เพื่อป้องกัน error
            
        # อัปเดตสีใน Canvas ที่ถูกสร้างไว้แล้ว
        self.mesh_color.rgba = bg_color
        if self.line_color:
            self.line_color.rgba = border_color