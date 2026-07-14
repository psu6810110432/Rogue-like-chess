# components/chess_square.py
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp 

class ChessSquare(Button):
    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row, self.col = row, col
        
        self.background_normal = '' 
        self.background_down = ''
        
        self.piece_img = Image(fit_mode='contain', opacity=0)
        self.piece_img.bind(texture=self._set_nearest_filter)
        self.add_widget(self.piece_img)
        
        self.passive_indicator = Image(
            size_hint=(None, None),
            size=(22, 22),
            opacity=0,
            fit_mode='contain'
        )
        self.passive_indicator.bind(texture=self._set_nearest_filter)
        self.add_widget(self.passive_indicator)
        
        self.commander_indicator = Image(
            size_hint=(None, None),
            size=(24, 24),
            opacity=0,
            fit_mode='contain'
        )
        self.commander_indicator.bind(texture=self._set_nearest_filter)
        self.add_widget(self.commander_indicator)
        
        self.is_last_move = False
        self.is_legal = False
        self.highlight = False 
        
        self.update_square_style()
        self.bind(pos=self.sync_layout, size=self.sync_layout)

    def _set_nearest_filter(self, widget, texture):
        if texture:
            texture.mag_filter = 'nearest'

    def sync_layout(self, *args):
        self.piece_img.size = (self.width * 0.85, self.height * 0.85)
        self.piece_img.center = self.center
        
        if hasattr(self, 'passive_indicator'):
            self.passive_indicator.pos = (self.x + self.width - 26, self.y + self.height - 26)
            self.passive_indicator.canvas.before.clear()
            if self.passive_indicator.opacity > 0:
                with self.passive_indicator.canvas.before:
                    Color(0, 0, 0, 0.7)
                    Ellipse(pos=(self.passive_indicator.x - 2, self.passive_indicator.y - 2), 
                           size=(self.passive_indicator.width + 4, self.passive_indicator.height + 4))
        
        if hasattr(self, 'commander_indicator'):
            self.commander_indicator.pos = (self.x + self.width / 2 - 12, self.y + self.height - 26)
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
                Line(rectangle=(self.x + dp(2), self.y + dp(2), self.width - dp(4), self.height - dp(4)), width=dp(2.5))
            elif self.is_legal:
                Color(0.1, 1, 0.1, 1) 
                Line(rectangle=(self.x + dp(2), self.y + dp(2), self.width - dp(4), self.height - dp(4)), width=dp(2))
            elif self.is_last_move:
                Color(1, 1, 0, 0.6) 
                Line(rectangle=(self.x + dp(1), self.y + dp(1), self.width - dp(2), self.height - dp(2)), width=dp(1.5))

    def update_square_style(self, highlight=False, is_legal=False, is_check=False, is_last=False):
        self.is_last_move = is_last
        self.is_legal = is_legal
        self.highlight = highlight 
        if is_check: self.background_color = (1, 0.2, 0.2, 0.8) 
        elif highlight: self.background_color = (1, 1, 0, 0.3) 
        else: self.background_color = (0, 0, 0, 0) 
        self.sync_layout()

    def set_piece_icon(self, path, is_frozen=False, piece=None):
        if path:
            self.piece_img.source = path
            self.piece_img.opacity = 1
            self.show_hidden_passive(piece)
            self.show_commander_indicator(piece)
            
            if is_frozen:
                self.piece_img.color = (0.2, 0.6, 1, 1)  
                if self.background_color == [0, 0, 0, 0]:
                    self.background_color = (0, 0.5, 1, 0.4) 
            else:
                self.piece_img.color = (1, 1, 1, 1)
                if self.background_color == [0, 0.5, 1, 0.4]: 
                    self.background_color = (0, 0, 0, 0)
        else: 
            self.piece_img.opacity = 0
            self.piece_img.color = (1, 1, 1, 1)
            if hasattr(self, 'passive_indicator'): self.passive_indicator.opacity = 0
            if hasattr(self, 'commander_indicator'): self.commander_indicator.opacity = 0
            if self.background_color == [0, 0.5, 1, 0.4]: self.background_color = (0, 0, 0, 0)
    
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
        
        # แก้ไขเงื่อนไขการเช็คคลาสเพื่อความถูกต้อง
        piece_class = piece.__class__.__name__.lower()
        is_header = getattr(piece, 'is_header', False)
        
        if piece_class == 'king':
            self.commander_indicator.source = 'assets/icon_effect/king.png'
            self.commander_indicator.opacity = 1
        elif piece_class == 'prince': # เช็คจาก class name ได้เลย
            self.commander_indicator.source = 'assets/icon_effect/prince.png'
            self.commander_indicator.opacity = 1
        elif is_header:
            self.commander_indicator.source = 'assets/icon_effect/general.png'
            self.commander_indicator.opacity = 1
        else:
            self.commander_indicator.opacity = 0
        
        self.sync_layout()