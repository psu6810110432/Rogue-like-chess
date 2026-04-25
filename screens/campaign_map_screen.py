# screens/campaign_map_screen.py
import random
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
# ✨ เพิ่ม Line และ Ellipse กลับเข้ามาตรงนี้
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.modalview import ModalView

# Import Components & Helpers ที่แยกออกมา
from logic.campaign_helpers import is_overlapping_any, get_distance, generate_piece, clone_piece, ensure_header, clear_temp_headers
from components.campaign_panel import CampaignArmyPanel
from components.map_node import MapNode


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

    def show_game_over(self, winner_faction, reason="MAIN BASE CAPTURED"):
        if hasattr(self, 'army_panel'):
            self.army_panel.close_panel()
            
        pop = ModalView(size_hint=(0.6, 0.4), auto_dismiss=False, background_color=(0,0,0,0.8))
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        with box.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            bg_rect = RoundedRectangle(radius=[dp(15)])
            
        def update_bg(*args):
            bg_rect.pos = box.pos
            bg_rect.size = box.size
            
        box.bind(pos=update_bg, size=update_bg)
                 
        box.add_widget(Label(text=f"[b][color=ffcc00]{winner_faction.upper()} WINS THE CAMPAIGN![/color][/b]", markup=True, font_size='24sp'))
        box.add_widget(Label(text=f"REASON: {reason}", font_size='16sp'))
        
        btn = Button(text="RETURN TO MENU", size_hint_y=0.4, background_color=(0.8, 0.2, 0.2, 1))
        btn.bind(on_release=lambda x: (pop.dismiss(), self.go_back(None)))
        box.add_widget(btn)
        
        pop.add_widget(box)
        pop.open()

    def get_nearest_friendly_base(self, node):
        best_node, min_d = None, float('inf')
        for n in self.nodes_list:
            if n.faction == node.faction and n != node:
                d = get_distance(n.base_pos, node.base_pos)
                if d < min_d:
                    min_d = d
                    best_node = n
        return best_node

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
                clear_temp_headers(clean_atk)
                clear_temp_headers(clean_def)
                
                def had_real_king(army): return any(p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' for p in army) and not any(getattr(p, 'is_header', False) for p in army)
                
                atk_had_king = had_real_king(app.combat_marching_army)
                atk_has_king = had_real_king(app.survivors_atk)
                def_had_king = had_real_king(app.combat_target_army)
                def_has_king = had_real_king(app.survivors_def)

                if atk_had_king and not atk_has_king and src.faction in ['white', 'black']:
                    self.show_game_over(winner_faction=tgt.faction, reason="ATTACKING KING KILLED")
                    return
                if def_had_king and not def_has_king and tgt.faction in ['white', 'black']:
                    self.show_game_over(winner_faction=src.faction, reason="DEFENDING KING KILLED")
                    return
                
                if winner == 'attacker':
                    orig_tgt_faction = tgt.faction
                    
                    if tgt.is_main_base and tgt.faction in ['white', 'black']:
                        self.show_game_over(winner_faction=src.faction, reason="MAIN BASE CAPTURED")
                        return

                    tgt.faction = src.faction
                    tgt.army_pieces = clean_atk
                    tgt.loyalty = 100 
                    tgt.update_graphics() 
                    
                    if tgt.node_type == 'castle' and orig_tgt_faction == 'red':
                        app.prince_rewards[src.faction] += 1
                        
                    self.status_lbl.text = f"[color=00ff00]VICTORY! YOU CAPTURED {tgt.node_id}.[/color]"
                    
                    if orig_tgt_faction in ['white', 'black'] and clean_def:
                        retreat_node = self.get_nearest_friendly_base(tgt)
                        if retreat_node:
                            retreat_node.army_pieces.extend(clean_def)
                            self.status_lbl.text += f" ENEMY RETREATED TO {retreat_node.node_id}."
                            
                elif winner == 'defender':
                    tgt.army_pieces = clean_def
                    if src.faction in ['white', 'black']:
                        if clean_atk:
                            src.army_pieces.extend(clean_atk) 
                            self.status_lbl.text = f"[color=ff0000]DEFEAT! YOUR ARMY RETREATED TO {src.node_id}.[/color]"
                        else:
                            self.status_lbl.text = f"[color=ff0000]CRUSHING DEFEAT! ARMY DESTROYED.[/color]"
                else:
                    tgt.army_pieces = clean_def
                    if src.faction in ['white', 'black']: src.army_pieces.extend(clean_atk) 
                    
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
        
        # ✨ เสกทหาร Guard ออกมากันบ้านตามระดับ
        def spawn_guards(addons_dict):
            if addons_dict.get('special') == 'guard':
                lvl = addons_dict.get('special_lvl', 1)
                g_list = ['levies', 'levies', 'pawn']
                if lvl >= 2: g_list.extend(['bishop', 'knight', 'rook'])
                if lvl >= 3: g_list.extend(['menatarm', 'rook', 'rook', 'bishop'])
                for p_name in g_list:
                    target_army.append(generate_piece(p_name, target_node.faction, app))
                    
        if hasattr(target_node, 'addons'): spawn_guards(target_node.addons)
        if target_node.node_type == 'castle' and hasattr(target_node, 'sub_villages'):
            for sv in target_node.sub_villages: spawn_guards(sv['addons'])
        
        if target_node.faction == 'red':
            target_count = random.randint(8, 12)
            while len(target_army) > target_count:
                removable_pieces = [p for p in target_army if p.__class__.__name__.lower() not in ['king']]
                if not removable_pieces: break
                p_to_remove = random.choice(removable_pieces)
                target_army.remove(p_to_remove)
                
        ensure_header(target_army, target_node.faction, app) 
        app.combat_target_army = target_army
        ensure_header(app.combat_marching_army, source_node.faction, app)
        
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(mode='Divide_Conquer')
        self.manager.current = 'gameplay'

    def switch_turn(self):
        app = App.get_running_app()
        
        if hasattr(self, 'army_panel'):
            self.army_panel.close_panel()

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
        
        if hasattr(self, 'army_panel'):
            self.army_panel.close_panel()

        if self.marching_from_node:
            self.marching_from_node.army_pieces.extend(app.combat_marching_army)
            self.marching_from_node = None
        
        tax_collected = 0
        rebellions = []
        
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                # ✨ คิดภาษีฐานหลักตาม Addon
                base_tax = 3 if node.node_type == 'village' else 6
                farm_bonus = getattr(node, 'addons', {}).get('farm', 0) * 2
                mine_bonus = 3 if getattr(node, 'addons', {}).get('special') == 'mine' else 0
                tax_collected += base_tax + farm_bonus + mine_bonus
                
                # ✨ คิดภาษีหมู่บ้านย่อย (ถ้าเป็นปราสาท)
                if node.node_type == 'castle':
                    for sv in getattr(node, 'sub_villages', []):
                        sv_farm = sv['addons'].get('farm', 0) * 2
                        sv_mine = 3 if sv['addons'].get('special') == 'mine' else 0
                        tax_collected += 3 + sv_farm + sv_mine

                # คิดค่า Loyalty
                if node.is_main_base:
                    node.loyalty = 100
                else:
                    if len(node.army_pieces) < 3: node.loyalty -= 20
                    else: node.loyalty += 10
                    node.loyalty = max(0, min(100, node.loyalty))
                    
                if node.loyalty == 0: rebellions.append(node)
                
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