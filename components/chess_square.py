# components/chess_square.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Quad, Line, Ellipse, PushMatrix, PopMatrix, Scale, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp 

class ChessSquare(ButtonBehavior, FloatLayout):
    def __init__(self, row, col, is_2d=True, piece_layer=None, tile_color_light=(0.8, 0.8, 0.8, 1), tile_color_dark=(0.4, 0.4, 0.4, 1), **kwargs):
        super().__init__(**kwargs)
        self.row, self.col = row, col
        self.is_2d = is_2d
        self.tile_color_light = tile_color_light
        self.tile_color_dark = tile_color_dark
        self.current_event = None
        self.current_event_path = None
        
        # 1. วาดพื้นกระดาน (แยกตาม 2D หรือ 2.5D)
        with self.canvas.before:
            # ประกาศ Kivy Color object เปล่าๆ แล้วค่อย assign .rgba ในตอน sync_layout
            self.bg_color = Color(1, 1, 1, 1) 
            if not self.is_2d:
                self.quad = Quad(points=[0]*8)
                Color(0.1, 0.1, 0.1, 0.5)
                self.border_line = Line(points=[0]*8, width=1, close=True)
            else:
                self.rect = Rectangle(pos=self.pos, size=self.size)

        self.piece_img = Image(fit_mode='contain', opacity=0, size_hint=(None, None) if not is_2d else (1, 1))
        self.piece_img.bind(texture=self._set_nearest_filter)
        
        if not self.is_2d:
            with self.piece_img.canvas.before:
                PushMatrix()
                self.scale_inst = Scale(x=1, y=1, origin=self.piece_img.center)
            with self.piece_img.canvas.after:
                PopMatrix()

        self.passive_indicator = Image(size_hint=(None, None), size=(dp(22), dp(22)), opacity=0, fit_mode='contain')
        self.passive_indicator.bind(texture=self._set_nearest_filter)
        
        self.commander_indicator = Image(size_hint=(None, None), size=(dp(24), dp(24)), opacity=0, fit_mode='contain')
        self.commander_indicator.bind(texture=self._set_nearest_filter)
        
        # ถ้าระบบ 2.5D ให้จับหมากไปไว้เลเยอร์บนสุด ป้องกันภาพซ้อน
        if not self.is_2d and piece_layer is not None:
            piece_layer.add_widget(self.piece_img)
            piece_layer.add_widget(self.passive_indicator)
            piece_layer.add_widget(self.commander_indicator)
        else:
            self.add_widget(self.piece_img)
            self.add_widget(self.passive_indicator)
            self.add_widget(self.commander_indicator)
            
        self.is_last_move = False
        self.is_legal = False
        self.highlight = False 
        self.is_check = False
        # ✨ เพิ่มตัวแปรสำหรับระบบ Fog
        self.is_fog = False
        self.fog_tex = None
        try:
            self.fog_tex = CoreImage('assets/ui/hidden_enemy.png').texture
            if self.fog_tex:
                self.fog_tex.mag_filter = 'nearest'
        except Exception:
            pass
        
        self.bind(pos=self.sync_layout, size=self.sync_layout)

    def _set_nearest_filter(self, widget, texture):
        if texture:
            texture.mag_filter = 'nearest'

    def sync_layout(self, *args):
        x, y, w, h = self.x, self.y, self.width, self.height
        
        # จัดการสีกระดานและไฮไลต์
        if self.is_check: 
            self.bg_color.rgba = (1, 0.2, 0.2, 0.8)
        elif self.highlight: 
            self.bg_color.rgba = (1, 1, 0, 0.3 if self.is_2d else 0.6)
        else:
            if self.is_2d:
                self.bg_color.rgba = (0, 0, 0, 0)
            else:
                # แก้ไข: ดึงสีที่กำหนดมาจาก init มาใช้ตรงนี้ (ต้องเป็น Tuple rgba)
                if (self.row + self.col) % 2 == 0: 
                    self.bg_color.rgba = self.tile_color_light
                else: 
                    self.bg_color.rgba = self.tile_color_dark

        # -------------------------------------
        # ระบบวาดผลลัพธ์ดั้งเดิม (2D Classic)
        # -------------------------------------
        if self.is_2d:
            self.rect.pos = self.pos
            self.rect.size = self.size
            self.piece_img.size = (w * 0.85, h * 0.85)
            self.piece_img.center = self.center
            
            if hasattr(self, 'passive_indicator'):
                self.passive_indicator.pos = (x + w - dp(26), y + h - dp(26))
                self.passive_indicator.canvas.before.clear()
                if self.passive_indicator.opacity > 0:
                    with self.passive_indicator.canvas.before:
                        Color(0, 0, 0, 0.7)
                        Ellipse(pos=(self.passive_indicator.x - 2, self.passive_indicator.y - 2), 
                               size=(self.passive_indicator.width + 4, self.passive_indicator.height + 4))
            
            if hasattr(self, 'commander_indicator'):
                self.commander_indicator.pos = (x + w / 2 - dp(12), y + h - dp(26))
                self.commander_indicator.canvas.before.clear()
                if self.commander_indicator.opacity > 0:
                    with self.commander_indicator.canvas.before:
                        Color(0, 0, 0, 0.7)
                        Ellipse(pos=(self.commander_indicator.x - 2, self.commander_indicator.y - 2), 
                               size=(self.commander_indicator.width + 4, self.commander_indicator.height + 4))
            
            self.canvas.after.clear()
            with self.canvas.after:
                if self.highlight:
                    Color(1, 0.5, 0, 1) 
                    Line(rectangle=(x + dp(2), y + dp(2), w - dp(4), h - dp(4)), width=dp(2.5))
                elif self.is_legal:
                    Color(0.1, 1, 0.1, 1) 
                    Line(rectangle=(x + dp(2), y + dp(2), w - dp(4), h - dp(4)), width=dp(2))
                elif self.is_last_move:
                    Color(1, 1, 0, 0.6) 
                    Line(rectangle=(x + dp(1), y + dp(1), w - dp(2), h - dp(2)), width=dp(1.5))
                    
        # -------------------------------------
        # ระบบวาดผลลัพธ์ใหม่ (2.5D Isometric)
        # -------------------------------------
        else:
            pts = [x, y + h/2, x + w/2, y, x + w, y + h/2, x + w/2, y + h]
            self.quad.points = pts
            self.border_line.points = pts
            
            self.piece_img.size = (dp(140), dp(140))
            self.piece_img.center_x = x + w / 2
            self.piece_img.y = y + h/2 - (self.piece_img.height * 0.15)
            self.scale_inst.origin = self.piece_img.center
            
            base_y = y + h/2
            if hasattr(self, 'passive_indicator'):
                self.passive_indicator.pos = (x + w - dp(26), base_y)
                self.passive_indicator.canvas.before.clear()
                if self.passive_indicator.opacity > 0:
                    with self.passive_indicator.canvas.before:
                        Color(0, 0, 0, 0.7)
                        Ellipse(pos=(self.passive_indicator.x - 2, self.passive_indicator.y - 2), 
                               size=(self.passive_indicator.width + 4, self.passive_indicator.height + 4))
            
            if hasattr(self, 'commander_indicator'):
                self.commander_indicator.pos = (x + w/2 - dp(12), base_y - dp(20))
                self.commander_indicator.canvas.before.clear()
                if self.commander_indicator.opacity > 0:
                    with self.commander_indicator.canvas.before:
                        Color(0, 0, 0, 0.7)
                        Ellipse(pos=(self.commander_indicator.x - 2, self.commander_indicator.y - 2), 
                               size=(self.commander_indicator.width + 4, self.commander_indicator.height + 4))
            
            self.canvas.after.clear()
            # วาดลูกบาศก์ก่อนแล้วค่อยทับด้วยเส้นขอบ
            if self.current_event:
                self.draw_event_cube(self.current_event, self.current_event_path)
            with self.canvas.after:
                if self.is_legal:
                    Color(0.1, 1, 0.1, 1) 
                    Line(points=pts, width=dp(2), close=True)
                elif self.is_last_move:
                    Color(1, 1, 0, 0.6) 
                    Line(points=pts, width=dp(1.5), close=True)

    def draw_event_cube(self, event_name, img_path):
        cube_z = dp(40)
        x, y, w, h = self.x, self.y, self.width, self.height
        
        left   = (x, y + h/2)
        bottom = (x + w/2, y)
        right  = (x + w, y + h/2)
        top    = (x + w/2, y + h)
        
        t_left   = (x, y + h/2 + cube_z)
        t_bottom = (x + w/2, y + cube_z)
        t_right  = (x + w, y + h/2 + cube_z)
        t_top    = (x + w/2, y + h + cube_z)

        if not img_path:
            if event_name == 'Sandstorm': img_path = 'assets/pieces/event/event2.png'
            elif event_name == 'Thorn': img_path = 'assets/pieces/event/event1.png'
            elif event_name == 'Ice': img_path = 'assets/pieces/event/event3.png'

        try:
            tex = CoreImage(img_path).texture
            tex.mag_filter = 'nearest'
            
            with self.canvas.after:
                Color(1, 1, 1, 1)
                Quad(texture=tex, points=[t_left[0], t_left[1], t_bottom[0], t_bottom[1], t_right[0], t_right[1], t_top[0], t_top[1]])
                Color(0.7, 0.7, 0.7, 1)
                Quad(texture=tex, points=[left[0], left[1], bottom[0], bottom[1], t_bottom[0], t_bottom[1], t_left[0], t_left[1]])
                Color(0.4, 0.4, 0.4, 1)
                Quad(texture=tex, points=[bottom[0], bottom[1], right[0], right[1], t_right[0], t_right[1], t_bottom[0], t_bottom[1]])
        except Exception as e:
            print(f"Error drawing event cube: {e}")

    def update_square_style(self, highlight=False, is_legal=False, is_check=False, is_last=False, is_fog=False):
        self.is_last_move = is_last
        self.is_legal = is_legal
        self.highlight = highlight 
        self.is_check = is_check
        self.is_fog = is_fog
        self.sync_layout()

    def set_piece_icon(self, path, is_frozen=False, piece=None, flip=False):
        self.current_event = None
        self.current_event_path = None
        
        # ป้องกันไม่ให้วาดลูกบาศก์ในโหมด 2D เด็ดขาด
        if not self.is_2d and piece and piece.__class__.__name__.lower() == 'obstacle':
            self.piece_img.opacity = 0
            self.current_event = getattr(piece, 'name', '')
            self.current_event_path = path
            self.sync_layout()
            return

        if path:
            self.piece_img.source = path
            self.piece_img.opacity = 1
            if not self.is_2d:
                self.scale_inst.x = -1 if flip else 1
            
            # ✨ นำ if piece: ออกไปเลย เพื่อบังคับให้ระบบเข้าไปเคลียร์ไอคอนค้าง
            # (เนื่องจากในฟังก์ชัน 2 ตัวนี้มีระบบเซ็ต opacity = 0 ถ้า piece=None ดักไว้อยู่แล้ว)
            self.show_hidden_passive(piece)
            self.show_commander_indicator(piece)
            
            self.piece_img.color = (0.2, 0.6, 1, 1) if is_frozen else (1, 1, 1, 1)
        else: 
            self.piece_img.opacity = 0
            self.piece_img.color = (1, 1, 1, 1)
            if hasattr(self, 'passive_indicator'): self.passive_indicator.opacity = 0
            if hasattr(self, 'commander_indicator'): self.commander_indicator.opacity = 0
            
        self.sync_layout()

    def show_hidden_passive(self, piece):
        if not piece or not hasattr(piece, 'hidden_passive'):
            if hasattr(self, 'passive_indicator'): self.passive_indicator.opacity = 0
            return
            
        passive_info = piece.hidden_passive.get_passive_info()
        if passive_info['type'] is None:
            self.passive_indicator.opacity = 0
            return
        
        p_type = passive_info['type']
        if p_type == 'buff1': self.passive_indicator.source = 'assets/icon_effect/bonus_coins.png'
        elif p_type == 'buff2': self.passive_indicator.source = 'assets/icon_effect/bonus_points.png'
        elif p_type == 'debuff1': self.passive_indicator.source = 'assets/icon_effect/reduce_coins.png'
        elif p_type == 'debuff2': self.passive_indicator.source = 'assets/icon_effect/reduce_points.png'
        
        self.passive_indicator.opacity = 1
        self.sync_layout()
    
    def show_commander_indicator(self, piece):
        if not piece or not hasattr(self, 'commander_indicator'):
            if hasattr(self, 'commander_indicator'): self.commander_indicator.opacity = 0
            return
        
        piece_class = piece.__class__.__name__.lower()
        is_header = getattr(piece, 'is_header', False)
        
        if piece_class == 'king':
            self.commander_indicator.source = 'assets/icon_effect/king.png'
            self.commander_indicator.opacity = 1
        elif piece_class == 'prince': 
            self.commander_indicator.source = 'assets/icon_effect/prince.png'
            self.commander_indicator.opacity = 1
        elif is_header:
            self.commander_indicator.source = 'assets/icon_effect/general.png'
            self.commander_indicator.opacity = 1
        else:
            self.commander_indicator.opacity = 0
        
        self.sync_layout()