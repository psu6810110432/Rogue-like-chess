# screens/campaign_map_screen.py
import random
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.uix.spinner import Spinner
from logic.pieces import Pawn, Knight, Bishop, Rook, Queen, King
from logic.pieces import Princess, Menatarm, Praetorian, Royalguard, Hastati, Levies
from components.hidden_passive import HiddenPassive

def check_rect_overlap(r1, r2):
    x1, y1, w1, h1 = r1; x2, y2, w2, h2 = r2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

def is_overlapping_any(rect, rect_list):
    for r in rect_list:
        if check_rect_overlap(rect, r): return True
    return False

def get_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def generate_piece(piece_name, faction, app):
    theme = getattr(app, f'selected_unit_{faction}', 'Medieval Knights') if faction != 'red' else 'Bandit'
    
    theme_map = {
        "Medieval Knights": "the knight company",
        "Heaven": "the ancient runes",
        "Ayothaya": "the chaos mankind",
        "Demon": "the deep anomaly",
        "Bandit": "bandit"
    }
    tribe = theme_map.get(theme, theme.lower())
    color = faction if faction in ['white', 'black'] else 'black'
    
    classes = {
        'pawn': Pawn, 'knight': Knight, 'bishop': Bishop, 'rook': Rook, 'queen': Queen, 'king': King, 'prince': King,
        'princess': Princess, 'menatarm': Menatarm, 'praetorian': Praetorian, 'royalguard': Royalguard,
        'hastati': Hastati, 'levies': Levies
    }
    
    p = classes[piece_name](color, tribe)
    if piece_name == 'prince': p.name = "Prince" 
    
    if not hasattr(p, 'hidden_passive') or p.hidden_passive is None:
        p.hidden_passive = HiddenPassive()
        p.base_points, p.coins = p.hidden_passive.apply_passive(p.base_points, p.coins)
    
    p.base_atk = getattr(p, 'base_atk', p.base_points)
    p.base_def = getattr(p, 'base_def', p.base_points)
    return p

def clone_piece(p, faction, app):
    p_name = p.__class__.__name__.lower()
    if getattr(p, 'name', '') == 'Prince': p_name = 'prince'
    elif getattr(p, 'name', '') == 'Garrison Commander': p_name = 'king' 
    
    new_p = generate_piece(p_name, faction, app)
    new_p.base_points = p.base_points
    new_p.coins = p.coins
    new_p.item = getattr(p, 'item', None)
    new_p.hidden_passive = getattr(p, 'hidden_passive', None)
    new_p.second_hidden_passive = getattr(p, 'second_hidden_passive', None)
    new_p.base_atk = getattr(p, 'base_atk', p.base_points)
    new_p.base_def = getattr(p, 'base_def', p.base_points)
    new_p.upgrade_level = getattr(p, 'upgrade_level', 0)
    new_p.upgrade_path = getattr(p, 'upgrade_path', 'standard')
    return new_p

def ensure_header(army_list, faction, app):
    has_header = any(p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' for p in army_list)
    if not has_header:
        commander = generate_piece('king', faction, app)
        commander.name = "Garrison Commander"
        army_list.append(commander)

# ----------------- ระบบ Upgrade Tree UI -----------------
class TechCard(ButtonBehavior, BoxLayout):
    def __init__(self, title, desc, atk, def_pt, coins, img_path, is_unlocked, is_available, on_click_cb, **kwargs):
        super().__init__(orientation='vertical', padding=dp(5), spacing=dp(2), size_hint=(None, None), size=(dp(120), dp(160)), **kwargs)
        self.is_unlocked = is_unlocked
        self.is_available = is_available
        self.on_click_cb = on_click_cb
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 0.9)
            self.bg = RoundedRectangle(radius=[dp(8)])
            
            if is_unlocked:
                Color(0.9, 0.8, 0.2, 1) 
                width = 2
            elif is_available:
                Color(0.4, 0.8, 0.4, 1) 
                width = 1.5
            else:
                Color(0.3, 0.3, 0.35, 1) 
                width = 1
                
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=width)
            
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='13sp', size_hint_y=0.15))
        
        img = Image(source=img_path, allow_stretch=True, keep_ratio=True, size_hint_y=0.4)
        if not is_unlocked and not is_available: img.opacity = 0.4
        self.add_widget(img)
        
        stats_color = "aaaaaa" if not is_unlocked and not is_available else "ffffff"
        self.add_widget(Label(text=f"[color={stats_color}]ATK: {atk} | DEF: {def_pt}\nCoins: {coins}[/color]", markup=True, font_size='11sp', size_hint_y=0.25, halign='center'))
        self.add_widget(Label(text=f"[color=00ffcc]{desc}[/color]", markup=True, font_size='10sp', size_hint_y=0.2, halign='center'))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        if self.is_available and self.on_click_cb:
            self.on_click_cb()

