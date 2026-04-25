# components/map_node.py
import random
import math
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

def get_active_addons_list(addons_dict):
    active = []
    if addons_dict.get('farm', 0) > 0: active.append(('farm', addons_dict['farm']))
    if addons_dict.get('tavern', 0) > 0: active.append(('tavern', addons_dict['tavern']))
    if addons_dict.get('special'): active.append((addons_dict['special'], addons_dict.get('special_lvl', 1)))
    return active

class MapNode(Button):
    def __init__(self, node_type, faction, node_id, is_main_base=False, app=None, **kwargs):
        super().__init__(**kwargs)
        self.node_type = node_type 
        self.faction = faction     
        self.node_id = node_id
        self.is_main_base = is_main_base 
        self.neighbors = []             
        self.size_hint = (None, None)
        self.size = (dp(70), dp(70)) # ✨ ขยายขนาดรูปฐานหลัก
        self.background_color = (0, 0, 0, 0) 
        self.is_selected_node = False 
        
        self.loyalty = 100 
        self.army_pieces = []

        self.addons = {
            'farm': 1,
            'tavern': 1,
            'special': roll_special_addon(),
            'special_lvl': 1
        }

        self.sub_villages = []
        if self.node_type == 'castle':
            num_subs = random.randint(1, 3)
            angles = [30, 150, 270] 
            for i in range(num_subs):
                angle = math.radians(angles[i] + random.uniform(-15, 15))
                dist = dp(random.uniform(110, 140)) # ✨ เพิ่มระยะห่างให้เกิดช่องว่าง > 30px
                self.sub_villages.append({
                    'id': f"V{i+1}",
                    'rel_pos': (math.cos(angle) * dist, math.sin(angle) * dist),
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
        
        # จัดเตรียมข้อมูล Addon สำหรับวาดกราฟิก
        self.addon_data = []
        main_addons = get_active_addons_list(self.addons)
        a_step = 360 / max(1, len(main_addons))
        offset = 90 if self.node_type == 'castle' else 0
        for i, (a_name, a_lvl) in enumerate(main_addons):
            angle = math.radians(i * a_step + offset)
            dist = dp(90) # ระยะห่าง Addon ฐานหลัก
            self.addon_data.append({
                'name': a_name, 'lvl': a_lvl,
                'rel_pos': (math.cos(angle)*dist, math.sin(angle)*dist)
            })

        for sv in self.sub_villages:
            sv['addon_data'] = []
            sv_addons = get_active_addons_list(sv['addons'])
            sv_step = 360 / max(1, len(sv_addons))
            for i, (a_name, a_lvl) in enumerate(sv_addons):
                sv_angle = math.atan2(sv['rel_pos'][1], sv['rel_pos'][0])
                angle = sv_angle + math.radians(-90 + i * sv_step)
                dist = dp(70) # ระยะห่าง Addon หมู่บ้านย่อย
                sv['addon_data'].append({
                    'name': a_name, 'lvl': a_lvl,
                    'rel_pos': (math.cos(angle)*dist, math.sin(angle)*dist)
                })

        with self.canvas.before:
            if self.is_main_base:
                Color(1, 0.8, 0, 0.4)
                self.aura = Ellipse(size=(self.width + dp(30), self.height + dp(30)))
            else:
                self.aura = None

            # ✨ วาดเส้นทาง (Paths) สีน้ำตาลอ่อน
            Color(0.4, 0.3, 0.2, 1)
            
            self.sv_lines = []
            for sv in self.sub_villages:
                l = Line(width=1.5)
                self.sv_lines.append((l, sv['rel_pos']))
                
                sv['a_lines'] = []
                for ad in sv['addon_data']:
                    al = Line(width=1)
                    sv['a_lines'].append((al, sv['rel_pos'], ad['rel_pos']))

            self.main_a_lines = []
            for ad in self.addon_data:
                al = Line(width=1.5)
                self.main_a_lines.append((al, ad['rel_pos']))
                
            Color(1, 1, 1, 1) # Reset color for Images
            
            # ✨ วาดหมู่บ้านย่อยและ Addon
            self.sv_rects = []
            for sv in self.sub_villages:
                sv['a_rects'] = []
                for ad in sv['addon_data']:
                    folder = "base1" if ad['lvl'] <= 1 else ("up1" if ad['lvl'] == 2 else "up2")
                    img_path = f"assets/structure/addon/{folder}/{ad['name']}.png"
                    rect = Rectangle(source=img_path, size=(dp(25), dp(25)))
                    sv['a_rects'].append((rect, sv['rel_pos'], ad['rel_pos']))

                img_path = f"assets/structure/base/village/village_{self.faction}.png"
                rect = Rectangle(source=img_path, size=(dp(45), dp(45)))
                self.sv_rects.append((rect, sv['rel_pos']))

            # ✨ วาด Addon ฐานหลัก
            self.main_a_rects = []
            for ad in self.addon_data:
                folder = "base1" if ad['lvl'] <= 1 else ("up1" if ad['lvl'] == 2 else "up2")
                img_path = f"assets/structure/addon/{folder}/{ad['name']}.png"
                rect = Rectangle(source=img_path, size=(dp(30), dp(30)))
                self.main_a_rects.append((rect, ad['rel_pos']))
                
            # ✨ วาดฐานหลัก
            main_img = f'assets/structure/base/{self.node_type}/{self.node_type}_{self.faction}.png'
            self.shape = Rectangle(source=main_img, size=self.size)

            # วาดเส้นขอบวงกลมแสดงสถานะ (เลือก/ไม่เลือก)
            if self.is_selected_node:
                Color(0.2, 0.5, 1.0, 1)
                self.border_line = Line(width=3)
            else:
                if self.faction == 'white': fac_color = (0.9, 0.9, 0.9, 1)
                elif self.faction == 'black': fac_color = (0.1, 0.1, 0.1, 1)
                else: fac_color = (0.8, 0.2, 0.2, 1) 
                Color(*fac_color)
                self.border_line = Line(width=2)

    def update_canvas(self, *args):
        cx, cy = self.center_x, self.center_y
        
        if self.aura:
            self.aura.pos = (self.x - dp(15), self.y - dp(15))
            self.aura.size = (self.width + dp(30), self.height + dp(30))
        
        # จัดตำแหน่งเส้นทางเชื่อมต่อให้ยึดติดกับจุดศูนย์กลาง
        for l, rpos in self.sv_lines:
            l.points = [cx, cy, cx + rpos[0], cy + rpos[1]]
            
        for sv in self.sub_villages:
            for al, svrpos, arpos in sv.get('a_lines', []):
                vx, vy = cx + svrpos[0], cy + svrpos[1]
                al.points = [vx, vy, vx + arpos[0], vy + arpos[1]]
                
        for al, rpos in self.main_a_lines:
            al.points = [cx, cy, cx + rpos[0], cy + rpos[1]]
            
        # จัดตำแหน่งรูปภาพทั้งหมด (หักลบจุดกึ่งกลางของรูป)
        for sv in self.sub_villages:
            for rect, svrpos, arpos in sv.get('a_rects', []):
                rect.pos = (cx + svrpos[0] + arpos[0] - dp(12.5), cy + svrpos[1] + arpos[1] - dp(12.5))
        
        for rect, rpos in self.sv_rects:
            rect.pos = (cx + rpos[0] - dp(22.5), cy + rpos[1] - dp(22.5))
            
        for rect, rpos in self.main_a_rects:
            rect.pos = (cx + rpos[0] - dp(15), cy + rpos[1] - dp(15))
            
        if hasattr(self, 'shape'):
            self.shape.pos = self.pos
            self.shape.size = self.size
            
        radius = dp(45) if self.is_selected_node else dp(40)
        self.border_line.circle = (cx, cy, radius)

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