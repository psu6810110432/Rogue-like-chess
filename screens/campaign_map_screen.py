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
    return new_p

def ensure_header(army_list, faction, app):
    has_header = any(p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' for p in army_list)
    if not has_header:
        commander = generate_piece('king', faction, app)
        commander.name = "Garrison Commander"
        army_list.append(commander)

# ----------------- UI การ์ดทหารสไตล์ Total War -----------------
class PieceCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_obj, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(110), **kwargs)
        self.piece_obj = piece_obj
        self.is_selected = False
        
        with self.canvas.before:
            Color(0.12, 0.12, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            self.border_color = Color(0.3, 0.3, 0.35, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)], width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)

        p_name = piece_obj.__class__.__name__.lower()
        tribe = getattr(piece_obj, 'tribe', 'the knight company')
        color = piece_obj.color
        
        # ✨ อัปเดต Path เป็นโฟลเดอร์แบบใหม่ (/1base/)
        if p_name in ['pawn', 'hastati', 'levies']:
            num = getattr(piece_obj, 'variant', 1)
            filename = f"{p_name}{num}.png"
        else:
            filename = f"{p_name}.png"
            
        if getattr(piece_obj, 'name', '') == 'Prince': filename = 'prince.png'
        
        img_path = f"assets/pieces/{tribe}/{color}/1base/{filename}"
        
        self.add_widget(Image(source=img_path, size_hint=(0.7, 0.6), pos_hint={'center_x': 0.5, 'top': 0.9}))
        display_name = getattr(piece_obj, 'name', p_name.capitalize())
        self.add_widget(Label(text=f"[b]{display_name}[/b]", markup=True, font_size='13sp', pos_hint={'center_x': 0.5, 'y': 0.15}, size_hint=(1, 0.2)))
        
        hp = getattr(piece_obj, 'hidden_passive', None)
        passive_text = hp.description if hp and hp.passive_type else "No Passive"
        self.add_widget(Label(text=f"[size=10sp][color=a0a0a0]{passive_text}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

        if getattr(piece_obj, 'item', None):
            self.add_widget(Image(source=piece_obj.item.image_path, size_hint=(0.35, 0.35), pos_hint={'right': 0.95, 'top': 0.95}))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(8)]

    def on_release(self):
        App.get_running_app().play_click_sound()
        self.is_selected = not self.is_selected
        self.border_color.rgba = (1, 0.8, 0, 1) if self.is_selected else (0.3, 0.3, 0.35, 1)
        self.border_line.width = 2.5 if self.is_selected else 1.5

class RecruitCard(ButtonBehavior, FloatLayout):
    def __init__(self, piece_name, cost, faction, app, click_cb, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(110), **kwargs)
        self.click_cb = click_cb
        self.piece_name = piece_name
        self.cost = cost
        
        with self.canvas.before:
            Color(0.12, 0.2, 0.12, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)], width=1.5)
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
        
        # ✨ อัปเดต Path เป็นโฟลเดอร์แบบใหม่ (/1base/)
        if piece_name in ['pawn', 'hastati', 'levies']:
            filename = f"{piece_name}1.png"
        else:
            filename = f"{piece_name}.png"
            
        img_path = f"assets/pieces/{tribe}/{faction}/1base/{filename}"
        
        self.add_widget(Image(source=img_path, size_hint=(0.7, 0.6), pos_hint={'center_x': 0.5, 'top': 0.9}))
        self.add_widget(Label(text=f"[b]{piece_name.capitalize()}[/b]", markup=True, font_size='13sp', pos_hint={'center_x': 0.5, 'y': 0.15}, size_hint=(1, 0.2)))
        self.add_widget(Label(text=f"[size=12sp][color=ffff00]Cost: {cost}[/color][/size]", markup=True, pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(1, 0.15)))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(8)]

    def on_release(self):
        self.click_cb(self.piece_name, self.cost)


