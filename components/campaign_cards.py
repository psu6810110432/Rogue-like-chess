# components/campaign_cards.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Line, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from logic.image_utils import safe_piece_path
from kivy.uix.behaviors import ButtonBehavior

class PieceCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_obj, map_screen_ref=None, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(130), **kwargs)
        self.piece_obj = piece_obj
        self.is_selected = False
        self.map_screen_ref = map_screen_ref
        
        with self.canvas.before:
            Color(0.12, 0.12, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            self.border_color = Color(0.3, 0.3, 0.35, 1)
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)

        p_name = piece_obj.__class__.__name__.lower()
        tribe = getattr(piece_obj, 'tribe', 'the knight company')
        color = piece_obj.color
        lvl   = getattr(piece_obj, 'upgrade_level', 0)

        if getattr(piece_obj, 'is_header', False):
            with self.canvas.before:
                Color(1, 0.8, 0, 0.3)
                Ellipse(pos=(self.center_x - dp(25), self.top - dp(55)), size=(dp(50), dp(50)))
                
        img_path = safe_piece_path(piece_obj, tribe, color)
        self.add_widget(Image(source=img_path, size_hint=(0.85, 0.65), pos_hint={'center_x': 0.5, 'top': 0.98}))

        display_name = getattr(piece_obj, 'name', p_name.capitalize())
        lvl_str = f" [color=ffff00]+{lvl}[/color]" if lvl > 0 else ""

        
        name_lbl = Label(text=f"[b]{display_name}{lvl_str}[/b]", markup=True, font_size='12sp', pos_hint={'center_x': 0.5, 'y': 0.18}, size_hint=(1, 0.2), halign='center', valign='middle')
        name_lbl.bind(size=name_lbl.setter('text_size'))
        self.add_widget(name_lbl)
        
        hp = getattr(piece_obj, 'hidden_passive', None)
        passive_text = hp.description if hp and hp.passive_type else "No Passive"
        
        p_color = "a0a0a0"
        if hp and hp.passive_type:
            if hp.passive_type.startswith('buff'): p_color = "44ff44" 
            else: p_color = "ff4444" 
            
        self.add_widget(Label(text=f"[size=11sp][color={p_color}]{passive_text}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

        if getattr(piece_obj, 'item', None):
            self.add_widget(Image(source=piece_obj.item.image_path, size_hint=(0.35, 0.35), pos_hint={'right': 0.95, 'top': 0.95}))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        App.get_running_app().play_click_sound()
        
        if self.map_screen_ref and getattr(self.map_screen_ref.army_panel, 'is_upgrade_mode', False):
            def on_upgraded():
                self.map_screen_ref.army_panel.switch_tab('army')
            
            from components.campaign_popups import UpgradeTreePopup
            pop = UpgradeTreePopup(self.piece_obj, on_upgraded)
            pop.bind(on_open=lambda instance: setattr(pop, 'width', self.map_screen_ref.width * 0.9))
            pop.open()
        else:
            self.is_selected = not self.is_selected
            self.border_color.rgba = (1, 0.8, 0, 1) if self.is_selected else (0.3, 0.3, 0.35, 1)
            self.border_line.width = 2.5 if self.is_selected else 1.5


class RecruitCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_name, cost, faction, app, click_cb, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(120), **kwargs)
        self.click_cb = click_cb
        self.piece_name = piece_name
        self.cost = cost
        
        with self.canvas.before:
            if piece_name is None:
                Color(0.1, 0.1, 0.1, 0.95) 
            else:
                Color(0.12, 0.2, 0.12, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)

        if piece_name is None:
            self.disabled = True
            self.add_widget(Label(text="[b]X[/b]", markup=True, font_size='40sp', color=(0.4, 0.4, 0.4, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}))
            return

        theme = getattr(app, f'selected_unit_{faction}', 'Medieval Knights')
        theme_map = {
            "Medieval Knights": "the knight company",
            "Heaven": "the ancient runes",
            "Ayothaya": "the chaos mankind",
            "Demon": "the deep anomaly",
            "Bandit": "bandit"
        }
        tribe = theme_map.get(theme, theme.lower())
        
        if piece_name in ['pawn', 'hastati', 'levies']: filename = f"{piece_name}1.png"
        else: filename = f"{piece_name}.png"
            
        img_path = f"assets/pieces/{tribe}/{faction}/1base/{filename}"
        img = Image(source=img_path, size_hint=(0.85, 0.65), pos_hint={'center_x': 0.5, 'top': 0.98})
        self.add_widget(img)
        
        self.add_widget(Label(text=f"[b]{piece_name.capitalize()}[/b]", markup=True, font_size='13sp', pos_hint={'center_x': 0.5, 'y': 0.18}, size_hint=(1, 0.2)))
        self.add_widget(Label(text=f"[size=12sp][color=ffff00]Cost: {cost}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        if self.piece_name is not None and self.click_cb:
            self.click_cb(self.piece_name, self.cost)