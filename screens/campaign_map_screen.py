# screens/campaign_map_screen.py
import random
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from logic.environment_generator import EnvironmentGenerator, EnvTile, EnvProp
from kivy.uix.widget import Widget
from logic.campaign_helpers import get_distance, generate_piece, ensure_header, resolve_map_battle
from logic.campaign_map_generator import MapGenerator
from logic.campaign_ai import CampaignAI
from components.campaign_panel import CampaignArmyPanel
from components.map_node import MapNode
# ✨ เพิ่มการ Import แมพ 3D โหมด DNC เข้ามา
from components.board_3d_macro import MacroBoard3D

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
        
        jump_btn = Button(text="  BASE", size_hint_x=0.1, background_color=(0.2, 0.5, 0.8, 1))
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
        self.campaign_ai = CampaignAI()
        self.ai_turn_active = False
        # --- ส่วนที่เพิ่มใหม่: หน้า Loading Screen สไตล์ Minimalist ---
        self.loading_overlay = FloatLayout(opacity=0)
        with self.loading_overlay.canvas.before:
            Color(0.05, 0.05, 0.08, 0.95) # พื้นหลังสีดำโปร่งแสงนิดๆ
            self.loading_bg = Rectangle(pos=self.pos, size=self.size)
            
        self.loading_label = Label(
            text="[b]GENERATING WORLD...[/b]", 
            markup=True, 
            font_size='26sp', 
            color=(0.83, 0.68, 0.21, 1), # ตัวหนังสือสีทอง
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.loading_overlay.add_widget(self.loading_label)
        self.ui_layer.add_widget(self.loading_overlay)
        
        self.bind(pos=self._update_loading_bg, size=self._update_loading_bg)

    # Helper สำหรับอัปเดตขนาดฉากโหลด
    def _update_loading_bg(self, instance, value):
        if hasattr(self, 'loading_bg'):
            self.loading_bg.pos = instance.pos
            self.loading_bg.size = instance.size


    def _update_top_bg(self, instance, value):
        self.top_bg.pos, self.top_bg.size = instance.pos, instance.size

    def jump_to_base(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound') and not self.ai_turn_active:
            app.play_click_sound()
                
        target_node = next((n for n in self.nodes_list if n.faction == app.current_map_turn and n.is_main_base), None)
        if target_node:
            self.scroll_view.scroll_x = target_node.x / self.map_content.width
            self.scroll_view.scroll_y = target_node.y / self.map_content.height

    def show_game_over(self, winner_faction, reason="MAIN BASE CAPTURED"):
        if hasattr(self, 'army_panel'): self.army_panel.close_panel()
                
        pop = ModalView(size_hint=(0.6, 0.4), auto_dismiss=False, background_color=(0,0,0,0.8))
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        with box.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            bg_rect = RoundedRectangle(radius=[dp(15)])
            
        def update_bg(*args):
            bg_rect.pos, bg_rect.size = box.pos, box.size
            
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
                    min_d, best_node = d, n
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
                resolve_map_battle(app, self)
                # If the AI was mid-turn when combat started, auto-end
                # its turn now that the battle has resolved.
                if self.ai_turn_active:
                    Clock.schedule_once(
                        lambda dt: self.end_turn(None), 1.0
                    )

    def go_back(self, instance):
        app = App.get_running_app()
        self.campaign_ai.cancel()
        self.ai_turn_active = False
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
        
        def spawn_guards(addons_dict):
            if addons_dict.get('special') == 'guard':
                lvl = addons_dict.get('special_lvl', 1)
                if target_node.faction == 'red':
                    g_list = ['pawn', 'pawn', 'pawn']
                    if lvl >= 2: g_list.extend(['bishop', 'knight', 'rook'])
                    if lvl >= 3: g_list.extend(['knight', 'rook', 'rook', 'bishop'])
                else:
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
                target_army.remove(random.choice(removable_pieces))
                
        ensure_header(target_army, target_node.faction, app) 
        app.combat_target_army = target_army
        ensure_header(app.combat_marching_army, source_node.faction, app)
        
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(mode='Divide_Conquer')
        self.manager.current = 'gameplay'

    def switch_turn(self):
        app = App.get_running_app()
        if hasattr(self, 'army_panel'): self.army_panel.close_panel()
                
        if app.current_map_turn == 'white':
            app.current_map_turn = 'black'
            self.status_lbl.text = f"DARK ABYSS (BLACK) - TURN {app.turn_number}"
            self.status_lbl.color = (0.6, 0.6, 0.8, 1)
        else:
            app.current_map_turn = 'white'
            app.turn_number += 1
            self.status_lbl.text = f"DIVINE ORDER (WHITE) - TURN {app.turn_number}"
            self.status_lbl.color = (1, 0.8, 0.2, 1)
            # AI turn just finished — unlock inputs
            self.ai_turn_active = False
            
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                node.fatigue = max(0, getattr(node, 'fatigue', 0) - 3)
                
        self.jump_to_base(None)
        
        # If Black's turn in a PVE match, hand control to the Campaign AI
        if (app.current_map_turn == 'black'
                and getattr(app, 'match_type', '') == 'PVE'):
            self.ai_turn_active = True
            self.campaign_ai.execute_turn(self, 'black')

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
        # Block the human player from pressing END TURN during the AI's turn
        if self.ai_turn_active and instance is not None:
            return
        if instance is not None:
            app.play_click_sound()
        if hasattr(self, 'army_panel'): self.army_panel.close_panel()
                
        if self.marching_from_node:
            self.marching_from_node.army_pieces.extend(app.combat_marching_army)
            self.marching_from_node = None
            
        tax_collected = 0
        rebellions = []
        
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                if hasattr(node, 'refresh_recruits'): node.refresh_recruits()
                
                farm_bonus = getattr(node, 'addons', {}).get('farm', 0) * 2
                mine_bonus = 3 if getattr(node, 'addons', {}).get('special') == 'mine' else 0
                tax_collected += farm_bonus + mine_bonus
                
                if node.node_type == 'castle':
                    for sv in getattr(node, 'sub_villages', []):
                        tax_collected += (sv['addons'].get('farm', 0) * 2) + (3 if sv['addons'].get('special') == 'mine' else 0)
                        
                if node.is_main_base:
                    node.loyalty = 100
                else:
                    node.loyalty = max(0, min(100, node.loyalty + (10 if len(node.army_pieces) >= 3 else -20)))
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
        map_w, map_h = 9600, 5400

        # ✨ เช็คว่าผู้เล่นเลือกเล่นโหมด 2D หรือ 3D
        self.current_dimension = getattr(app, 'selected_dimension', '2D')
        
        map_data = MapGenerator.generate_data(size_val, map_w, map_h)
        nodes_data = map_data['w_nodes'] + map_data['b_nodes']
        all_edges = map_data['white_edges'] + map_data['black_edges']
        if map_data['cross_edge']:
            all_edges.append(map_data['cross_edge'])

        # เคลียร์กระดาน 3D อันเก่าทิ้ง (ถ้ามี) เพื่อป้องกันการซ้อนทับกัน
        if hasattr(self, 'macro_3d') and self.macro_3d in self.children:
            self.remove_widget(self.macro_3d)

        # ====================================================
        # 🟢 กรณีเป็นโหมด 2D CLASSIC CAMPAIGN
        # ====================================================
        if self.current_dimension == '2D':
            self.scroll_view.opacity = 1
            self.scroll_view.disabled = False

            # --- 1. คำนวณสภาพแวดล้อม ---
            tiles, props = EnvironmentGenerator.generate_environment(map_w, map_h, nodes_data, all_edges)

            # --- 2. สร้าง Layer เพื่อแก้ปัญหาการทับซ้อน (Z-Index) ---
            bg_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            line_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            prop_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))

            # --- 3. วาง Background Tiles ลงใน bg_layer ---
            for t_data in tiles:
                tile = EnvTile(
                    source=f"assets/environment/{t_data['biome']}.png",
                    pos=(t_data['x'], t_data['y']),
                    size=(t_data['w'], t_data['h']),
                    size_hint=(None, None)
                )
                bg_layer.add_widget(tile)

            # --- 4. วาดเส้นทาง (Edges) ลงบน line_layer ---
            with line_layer.canvas:
                Color(0.85, 0.75, 0.3, 0.8)
                for u, v in map_data['white_edges'] + map_data['black_edges']:
                    Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4)
                    
                if map_data['cross_edge']:
                    u, v = map_data['cross_edge']
                    Color(0.9, 0.4, 0.2, 0.9)
                    Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=8)

            # --- 5. วาง Props ลงใน prop_layer ---
            for p_data in props:
                px = p_data['x'] - (p_data['size'] / 2)
                py = p_data['y'] - (p_data['size'] / 2)
                prop = EnvProp(
                    source=f"assets/environment/{p_data['type']}.png",
                    pos=(px, py),
                    size=(p_data['size'], p_data['size']),
                    size_hint=(None, None)
                )
                prop_layer.add_widget(prop)

            # --- นำ Layer ทั้ง 3 มาซ้อนกันบน map_content ตามลำดับ ---
            self.map_content.add_widget(bg_layer)
            self.map_content.add_widget(line_layer)
            self.map_content.add_widget(prop_layer)

            # --- 6. วาง Nodes ให้อยู่บนสุด ---
            nodes_dict = {}
            for data in nodes_data:
                node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'], app=app)
                node.base_pos = data['pos']
                node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
                self.nodes_list.append(node)
                nodes_dict[data['id']] = node

            for u, v in map_data['white_edges'] + map_data['black_edges']:
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])
                
            if map_data['cross_edge']:
                u, v = map_data['cross_edge']
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])
                    
            for node in self.nodes_list: 
                self.map_content.add_widget(node)
                
            self.scroll_view.scroll_x, self.scroll_view.scroll_y = 0.5, 0.5
            self.jump_to_base(None)

        # ====================================================
        # 🔴 กรณีเป็นโหมด 2.5D (3D) MACRO MAP
        # ====================================================
        else:
            # ซ่อนจอภาพและปิดการเลื่อน 2D ไปก่อน
            self.scroll_view.opacity = 0
            self.scroll_view.disabled = True

            # กำหนดขนาดของ Grid 3D อิงตามขนาดแผนที่ (S, M, L)
            grid_size = 20
            if size_val == 'Size_S': grid_size = 16
            elif size_val == 'Size_M': grid_size = 24
            elif size_val == 'Size_L': grid_size = 32

            # โหลด MacroBoard3D ขึ้นมา
            self.macro_3d = MacroBoard3D(map_size=(grid_size, grid_size), size_hint=(1, 1))

            # ถอด UI ออกมาแป๊บนึง เพื่อยัดกระดาน 3D เข้าไปข้างล่างให้อยู่หลัง UI เสมอ
            self.remove_widget(self.ui_layer)
            self.add_widget(self.macro_3d)
            self.add_widget(self.ui_layer)

            # เฟสแรก: ยังไม่แสดงปุ่มเมือง แต่ต้องลงทะเบียนเมืองเข้าหลังบ้านไว้ เพื่อไม่ให้ระบบพัง
            for data in nodes_data:
                node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'], app=app)
                # เราดรอป node ทิ้งไว้ใน list หลังบ้านเฉยๆ ระบบ AI หรือ Turn จะได้ทำงานรอด
                self.nodes_list.append(node)

        self.hide_loading()

    def show_loading(self):
        self.loading_overlay.opacity = 1
        # ป้องกันไม่ให้ผู้เล่นกดปุ่มอื่นขณะโหลด
        self.disabled = True 

    def hide_loading(self):
        self.loading_overlay.opacity = 0
        self.disabled = False
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
            
            app.unlocked_units = {
                'white': {'pawn', 'levies', 'menatarm', 'knight', 'bishop', 'rook', 'queen'},
                'black': {'pawn', 'levies', 'menatarm', 'knight', 'bishop', 'rook', 'queen'}
            }
            self.marching_from_node = None
            
            # --- แก้ไขตรงนี้ ---
            self.show_loading()
            # หน่วงเวลา 0.1 วินาที เพื่อให้ Kivy วาดหน้า Loading Screen ก่อนที่โค้ดคำนวณจะทำงาน
            Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)
            
            app.campaign_initialized = True
        else:
            self.marching_from_node = None
            if getattr(app, 'battle_finished', False):
                resolve_map_battle(app, self)
                if self.ai_turn_active:
                    Clock.schedule_once(
                        lambda dt: self.end_turn(None), 1.0
                    )