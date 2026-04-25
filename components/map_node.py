# components/map_node.py
import random
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.app import App

from logic.campaign_helpers import generate_piece

def roll_special_addon():
    roll = random.randint(1, 100)
    if roll <= 50: return None
    elif roll <= 70: return 'mine'
    elif roll <= 75: return 'blacksmith'
    elif roll <= 80: return 'weaponsmith'
    elif roll <= 85: return 'guard'
    else: return 'statue'

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
        self.is_selected_node = False 
        
        self.loyalty = 100 
        self.army_pieces = []

        # ✨ ระบบ Addon ของเมืองหลัก
        self.addons = {
            'farm': 1,
            'tavern': 1,
            'special': roll_special_addon(),
            'special_lvl': 1
        }

        # ✨ ระบบปราสาทมีหมู่บ้านบริวาร (Sub-villages) 1-3 แห่ง
        self.sub_villages = []
        if self.node_type == 'castle':
            num_subs = random.randint(1, 3)
            for i in range(num_subs):
                self.sub_villages.append({
                    'id': f"V{i+1}",
                    'addons': {
                        'farm': 1, 'tavern': 1, 
                        'special': roll_special_addon(), 'special_lvl': 1
                    }
                })

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
                
            if self.is_selected_node:
                Color(0.2, 0.5, 1.0, 1)
                self.border_line = Line(circle=(self.center_x, self.center_y, dp(32)), width=4)
            else:
                if self.faction == 'white': fac_color = (0.9, 0.9, 0.9, 1)
                elif self.faction == 'black': fac_color = (0.1, 0.1, 0.1, 1)
                else: fac_color = (0.8, 0.2, 0.2, 1) 
                
                Color(*fac_color)
                self.border_line = Line(circle=(self.center_x, self.center_y, dp(28)), width=3)

    def update_canvas(self, *args):
        if hasattr(self, 'shape'):
            self.shape.pos, self.shape.size = self.pos, self.size
            
            radius = dp(32) if self.is_selected_node else dp(28)
            self.border_line.circle = (self.center_x, self.center_y, radius)
            if self.aura: self.aura.pos, self.aura.size = (self.x - dp(10), self.y - dp(10)), (self.width + dp(20), self.height + dp(20))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        map_screen = app.root.get_screen('campaign_map')
        
        if map_screen.marching_from_node:
            if self in map_screen.marching_from_node.neighbors:
                if self.faction == map_screen.marching_from_node.faction:
                    headers = sum(1 for p in self.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False))
                    m_headers = sum(1 for p in app.combat_marching_army if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False))
                    max_cap = 16 if (headers + m_headers) > 0 else 8
                    
                    if len(self.army_pieces) + len(app.combat_marching_army) <= max_cap:
                        self.army_pieces.extend(app.combat_marching_army)
                        app.combat_marching_army = []
                        map_screen.status_lbl.text = "[color=00ff00]ARMY MERGED SUCCESSFUL![/color]"
                        
                        current_fatigue = app.army_fatigue.get(map_screen.marching_from_node.faction, 0)
                        app.army_fatigue[map_screen.marching_from_node.faction] = min(6, current_fatigue + 1)
                    else:
                        map_screen.status_lbl.text = "[color=ff0000]MERGE FAILED: CAPACITY LIMIT EXCEEDED![/color]"
                        map_screen.marching_from_node.army_pieces.extend(app.combat_marching_army)
                else:
                    fatigue_cost = 2 if self.node_type == 'castle' else 1
                    current_fatigue = app.army_fatigue.get(map_screen.marching_from_node.faction, 0)
                    app.army_fatigue[map_screen.marching_from_node.faction] = min(6, current_fatigue + fatigue_cost)
                    
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