# ----------------- UI แถบซ้ายล่าง (Total War Army Panel) -----------------
class CampaignArmyPanel(FloatLayout):
    def __init__(self, map_screen, app, **kwargs):
        super().__init__(size_hint=(0.85, None), height=dp(200), pos_hint={'x': 0.02, 'y': -0.5}, **kwargs) 
        self.map_screen = map_screen
        self.app = app
        self.current_node = None
        self.current_tab = 'army'

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.bg = RoundedRectangle(radius=[dp(12)])
            self.border_color = Color(0.5, 0.5, 0.5, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(12)], width=2)
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
        self.btn_action = Button(text="[b]MARCH / ATTACK[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1))
        self.btn_action.bind(on_release=self.execute_action)
        self.btn_return = Button(text="[b]RETURN BASE[/b]", markup=True, background_color=(0.2, 0.4, 0.8, 1))
        self.btn_return.bind(on_release=self.return_to_base)
        
        self.action_box.add_widget(self.btn_action)
        self.action_box.add_widget(self.btn_return)
        self.add_widget(self.action_box)

        self.piece_cards = []

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]

    def open_for_node(self, node):
        from kivy.animation import Animation
        self.current_node = node
        self.header_lbl.text = f"{node.faction.upper()} {node.node_type.upper()}"
        
        if node.faction == 'white': self.border_color.rgba = (0.9, 0.9, 0.9, 1)
        elif node.faction == 'black': self.border_color.rgba = (0.3, 0.3, 0.4, 1)
        
        self.switch_tab('army')
        Animation(pos_hint={'y': 0.02}, duration=0.3, t='out_quad').start(self)

    def close_panel(self, *args):
        from kivy.animation import Animation
        self.app.play_click_sound()
        Animation(pos_hint={'y': -0.5}, duration=0.2).start(self)

    def switch_tab(self, tab_name):
        self.app.play_click_sound()
        self.current_tab = tab_name
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
            
            # ✨ นำค่า Fatigue มาแสดงผล
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            fatigue_color = '00ff00' if fatigue == 0 else ('ffaa00' if fatigue < 3 else 'ff0000')
            self.status_lbl.text = f"Loyalty: [color={color_lylt}]{lylt}%[/color] | Cap: [b]{total}/{max_cap}[/b] | Fatigue: [color={fatigue_color}]{fatigue}/4[/color]"
            
            self.btn_action.text = "[b]MARCH / ATTACK[/b]"
            self.btn_action.background_color = (0.8, 0.2, 0.2, 1)
            
            self.btn_return.opacity = 1
            self.btn_return.disabled = False
            
            for p in self.current_node.army_pieces:
                card = PieceCard(p)
                self.piece_cards.append(card)
                self.content_grid.add_widget(card)
        else:
            self.btn_tab_army.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_recruit.background_color = (0.3, 0.8, 0.3, 1)
            self.status_lbl.text = f"Tax: [color=00ff00]{self.app.tax_points[self.current_node.faction]}[/color] | Cap: {total}/{max_cap}"
            
            self.btn_action.text = "[b]QUICK RECRUIT\n(7 TAX)[/b]"
            self.btn_action.background_color = (0.8, 0.6, 0.1, 1)
            
            self.btn_return.opacity = 0
            self.btn_return.disabled = True
            
            can_heavy = (self.current_node.node_type == 'castle')
            units_to_sell = [
                ('princess', 2), ('menatarm', 2), ('praetorian', 2), ('royalguard', 2),
                ('queen', 2), ('rook', 2), ('bishop', 2), ('knight', 2), 
                ('hastati', 1), ('levies', 1), ('pawn', 1)
            ]
            for p_name, cost in units_to_sell:
                if cost == 2 and not can_heavy: continue
                card = RecruitCard(p_name, cost, self.current_node.faction, self.app, self.buy_piece)
                self.content_grid.add_widget(card)

    def buy_piece(self, piece_name, cost):
        self.app.play_click_sound()
        tax = self.app.tax_points[self.current_node.faction]
        if tax < cost: return
        
        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
        heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
        heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
        max_cap = 16 if headers > 0 else 8
        if len(self.current_node.army_pieces) >= max_cap: return
        
        if piece_name in ['pawn', 'hastati', 'levies'] and heavies > 9: return 
        
        self.app.tax_points[self.current_node.faction] -= cost
        new_p = generate_piece(piece_name, self.current_node.faction, self.app)
        self.current_node.army_pieces.append(new_p)
        self.switch_tab('recruit') 

    def execute_action(self, instance):
        self.app.play_click_sound()
        if self.current_tab == 'army':
            # ✨ เช็ค Fatigue ถ้ามากกว่าหรือเท่ากับ 3 จะเดินทัพไม่ได้
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

    def return_to_base(self, instance):
        self.app.play_click_sound()
        if self.current_tab != 'army' or self.current_node.is_main_base: return
        
        selected_pieces = [card.piece_obj for card in self.piece_cards if card.is_selected]
        if len(selected_pieces) == 0:
            selected_pieces = self.current_node.army_pieces.copy()
            
        if len(selected_pieces) == 0: return
        
        main_base = None
        for n in self.map_screen.nodes_list:
            if n.faction == self.current_node.faction and n.is_main_base:
                main_base = n
                break
                
        if main_base:
            for p in selected_pieces:
                self.current_node.army_pieces.remove(p)
                main_base.army_pieces.append(p)
            self.close_panel()
            self.map_screen.status_lbl.text = f"[color=00ff00]ARMY RETURNED TO CAPITAL ({main_base.node_id})![/color]"

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
                    # ✨ เช็คการเข้าโจมตี เพิ่ม Fatigue ตาม node_type
                    fatigue_cost = 2 if self.node_type == 'castle' else 1
                    current_fatigue = app.army_fatigue.get(map_screen.marching_from_node.faction, 0)
                    
                    # เพิ่ม Fatigue (สูงสุดคือ 4)
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
            app.army_fatigue = {'white': 0, 'black': 0} # ✨ สร้างตัวแปรเก็บ Fatigue
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
            
        # ✨ ล้างค่า Fatigue เมื่อเข้าเทิร์นใหม่ (-3 หน่วย แต่ไม่ต่ำกว่า 0)
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