class UpgradeTreePopup(ModalView):
    def __init__(self, piece_obj, update_callback, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), background_color=(0, 0, 0, 0.8), auto_dismiss=False, **kwargs)
        self.piece = piece_obj
        self.update_callback = update_callback
        
        self.root_layout = FloatLayout()
        with self.root_layout.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.83, 0.68, 0.21, 1)
            self.border_line = Line(rounded_rectangle=(self.root_layout.x, self.root_layout.y, self.root_layout.width, self.root_layout.height, dp(15)), width=2)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'top': 1}, padding=[dp(15), dp(5)])
        p_name = getattr(self.piece, 'name', self.piece.__class__.__name__.capitalize())
        header.add_widget(Label(text=f"[b]UPGRADE PATH: {p_name}[/b]", markup=True, font_size='20sp', halign='left', color=(1, 0.8, 0.2, 1)))
        
        close_btn = Button(text="CLOSE", size_hint_x=None, width=dp(80), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        self.root_layout.add_widget(header)

        self.tree_layout = FloatLayout(size_hint=(1, 0.9), pos_hint={'y': 0})
        self.root_layout.add_widget(self.tree_layout)
        
        self.bind(size=self.draw_tree) 
        Clock.schedule_once(lambda dt: self.draw_tree(), 0.1)
        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(15))

    def draw_tree(self, *args):
        self.tree_layout.clear_widgets()
        self.tree_layout.canvas.before.clear()
        
        p = self.piece
        c_name = p.__class__.__name__.lower()
        tribe = getattr(p, 'tribe', 'the knight company')
        color = p.color
        
        lvl = getattr(p, 'upgrade_level', 0)
        path = getattr(p, 'upgrade_path', 'standard')
        
        if c_name in ['pawn', 'hastati', 'levies']: filename = f"{c_name}{getattr(p, 'variant', 1)}.png"
        else: filename = f"{c_name}.png"
        if getattr(p, 'name', '') == 'Prince': filename = 'prince.png'
            
        base_img = f"assets/pieces/{tribe}/{color}/1base/{filename}"
        atk1_img = f"assets/pieces/{tribe}/{color}/2upATK/{filename}"
        def2_img = f"assets/pieces/{tribe}/{color}/3upDEF/{filename}"
        
        has_special = c_name in ['praetorian', 'menatarm']
        spec1_img = f"assets/pieces/{tribe}/{color}/4up_rehidden/{filename}" if has_special else None
        spec2_img = f"assets/pieces/{tribe}/{color}/5up_reroll_ATK_DEF/{filename}" if has_special else None

        def draw_line(p1, p2, is_active):
            with self.tree_layout.canvas.before:
                Color(0.9, 0.8, 0.2, 1) if is_active else Color(0.4, 0.4, 0.4, 1)
                Line(points=[p1[0], p1[1], p2[0], p2[1]], width=2 if is_active else 1.5)

        cx = self.width / 2 if self.width > 1 else dp(400)
        cy = self.height / 2 if self.height > 1 else dp(300)
        card_w, card_h = dp(120), dp(160)
        
        y_top = cy + dp(120)
        y_mid = cy - dp(40)
        y_bot = cy - dp(200)

        b_atk = getattr(p, 'base_atk', p.base_points) if lvl == 0 else p.base_points
        b_def = getattr(p, 'base_def', p.base_points) if lvl == 0 else p.base_points
        
        node_base = TechCard("Base Form", "Default Stats", b_atk, b_def, p.coins, base_img, (lvl == 0), False, None)
        node_base.pos = (cx - card_w/2, y_top - card_h/2)
        self.tree_layout.add_widget(node_base)

        if not has_special:
            n1_unlocked = (lvl >= 1)
            n1_avail = (lvl == 0)
            n1_atk = b_atk + 2
            node_u1 = TechCard("Rank I", "+2 Base ATK", n1_atk, b_def, p.coins, atk1_img, n1_unlocked, n1_avail, lambda: self.do_upgrade("standard"))
            node_u1.pos = (cx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1)
            
            n2_unlocked = (lvl == 2)
            n2_avail = (lvl == 1)
            n2_def = b_def + 2
            node_u2 = TechCard("Rank II", "+2 Base DEF", n1_atk, n2_def, p.coins, def2_img, n2_unlocked, n2_avail, lambda: self.do_upgrade("standard"))
            node_u2.pos = (cx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1.center_x, node_u1.top), n1_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1.center_x, node_u1.y), (node_u2.center_x, node_u2.top), n2_unlocked), 0.1)
            
        else:
            lx = cx - dp(100)
            rx = cx + dp(100)
            
            n1_std_unlocked = (lvl >= 1 and path == "standard")
            n1_std_avail = (lvl == 0)
            node_u1_std = TechCard("Rank I (Combat)", "+2 Base ATK", b_atk+2, b_def, p.coins, atk1_img, n1_std_unlocked, n1_std_avail, lambda: self.do_upgrade("standard"))
            node_u1_std.pos = (lx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1_std)
            
            n2_std_unlocked = (lvl == 2 and path == "standard")
            n2_std_avail = (lvl == 1 and path == "standard")
            node_u2_std = TechCard("Rank II (Combat)", "+2 Base DEF", b_atk+2, b_def+2, p.coins, def2_img, n2_std_unlocked, n2_std_avail, lambda: self.do_upgrade("standard"))
            node_u2_std.pos = (lx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2_std)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1_std.center_x, node_u1_std.top), n1_std_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_std.center_x, node_u1_std.y), (node_u2_std.center_x, node_u2_std.top), n2_std_unlocked), 0.1)

            n1_spc_unlocked = (lvl >= 1 and path == "special")
            n1_spc_avail = (lvl == 0)
            desc1 = "Reroll Hidden Passive" if not n1_spc_unlocked else getattr(p.hidden_passive, 'description', 'Passive Re-rolled')
            n1_spc_atk = b_atk if not n1_spc_unlocked else p.base_atk
            n1_spc_def = b_def if not n1_spc_unlocked else p.base_def
            
            node_u1_spc = TechCard("Rank I (Utility)", desc1, n1_spc_atk, n1_spc_def, p.coins, spec1_img, n1_spc_unlocked, n1_spc_avail, lambda: self.do_upgrade("special"))
            node_u1_spc.pos = (rx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1_spc)
            
            n2_spc_unlocked = (lvl == 2 and path == "special")
            n2_spc_avail = (lvl == 1 and path == "special")
            desc2 = "Gain 2nd Hidden Passive" if not n2_spc_unlocked else getattr(p.second_hidden_passive, 'description', '2nd Passive Active')
            
            node_u2_spc = TechCard("Rank II (Utility)", desc2, p.base_atk, p.base_def, p.coins, spec2_img, n2_spc_unlocked, n2_spc_avail, lambda: self.do_upgrade("special"))
            node_u2_spc.pos = (rx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2_spc)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1_spc.center_x, node_u1_spc.top), n1_spc_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_spc.center_x, node_u1_spc.y), (node_u2_spc.center_x, node_u2_spc.top), n2_spc_unlocked), 0.1)

    def do_upgrade(self, path):
        app = App.get_running_app()
        app.play_click_sound()
        
        cost = 3 if getattr(self.piece, 'upgrade_level', 0) == 0 else 5
        faction = app.current_map_turn
        
        if app.tax_points.get(faction, 0) < cost:
            return
            
        app.tax_points[faction] -= cost
        
        if hasattr(self.piece, 'upgrade_piece'):
            self.piece.upgrade_piece(path)
            
        self.draw_tree()
        if self.update_callback:
            self.update_callback()

# ----------------- UI การ์ดทหารสไตล์ Total War -----------------
class PieceCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_obj, map_screen_ref=None, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(110), **kwargs)
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
        
        lvl = getattr(piece_obj, 'upgrade_level', 0)
        path = getattr(piece_obj, 'upgrade_path', 'standard')
        
        stage_folder = "1base"
        if lvl > 0:
            if path == 'standard': stage_folder = "2upATK" if lvl == 1 else "3upDEF"
            elif path == 'special': stage_folder = "4up_rehidden" if lvl == 1 else "5up_reroll_ATK_DEF"
            
        if p_name in ['pawn', 'hastati', 'levies']:
            num = getattr(piece_obj, 'variant', 1)
            filename = f"{p_name}{num}.png"
        else:
            filename = f"{p_name}.png"
            
        if getattr(piece_obj, 'name', '') == 'Prince': filename = 'prince.png'
        
        img_path = f"assets/pieces/{tribe}/{color}/{stage_folder}/{filename}"
        
        self.add_widget(Image(source=img_path, size_hint=(0.7, 0.6), pos_hint={'center_x': 0.5, 'top': 0.9}))
        display_name = getattr(piece_obj, 'name', p_name.capitalize())
        
        lvl_str = f" [color=ffff00]+{lvl}[/color]" if lvl > 0 else ""
        self.add_widget(Label(text=f"[b]{display_name}{lvl_str}[/b]", markup=True, font_size='13sp', pos_hint={'center_x': 0.5, 'y': 0.15}, size_hint=(1, 0.2)))
        
        hp = getattr(piece_obj, 'hidden_passive', None)
        passive_text = hp.description if hp and hp.passive_type else "No Passive"
        self.add_widget(Label(text=f"[size=10sp][color=a0a0a0]{passive_text}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

        if getattr(piece_obj, 'item', None):
            self.add_widget(Image(source=piece_obj.item.image_path, size_hint=(0.35, 0.35), pos_hint={'right': 0.95, 'top': 0.95}))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        App.get_running_app().play_click_sound()
        
        # ✨ ถ้าอยู่ในโหมดอัปเกรด ให้เปิด Popup เลย
        if self.map_screen_ref and getattr(self.map_screen_ref.army_panel, 'is_upgrade_mode', False):
            def on_upgraded():
                self.map_screen_ref.army_panel.switch_tab('army') 
            pop = UpgradeTreePopup(self.piece_obj, on_upgraded)
            pop.open()
        else:
            self.is_selected = not self.is_selected
            self.border_color.rgba = (1, 0.8, 0, 1) if self.is_selected else (0.3, 0.3, 0.35, 1)
            self.border_line.width = 2.5 if self.is_selected else 1.5

# ✨ เพิ่มระบบ Locked Status ลงใน RecruitCard
class RecruitCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_name, cost, faction, app, click_cb, is_locked=False, unlock_cost=0, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(110), **kwargs)
        self.click_cb = click_cb
        self.piece_name = piece_name
        self.cost = cost
        self.is_locked = is_locked
        self.unlock_cost = unlock_cost
        
        with self.canvas.before:
            Color(0.25, 0.1, 0.1, 0.95) if is_locked else Color(0.12, 0.2, 0.12, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)

        theme = getattr(app, f'selected_unit_{faction}', 'Medieval Knights')
        theme_map = {
            "Medieval Knights": "the knight company",
            "Heaven": "the ancient runes",
            "Ayothaya": "the chaos mankind",
            "Demon": "the deep anomaly",
            "Bandit": "bandit"
        }
        tribe = theme_map.get(theme, theme.lower())
        
        if piece_name in ['pawn', 'hastati', 'levies']:
            filename = f"{piece_name}1.png"
        else:
            filename = f"{piece_name}.png"
            
        img_path = f"assets/pieces/{tribe}/{faction}/1base/{filename}"
        
        img = Image(source=img_path, size_hint=(0.7, 0.6), pos_hint={'center_x': 0.5, 'top': 0.9})
        if is_locked: img.opacity = 0.3
        self.add_widget(img)
        
        self.add_widget(Label(text=f"[b]{piece_name.capitalize()}[/b]", markup=True, font_size='13sp', pos_hint={'center_x': 0.5, 'y': 0.15}, size_hint=(1, 0.2)))
        
        if is_locked:
            self.add_widget(Label(text=f"[size=12sp][color=ff5555]Unlock: {unlock_cost}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))
        else:
            self.add_widget(Label(text=f"[size=12sp][color=ffff00]Cost: {cost}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        self.click_cb(self.piece_name, self.cost, self.is_locked, self.unlock_cost)


# ----------------- UI แถบซ้ายล่าง (Total War Army Panel) -----------------
class CampaignArmyPanel(FloatLayout):
    def __init__(self, map_screen, app, **kwargs):
        super().__init__(size_hint=(0.85, None), height=dp(200), pos_hint={'x': 0.02, 'y': -0.5}, **kwargs) 
        self.map_screen = map_screen
        self.app = app
        self.current_node = None
        self.current_tab = 'army'
        self.is_upgrade_mode = False 

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.bg = RoundedRectangle(radius=[dp(12)])
            self.border_color = Color(0.5, 0.5, 0.5, 1)
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=2)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.header_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), pos_hint={'top': 1, 'x': 0}, padding=[dp(10), dp(5)])
        
        self.header_lbl = Label(text="ARMY HQ", bold=True, font_size='18sp', size_hint_x=0.3, halign='left')
        self.status_lbl = Label(text="", markup=True, size_hint_x=0.2, font_size='14sp')
        
        self.btn_tab_army = Button(text="[b]ARMY[/b]", markup=True, size_hint_x=0.15, background_color=(0.3, 0.5, 0.8, 1))
        self.btn_tab_army.bind(on_release=lambda x: self.switch_tab('army'))
        self.btn_tab_recruit = Button(text="[b]RECRUIT[/b]", markup=True, size_hint_x=0.15, background_color=(0.2, 0.2, 0.2, 1))
        self.btn_tab_recruit.bind(on_release=lambda x: self.switch_tab('recruit'))
        
        btn_close = Button(text="CLOSE", size_hint_x=0.1, background_color=(0.5, 0.2, 0.2, 1))
        btn_close.bind(on_release=self.close_panel)
        
        self.header_box.add_widget(self.header_lbl)
        self.header_box.add_widget(self.status_lbl)
        self.header_box.add_widget(self.btn_tab_army)
        self.header_box.add_widget(self.btn_tab_recruit)
        self.header_box.add_widget(btn_close)
        self.add_widget(self.header_box)

        self.content_scroll = ScrollView(size_hint=(0.7, 0.7), pos_hint={'x': 0.02, 'y': 0.05}, do_scroll_x=True, do_scroll_y=False)
        self.content_grid = GridLayout(rows=1, spacing=dp(8), size_hint_x=None, padding=dp(5))
        self.content_grid.bind(minimum_width=self.content_grid.setter('width'))
        self.content_scroll.add_widget(self.content_grid)
        self.add_widget(self.content_scroll)

        self.action_box = BoxLayout(orientation='vertical', size_hint=(0.25, 0.7), pos_hint={'right': 0.98, 'y': 0.05}, spacing=dp(5))
        
        self.btn_action = Button(text="[b]MARCH / ATTACK[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1), size_hint_y=0.6)
        self.btn_action.bind(on_release=self.execute_action)
        self.action_box.add_widget(self.btn_action)
        
        # ✨ เพิ่มปุ่ม Upgrade แบบ Toggle
        self.sub_action_box = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=0.4)
        
        self.btn_upgrade = Button(text="[b]UPGRADE[/b]", markup=True, background_color=(0.6, 0.2, 0.8, 1))
        self.btn_upgrade.bind(on_release=self.toggle_upgrade_mode)
        self.sub_action_box.add_widget(self.btn_upgrade)
        
        self.action_box.add_widget(self.sub_action_box)
        self.add_widget(self.action_box)

        self.piece_cards = []

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(12))

    def open_for_node(self, node):
        from kivy.animation import Animation
        self.current_node = node
        self.header_lbl.text = f"{node.faction.upper()} {node.node_type.upper()}"
        self.is_upgrade_mode = False
        
        if node.faction == 'white': self.border_color.rgba = (0.9, 0.9, 0.9, 1)
        elif node.faction == 'black': self.border_color.rgba = (0.3, 0.3, 0.4, 1)
        
        self.switch_tab('army')
        Animation(pos_hint={'y': 0.02}, duration=0.3, t='out_quad').start(self)

    def close_panel(self, *args):
        from kivy.animation import Animation
        self.app.play_click_sound()
        Animation(pos_hint={'y': -0.5}, duration=0.2).start(self)

    def toggle_upgrade_mode(self, instance):
        self.app.play_click_sound()
        self.is_upgrade_mode = not self.is_upgrade_mode
        
        if self.is_upgrade_mode:
            self.btn_upgrade.background_color = (0.8, 0.8, 0.2, 1)
            self.map_screen.status_lbl.text = f"[color=ffff00]UPGRADE MODE: Tax {self.app.tax_points.get(self.current_node.faction, 0)} | Select a unit to open Tech Tree.[/color]"
            
            for card in self.piece_cards:
                card.is_selected = False
                card.border_color.rgba = (0.3, 0.3, 0.35, 1)
                card.border_line.width = 1.5
        else:
            self.switch_tab('army')

    def switch_tab(self, tab_name):
        self.app.play_click_sound()
        self.current_tab = tab_name
        self.is_upgrade_mode = False
        self.content_grid.clear_widgets()
        self.piece_cards.clear()

        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
        heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
        heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
        total = len(self.current_node.army_pieces)
        max_cap = 16 if headers > 0 else 8

        if tab_name == 'army':
            self.btn_tab_army.background_color = (0.3, 0.5, 0.8, 1)
            self.btn_tab_recruit.background_color = (0.2, 0.2, 0.2, 1)
            
            lylt = getattr(self.current_node, 'loyalty', 100)
            color_lylt = '00ff00' if lylt > 60 else ('ffcc00' if lylt > 20 else 'ff0000')
            
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            fatigue_color = '00ff00' if fatigue == 0 else ('ffaa00' if fatigue < 3 else 'ff0000')
            self.status_lbl.text = f"Loyalty: [color={color_lylt}]{lylt}%[/color] | Cap: [b]{total}/{max_cap}[/b] | Fatigue: [color={fatigue_color}]{fatigue}/4[/color]"
            
            self.btn_action.text = "[b]MARCH / ATTACK[/b]"
            self.btn_action.background_color = (0.8, 0.2, 0.2, 1)
            self.btn_action.opacity = 1
            self.btn_action.disabled = False
            
            self.sub_action_box.opacity = 1
            self.btn_upgrade.disabled = False
            self.btn_upgrade.background_color = (0.6, 0.2, 0.8, 1)
            
            for p in self.current_node.army_pieces:
                card = PieceCard(p, map_screen_ref=self.map_screen) 
                self.piece_cards.append(card)
                self.content_grid.add_widget(card)
        else:
            self.btn_tab_army.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_recruit.background_color = (0.3, 0.8, 0.3, 1)
            self.status_lbl.text = f"Tax: [color=00ff00]{self.app.tax_points.get(self.current_node.faction, 0)}[/color] | Cap: {total}/{max_cap}"
            
            self.btn_action.text = "[b]QUICK RECRUIT\n(7 TAX)[/b]"
            self.btn_action.background_color = (0.8, 0.6, 0.1, 1)
            self.btn_action.opacity = 1
            self.btn_action.disabled = False
            
            self.sub_action_box.opacity = 0
            self.btn_upgrade.disabled = True
            
            # ✨ นำ Queen และ Princess ออก และปรับราคาตามที่สั่ง
            can_heavy = (self.current_node.node_type == 'castle')
            units_to_sell = [
                ('praetorian', 7), ('royalguard', 7), ('menatarm', 5),
                ('knight', 4), ('bishop', 4), ('rook', 4), 
                ('hastati', 3), ('levies', 2), ('pawn', 2)
            ]
            unlock_costs = {'praetorian': 14, 'royalguard': 14, 'hastati': 6} # ค่าใช้จ่ายปลดล็อคตั้งต้น (แก้ไขได้)
            
            for p_name, cost in units_to_sell:
                if cost > 3 and not can_heavy: continue # เฉพาะปราสาทที่สร้างตัวแพงได้
                
                is_locked = p_name not in self.app.unlocked_units.get(self.current_node.faction, set())
                ucost = unlock_costs.get(p_name, 0)
                card = RecruitCard(p_name, cost, self.current_node.faction, self.app, self.buy_piece, is_locked=is_locked, unlock_cost=ucost)
                self.content_grid.add_widget(card)

    def buy_piece(self, piece_name, cost, is_locked, unlock_cost):
        self.app.play_click_sound()
        faction = self.current_node.faction
        
        # ✨ ถ้าติดล็อคอยู่ ให้ใช้คำสั่งซื้อเป็นการปลดล็อคแทน
        if is_locked:
            if self.app.tax_points.get(faction, 0) >= unlock_cost:
                self.app.tax_points[faction] -= unlock_cost
                self.app.unlocked_units[faction].add(piece_name)
                self.switch_tab('recruit')
            return
            
        tax = self.app.tax_points[faction]
        if tax < cost: return
        
        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
        heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
        heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
        max_cap = 16 if headers > 0 else 8
        if len(self.current_node.army_pieces) >= max_cap: return
        
        if piece_name in ['pawn', 'hastati', 'levies'] and heavies > 9: return 
        
        self.app.tax_points[faction] -= cost
        new_p = generate_piece(piece_name, faction, self.app)
        self.current_node.army_pieces.append(new_p)
        self.switch_tab('recruit') 

    def execute_action(self, instance):
        self.app.play_click_sound()
        if self.current_tab == 'army':
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            if fatigue >= 3:
                self.map_screen.status_lbl.text = "[color=ff0000]ARMY IS TOO EXHAUSTED (FATIGUE LEVEL 3+)! MUST REST.[/color]"
                return
                
            selected_pieces = [card.piece_obj for card in self.piece_cards if card.is_selected]
            if len(selected_pieces) == 0:
                selected_pieces = self.current_node.army_pieces.copy() 
            
            if len(selected_pieces) == 0: return 
            
            for p in selected_pieces:
                self.current_node.army_pieces.remove(p)
                
            self.app.combat_marching_army = selected_pieces
            self.close_panel()
            self.map_screen.start_marching(self.current_node)
        else:
            tax = self.app.tax_points[self.current_node.faction]
            if tax < 7: return
            self.app.tax_points[self.current_node.faction] -= 7
            
            targets = ['queen', 'rook', 'rook', 'bishop', 'bishop', 'knight', 'knight'] + ['pawn']*8
            for p_name in targets:
                headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
                heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
                heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
                if len(self.current_node.army_pieces) >= (16 if headers > 0 else 8): break
                
                actual_p = p_name
                if p_name in ['queen', 'rook', 'bishop', 'knight'] and heavies >= 9:
                    actual_p = 'pawn'
                    
                self.current_node.army_pieces.append(generate_piece(actual_p, self.current_node.faction, self.app))
            self.switch_tab('recruit')

# ----------------- คลาส MapNode -----------------
class MapNode(Button):
    def __init__(self, node_type, faction, node_id, is_main_base=False, app=None, **kwargs):
        super().__init__(**kwargs)
        self.node_type = node_type 
        self.faction = faction     
        self.node_id = node_id
        self.is_main_base = is_main_base 
        self.neighbors = []             
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        self.background_color = (0, 0, 0, 0) 
        
        self.loyalty = 100 

        self.army_pieces = []
        if app:
            if self.is_main_base:
                pieces_to_gen = ['king', 'queen', 'rook', 'rook', 'bishop', 'bishop', 'knight', 'knight'] + ['pawn']*8
                for pt in pieces_to_gen: self.army_pieces.append(generate_piece(pt, faction, app))
            elif faction == 'red':
                if node_type == 'castle':
                    pieces_to_gen = ['king', 'queen', 'rook', 'rook', 'bishop', 'bishop', 'knight', 'knight'] + ['pawn']*8
                else:
                    pieces_to_gen = ['king', 'rook', 'bishop', 'knight'] + ['pawn']*8
                for pt in pieces_to_gen: self.army_pieces.append(generate_piece(pt, faction, app))

        self.update_graphics()
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_graphics(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_main_base:
                Color(1, 0.8, 0, 0.4)
                self.aura = Ellipse(pos=(self.x - dp(10), self.y - dp(10)), size=(self.width + dp(20), self.height + dp(20)))
            else:
                self.aura = None

            if self.node_type == 'castle':
                self.color_inst = Color(0.5, 0.5, 0.55, 1)
                self.shape = Rectangle(pos=self.pos, size=self.size)
            else:
                self.color_inst = Color(0.85, 0.85, 0.85, 1)
                self.shape = Ellipse(pos=self.pos, size=self.size)
                
            if self.faction == 'white': fac_color = (0.9, 0.9, 0.9, 1)
            elif self.faction == 'black': fac_color = (0.1, 0.1, 0.1, 1)
            else: fac_color = (0.8, 0.2, 0.2, 1) 
            
            Color(*fac_color)
            self.border_line = Line(circle=(self.center_x, self.center_y, dp(28)), width=3)

    def update_canvas(self, *args):
        if hasattr(self, 'shape'):
            self.shape.pos, self.shape.size = self.pos, self.size
            self.border_line.circle = (self.center_x, self.center_y, dp(28))
            if self.aura: self.aura.pos, self.aura.size = (self.x - dp(10), self.y - dp(10)), (self.width + dp(20), self.height + dp(20))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        map_screen = app.root.get_screen('campaign_map')
        
        if map_screen.marching_from_node:
            if self in map_screen.marching_from_node.neighbors:
                if self.faction == map_screen.marching_from_node.faction:
                    headers = sum(1 for p in self.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
                    m_headers = sum(1 for p in app.combat_marching_army if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
                    max_cap = 16 if (headers + m_headers) > 0 else 8
                    
                    if len(self.army_pieces) + len(app.combat_marching_army) <= max_cap:
                        self.army_pieces.extend(app.combat_marching_army)
                        app.combat_marching_army = []
                        map_screen.status_lbl.text = "[color=00ff00]ARMY MERGED SUCCESSFUL![/color]"
                    else:
                        map_screen.status_lbl.text = "[color=ff0000]MERGE FAILED: CAPACITY LIMIT EXCEEDED![/color]"
                        map_screen.marching_from_node.army_pieces.extend(app.combat_marching_army)
                else:
                    fatigue_cost = 2 if self.node_type == 'castle' else 1
                    current_fatigue = app.army_fatigue.get(map_screen.marching_from_node.faction, 0)
                    app.army_fatigue[map_screen.marching_from_node.faction] = min(4, current_fatigue + fatigue_cost)
                    
                    map_screen.initiate_combat(map_screen.marching_from_node, self)
            else: 
                map_screen.status_lbl.text = "[color=ff0000]TOO FAR! SELECT ADJACENT BASE.[/color]"
                map_screen.marching_from_node.army_pieces.extend(app.combat_marching_army) 
            
            map_screen.marching_from_node = None 
            return

        current_turn = getattr(app, 'current_map_turn', 'white')
        if self.faction == current_turn:
            if self.is_main_base and app.prince_rewards.get(self.faction, 0) > 0:
                app.prince_rewards[self.faction] -= 1
                self.army_pieces.append(generate_piece('prince', self.faction, app))
            map_screen.army_panel.open_for_node(self)
        else:
            map_screen.status_lbl.text = "[color=ff0000]ENEMY TERRITORY. SELECT YOUR BASE TO ATTACK FROM.[/color]"


# ----------------- คลาสหลัก CampaignMapScreen -----------------
class CampaignMapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.map_content = FloatLayout(size_hint=(None, None), size=(9600, 5400))
        self.scroll_view.add_widget(self.map_content)
        self.ui_layer = FloatLayout()
        
        self.add_widget(self.scroll_view)
        self.add_widget(self.ui_layer)
        
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9); self.top_bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=self._update_top_bg, size=self._update_top_bg)
            
        back_btn = Button(text="< SETUP", size_hint_x=0.1, background_color=(0.5, 0.1, 0.1, 1))
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        jump_btn = Button(text="📍 BASE", size_hint_x=0.1, background_color=(0.2, 0.5, 0.8, 1))
        jump_btn.bind(on_release=self.jump_to_base)
        top_bar.add_widget(jump_btn)
        
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - TURN 1", bold=True, color=(1, 0.8, 0.2, 1), font_size='18sp', markup=True)
        top_bar.add_widget(self.status_lbl)
        
        next_btn = Button(text="END TURN >", size_hint_x=0.15, background_color=(0.2, 0.6, 0.2, 1))
        next_btn.bind(on_release=self.end_turn)
        top_bar.add_widget(next_btn)
        
        self.ui_layer.add_widget(top_bar)
        
        self.nodes_list = []
        self.marching_from_node = None 

    def _update_top_bg(self, instance, value):
        self.top_bg.pos, self.top_bg.size = instance.pos, instance.size

    def jump_to_base(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()
            
        target_node = None
        for n in self.nodes_list:
            if n.faction == app.current_map_turn and n.is_main_base:
                target_node = n
                break
                
        if target_node:
            x_ratio = target_node.x / self.map_content.width
            y_ratio = target_node.y / self.map_content.height
            self.scroll_view.scroll_x = x_ratio
            self.scroll_view.scroll_y = y_ratio

    def on_enter(self):
        app = App.get_running_app()
        
        if not hasattr(self, 'army_panel'):
            self.army_panel = CampaignArmyPanel(self, app)
            self.ui_layer.add_widget(self.army_panel)

        if not getattr(app, 'campaign_initialized', False):
            app.current_map_turn = 'white'
            app.turn_number = 1
            app.tax_points = {'white': 0, 'black': 0}
            app.prince_rewards = {'white': 0, 'black': 0} 
            app.army_fatigue = {'white': 0, 'black': 0} 
            # ✨ สร้าง Set เริ่มต้นสำหรับเก็บยูนิตที่ปลดล็อคแล้ว (ตัวเบสิกจะมีมาให้แต่แรก)
            app.unlocked_units = {
                'white': {'pawn', 'levies', 'menatarm', 'knight', 'bishop', 'rook', 'queen'},
                'black': {'pawn', 'levies', 'menatarm', 'knight', 'bishop', 'rook', 'queen'}
            }
            self.marching_from_node = None
            Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)
            app.campaign_initialized = True
        else:
            self.marching_from_node = None
            
            if getattr(app, 'battle_finished', False):
                src = app.combat_source
                tgt = app.combat_target
                winner = app.battle_winner
                
                clean_atk = [clone_piece(p, src.faction, app) for p in app.survivors_atk]
                clean_def = [clone_piece(p, tgt.faction, app) for p in app.survivors_def]
                
                if winner == 'attacker':
                    orig_tgt_faction = tgt.faction
                    tgt.faction = src.faction
                    tgt.army_pieces = clean_atk
                    tgt.loyalty = 100 
                    tgt.update_graphics() 
                    
                    if tgt.node_type == 'castle' and orig_tgt_faction == 'red':
                        app.prince_rewards[src.faction] += 1
                        
                    self.status_lbl.text = f"[color=00ff00]VICTORY! YOU CAPTURED {tgt.node_id}.[/color]"
                elif winner == 'defender':
                    tgt.army_pieces = clean_def
                    src.army_pieces.extend(clean_atk) 
                    self.status_lbl.text = f"[color=ff0000]DEFEAT! YOUR ARMY RETREATED TO {src.node_id}.[/color]"
                else:
                    tgt.army_pieces = clean_def
                    src.army_pieces.extend(clean_atk) 
                    
                app.battle_finished = False

    def go_back(self, instance):
        app = App.get_running_app()
        app.campaign_initialized = False 
        self.manager.current = 'setup'

    def start_marching(self, source_node):
        self.marching_from_node = source_node
        self.status_lbl.text = "[color=00ffff]SELECT ADJACENT TARGET TO MARCH / ATTACK...[/color]"

    def initiate_combat(self, source_node, target_node):
        app = App.get_running_app()
        app.combat_source = source_node
        app.combat_target = target_node
        
        target_army = target_node.army_pieces.copy()
        ensure_header(target_army, target_node.faction, app) 
        
        if target_node.faction == 'red':
            target_count = random.randint(8, 12)
            while len(target_army) > target_count:
                removable_pieces = [p for p in target_army if p.__class__.__name__.lower() not in ['king']]
                if not removable_pieces: break
                p_to_remove = random.choice(removable_pieces)
                target_army.remove(p_to_remove)
                
        app.combat_target_army = target_army
        ensure_header(app.combat_marching_army, source_node.faction, app)
        
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(mode='Divide_Conquer')
        self.manager.current = 'gameplay'

    def switch_turn(self):
        app = App.get_running_app()
        if app.current_map_turn == 'white':
            app.current_map_turn = 'black'
            self.status_lbl.text = f"DARK ABYSS (BLACK) - TURN {app.turn_number}"
            self.status_lbl.color = (0.6, 0.6, 0.8, 1)
        else:
            app.current_map_turn = 'white'
            app.turn_number += 1
            self.status_lbl.text = f"DIVINE ORDER (WHITE) - TURN {app.turn_number}"
            self.status_lbl.color = (1, 0.8, 0.2, 1)
            
        current_fatigue = app.army_fatigue.get(app.current_map_turn, 0)
        app.army_fatigue[app.current_map_turn] = max(0, current_fatigue - 3)
        
        self.jump_to_base(None)

    def trigger_rebellion(self, node):
        app = App.get_running_app()
        app.play_click_sound()
        self.status_lbl.text = f"[color=ff0000]REBELLION AT {node.node_id}! DEFEND YOUR BASE![/color]"
        
        rebel_army = [generate_piece('king', 'red', app), generate_piece('knight', 'red', app), generate_piece('rook', 'red', app)]
        for _ in range(5): rebel_army.append(generate_piece('pawn', 'red', app))
            
        dummy_red_node = MapNode('village', 'red', 'REBEL', app=None)
        dummy_red_node.army_pieces = rebel_army
        
        app.combat_source = dummy_red_node
        app.combat_marching_army = rebel_army
        app.combat_target = node
        
        target_army = node.army_pieces.copy()
        ensure_header(target_army, node.faction, app)
        app.combat_target_army = target_army
        
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(mode='Divide_Conquer')
        self.manager.current = 'gameplay'

    def end_turn(self, instance):
        app = App.get_running_app()
        app.play_click_sound()
        if self.marching_from_node:
            self.marching_from_node.army_pieces.extend(app.combat_marching_army)
            self.marching_from_node = None
        
        tax_collected = 0
        rebellions = []
        
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                tax_collected += 3 if node.node_type == 'village' else 6
                
                if len(node.army_pieces) < 3: node.loyalty -= 20
                else: node.loyalty += 10
                
                node.loyalty = max(0, min(100, node.loyalty))
                if node.loyalty == 0:
                    rebellions.append(node)
                
        app.tax_points[app.current_map_turn] += tax_collected
        
        if rebellions:
            node = rebellions[0]
            node.loyalty = 50 
            self.switch_turn() 
            self.trigger_rebellion(node)
            return

        self.switch_turn()

    def generate_procedural_map(self):
        self.map_content.clear_widgets()
        self.map_content.canvas.before.clear()
        self.nodes_list.clear()
        
        app = App.get_running_app()
        size_val = getattr(app, 'selected_board', 'Size_S')
        num_castles, num_villages = {'Size_S':(1,2), 'Size_M':(2,3), 'Size_L':(3,4)}.get(size_val, (1,2))
        map_w, map_h = 9600, 5400
        water_rects, nodes_data = [], []

        with self.map_content.canvas.before:
            Color(0.12, 0.18, 0.12, 1)
            Rectangle(pos=(0, 0), size=(map_w, map_h))
            
            Color(0.1, 0.4, 0.6, 0.6)
            for _ in range(150):
                w, h = random.randint(200, 700), random.randint(200, 700)
                x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                if not is_overlapping_any((x, y, w, h), water_rects):
                    water_rects.append((x, y, w, h))
                    Rectangle(pos=(x, y), size=(w, h))

            Color(0.08, 0.35, 0.15, 0.7) 
            for _ in range(250):
                w, h = random.randint(150, 400), random.randint(150, 400)
                x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                if not is_overlapping_any((x, y, w, h), water_rects):
                    Rectangle(pos=(x, y), size=(w, h))

        def generate_nodes_for_faction(base_faction, count_castles, count_villages, min_x, max_x):
            faction_nodes = []
            types_to_spawn = ['castle'] * count_castles + ['village'] * count_villages
            for i, n_type in enumerate(types_to_spawn):
                for attempt in range(500):
                    nx, ny = random.randint(min_x, max_x), random.randint(300, map_h - 300)
                    if is_overlapping_any((nx-80, ny-80, 160, 160), water_rects): continue
                    too_close = any(get_distance((nx, ny), ex['pos']) < dp(200) for ex in nodes_data + faction_nodes)
                    if not too_close:
                        is_main = (i == 0)
                        faction_nodes.append({'pos': (nx, ny), 'faction': base_faction if is_main else 'red', 'type': n_type, 'id': f"{base_faction[0].upper()}{i}", 'main': is_main})
                        break
            return faction_nodes

        w_nodes = generate_nodes_for_faction('white', num_castles, num_villages, 500, 4000)
        b_nodes = generate_nodes_for_faction('black', num_castles, num_villages, 5600, 9100)
        nodes_data = w_nodes + b_nodes

        nodes_dict = {}
        for data in nodes_data:
            node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'], app=app)
            node.base_pos = data['pos']
            node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
            self.nodes_list.append(node)
            nodes_dict[data['id']] = node

        def create_connections(nodes):
            edges = []
            if not nodes: return edges
            visited, unvisited = [nodes[0]], nodes[1:]
            while unvisited:
                min_dist, best_edge, best_u = float('inf'), None, None
                for v in visited:
                    for u in unvisited:
                        dist = get_distance(v['pos'], u['pos'])
                        if dist < min_dist: min_dist, best_edge, best_u = dist, (v, u), u
                edges.append(best_edge); visited.append(best_u); unvisited.remove(best_u)
            for _ in range(len(nodes) // 2):
                u, v = random.sample(nodes, 2)
                if (u, v) not in edges and (v, u) not in edges: edges.append((u, v))
            return edges

        white_edges = create_connections(w_nodes)
        black_edges = create_connections(b_nodes)
        
        min_cross, cross_edge = float('inf'), None
        for w in w_nodes:
            for b in b_nodes:
                d = get_distance(w['pos'], b['pos'])
                if d < min_cross: min_cross, cross_edge = d, (w, b)

        with self.map_content.canvas.before:
            Color(0.85, 0.75, 0.3, 0.8)
            for u, v in white_edges + black_edges:
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4)
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])
            if cross_edge:
                u, v = cross_edge
                Color(0.9, 0.4, 0.2, 0.9)
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=8)
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])

        for node in self.nodes_list: self.map_content.add_widget(node)
        self.scroll_view.scroll_x, self.scroll_view.scroll_y = 0.5, 0.5
        self.jump_to_base(None)