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
from components.map_banner import MapBanner
from logic.environment_generator import EnvironmentGenerator, EnvProp
from kivy.uix.widget import Widget
from logic.campaign_helpers import get_distance, generate_piece, ensure_header, resolve_map_battle
from logic.campaign_map_generator import MapGenerator
from logic.campaign_ai import CampaignAI
from components.campaign_panel import CampaignArmyPanel
from components.map_node import MapNode
# ✨ เพิ่มการ Import แมพ 3D โหมด DNC เข้ามา
from components.board_3d_macro import MacroBoard3D
import math
from logic.save_manager import save_game


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
        

        center_box = BoxLayout(orientation='vertical', size_hint_x=0.65)
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - TURN 1", bold=True, color=(1, 0.8, 0.2, 1), font_size='16sp', markup=True)
        self.resource_lbl = Label(text="", bold=True, font_size='14sp', markup=True) # แถบโชว์ทรัพยากร
        
        center_box.add_widget(self.status_lbl)
        center_box.add_widget(self.resource_lbl)
        top_bar.add_widget(center_box)
        
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

            # ✨ สิ่งที่ต้องเพิ่ม: ทรัพยากรใหม่
            app.supplies_points = {'white': 0, 'black': 0} 
            app.wood_points = {'white': 0, 'black': 0}
            
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
        self.update_resource_display()

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
        # ข้อยกเว้น: ไม่ทำงานกับกบฏ (red faction) เพราะกบฏเกิดจากในเมืองเอง
        # --- 🏰 ระบบกำแพงเมือง (Wallbuilder) ---
        if getattr(target_node, 'building_state', None) == 'wallbuilder' and getattr(target_node, 'wallbuilder_cooldown', 0) == 0 and source_node.faction != 'red':
            if random.random() < 0.70: # 70% โอกาสป้องกันสำเร็จ
                if hasattr(app, 'play_click_sound'): app.play_click_sound()
                self.status_lbl.text = f"[color=ff0000]ATTACK ON {getattr(target_node, 'city_name', 'CASTLE').upper()} REPELLED BY WALL![/color]"
                
                # ติด Cooldown 2 เทิร์น
                target_node.wallbuilder_cooldown = 2 
                
                # ทัพศัตรูต้องล่าถอยกลับไปที่เดิม และเหนื่อยล้าเต็มที่ (Fatigue = 6) ทันที
                source_node.army_pieces.extend(app.combat_marching_army)
                source_node.fatigue = 6
                
                # คืนค่าสถานะการเดินทัพ เพื่อให้ผู้เล่นไปสั่งการเมืองอื่นต่อได้
                self.marching_from_node = None
                app.combat_marching_army = []
                self.refresh_banners()
                
                # 🟢 ลบ self.end_turn(None) ทิ้งไป และใช้แค่ return เพื่อออกจากฟังก์ชันการต่อสู้
                return
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
            self.ai_turn_active = False
            
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                node.fatigue = max(0, getattr(node, 'fatigue', 0) - 3)
                
        self.jump_to_base(None)
        
        # ✨ เพิ่มส่วนนี้: สั่งให้รีเฟรชธงใหม่เพื่อสลับฝั่งเมืองฝ่ายเราและศัตรู
        if getattr(self, 'current_dimension', '2D') != '2D':
            self.refresh_banners()
        
        # If Black's turn in a PVE match...
        if (app.current_map_turn == 'black'
                and getattr(app, 'match_type', '') == 'PVE'):
            self.ai_turn_active = True
            self.campaign_ai.execute_turn(self, 'black')
        self.update_resource_display()

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
        if self.ai_turn_active and instance is not None:
            return
        if instance is not None:
            app.play_click_sound()
        if hasattr(self, 'army_panel'): self.army_panel.close_panel()
                
        if self.marching_from_node:
            self.marching_from_node.army_pieces.extend(app.combat_marching_army)
            self.marching_from_node = None
            
        # 1. เพิ่มตัวแปรเริ่มต้นตรงนี้
        tax_collected = 0
        supplies_collected = 0 
        wood_collected = 0
        coal_collected = 0
        silver_collected = 0
        gold_collected = 0
        rebellions = []
        
        for node in self.nodes_list: 
            if node.faction == app.current_map_turn: 
                if hasattr(node, 'refresh_recruits'): node.refresh_recruits() 
                
                # --- 🟢 จัดการฟาร์ม ---
                farm_lvl = getattr(node, 'addons', {}).get('farm', 0)
                farm_mode = getattr(node, 'addons', {}).get('farm_mode', 'tax')
                
                if farm_lvl > 0:
                    if farm_mode == 'tax':
                        tax_collected += farm_lvl * 2
                    elif farm_mode == 'resources':
                        supplies_collected += farm_lvl * 2 
                        wood_collected += farm_lvl * 3 
                
                # --- ⛏️ จัดการเหมือง (Mine) ---
                spec = getattr(node, 'addons', {}).get('special')
                spec_lvl = getattr(node, 'addons', {}).get('special_lvl', 1)
                mine_mode = getattr(node, 'addons', {}).get('mine_mode', 'tax')
                
                if spec == 'mine':
                    if mine_mode == 'tax':
                        tax_collected += spec_lvl * 3 # ให้ภาษีคูณตามเลเวลจะได้คุ้มค่าอัปเกรด
                    elif mine_mode == 'resources':
                        if spec_lvl == 1:
                            coal_collected += 2
                        elif spec_lvl == 2:
                            silver_collected += 2
                        elif spec_lvl >= 3:
                            gold_collected += 1

                if node.node_type == 'castle':
                    # ลด Cooldown ของ Wallbuilder ลงทุกๆ เทิร์น
                    wb_cd = getattr(node, 'wallbuilder_cooldown', 0)
                    if wb_cd > 0:
                        node.wallbuilder_cooldown = wb_cd - 1

                    b_state = getattr(node, 'building_state', None)
                    
                    if b_state == 'building_market':
                        node.building_state = 'market'
                        node.market_rates = self.generate_market_rates(node)
                        if hasattr(node, 'update_building_visual'): node.update_building_visual() # ✨ วาดเมื่อสร้างเสร็จ
                        
                    elif b_state == 'market':
                        node.market_rates = self.generate_market_rates(node)
                        
                    elif b_state == 'building_makerspace': 
                        node.building_state = 'makerspace'
                        if hasattr(node, 'update_building_visual'): node.update_building_visual() # ✨ วาดเมื่อสร้างเสร็จ
                        
                    elif b_state == 'building_wallbuilder': 
                        node.building_state = 'wallbuilder'
                        node.wallbuilder_cooldown = 0
                        if hasattr(node, 'update_building_visual'): node.update_building_visual() # ✨ วาดเมื่อสร้างเสร็จ
                        
                    elif b_state == 'destroying':
                        node.building_state = None
                        if hasattr(node, 'market_rates'):
                            del node.market_rates
                        if hasattr(node, 'remove_building_visual'): node.remove_building_visual() # ✨ ลบภาพออกเมื่อถูกทำลาย
                
                # --- 🔵 จัดการสิ่งปลูกสร้างใน หมู่บ้านย่อย (Sub-villages) ---
                if node.node_type == 'castle': 
                    for sv in getattr(node, 'sub_villages', []): 
                        # ฟาร์มย่อย
                        sv_farm_lvl = sv['addons'].get('farm', 0)
                        sv_farm_mode = sv['addons'].get('farm_mode', 'tax')
                        if sv_farm_lvl > 0:
                            if sv_farm_mode == 'tax':
                                tax_collected += sv_farm_lvl * 2
                            elif sv_farm_mode == 'resources':
                                supplies_collected += sv_farm_lvl * 2
                                wood_collected += sv_farm_lvl * 3
                                
                        # เหมืองย่อย
                        sv_spec = sv['addons'].get('special')
                        sv_spec_lvl = sv['addons'].get('special_lvl', 1)
                        sv_mine_mode = sv['addons'].get('mine_mode', 'tax')
                        if sv_spec == 'mine':
                            if sv_mine_mode == 'tax':
                                tax_collected += sv_spec_lvl * 3
                            elif sv_mine_mode == 'resources':
                                if sv_spec_lvl == 1:
                                    coal_collected += 2
                                elif sv_spec_lvl == 2:
                                    silver_collected += 2
                                elif sv_spec_lvl >= 3:
                                    gold_collected += 1
                                

                # 2. ลบ if node.node_type == 'castle': บล็อกเก่าที่ซ้ำซ้อนทิ้งไปเลย เพื่อป้องกันการบวกภาษีซ้ำซ้อน
                        
                if node.is_main_base:
                    node.loyalty = 100
                else:
                    node.loyalty = max(0, min(100, node.loyalty + (10 if len(node.army_pieces) >= 3 else -20)))
                    if node.loyalty == 0: rebellions.append(node)
                    
        # อัปเดตเข้าระบบตอนจบเทิร์น
        app.tax_points[app.current_map_turn] += tax_collected
        app.supplies_points[app.current_map_turn] += supplies_collected
        app.wood_points[app.current_map_turn] += wood_collected
        app.coal_points[app.current_map_turn] += coal_collected
        app.silver_points[app.current_map_turn] += silver_collected
        app.gold_points[app.current_map_turn] += gold_collected
        
        if rebellions:
            node = rebellions[0]
            node.loyalty = 50 
            self.switch_turn() 
            self.trigger_rebellion(node)
            return
        

        # ✨ สั่งอัปเดตโมเดล 3D ใหม่ หากสร้างอาคารเสร็จในเทิร์นนี้
        if getattr(self, 'current_dimension', '2D') != '2D' and hasattr(self, 'macro_3d'):
            self.macro_3d.draw_structures(self.nodes_list, self.nodes_3d_pos, getattr(self, 'current_all_edges', []))
        
        app = App.get_running_app()
        save_game(app, self, save_name="", is_autosave=True, is_suspended=False)
            
        self.switch_turn()

    def generate_procedural_map(self):
        app = App.get_running_app()
        self.map_content.clear_widgets()
        self.map_content.canvas.before.clear()
        self.nodes_list.clear()

        # ====================================================
        # 1. โหลดข้อมูลจาก Database ก่อนเป็นอันดับแรก
        # ====================================================
        save_data = None
        if hasattr(app, 'loaded_world_id') and app.loaded_world_id is not None:
            from logic.save_manager import load_game_data
            save_data = load_game_data(app.loaded_world_id)

        # ====================================================
        # 2. คืนค่าทรัพยากร App และเซ็ตระบบ Seed
        # ====================================================
        if save_data:
            print("Loading Map from Save Data...")
            world_info = save_data.get('world', {})
            seed_to_use = world_info.get('map_seed', random.randint(100000, 999999))
            
            # โหลดการตั้งค่าห้อง
            app.match_type = world_info.get('match_type', 'LOCAL_PVP')
            app.selected_economic_system = bool(world_info.get('economic_system', 0))
            app.ai_difficulty = world_info.get('ai_difficulty', 'normal')
            app.current_map_turn = world_info.get('active_faction', 'white')
            app.turn_number = world_info.get('current_turn', 1)

            # 🟢 โหลดข้อมูลเผ่ากลับเข้าไปให้ตัวแปร App
            app.white_tribe = world_info.get('white_tribe', 'human')
            app.black_tribe = world_info.get('black_tribe', 'orc')

            # คืนค่าทรัพยากรทั้งหมดให้ App
            if 'factions' in save_data:
                for f_data in save_data['factions']:
                    fac = f_data['faction_name']
                    app.tax_points[fac] = f_data['tax_points']
                    app.supplies_points[fac] = f_data['supplies_points']
                    app.weapon_t1_points[fac] = f_data['weapon_t1']
                    app.weapon_t2_points[fac] = f_data['weapon_t2']
                    app.weapon_t3_points[fac] = f_data['weapon_t3']
                    
                    if not hasattr(app, 'wood_points'): app.wood_points = {}
                    if not hasattr(app, 'iron_points'): app.iron_points = {}
                    if not hasattr(app, 'coal_points'): app.coal_points = {}
                    if not hasattr(app, 'silver_points'): app.silver_points = {}
                    if not hasattr(app, 'gold_points'): app.gold_points = {}
                    
                    app.wood_points[fac] = f_data.get('wood_points', 0)
                    app.iron_points[fac] = f_data.get('iron_points', 0)
                    app.coal_points[fac] = f_data.get('coal_points', 0)
                    app.silver_points[fac] = f_data.get('silver_points', 0)
                    app.gold_points[fac] = f_data.get('gold_points', 0)
        else:
            seed_to_use = random.randint(100000, 999999)
            print(f"Generating NEW Map with Seed: {seed_to_use}")

        app.current_map_seed = seed_to_use
        random.seed(seed_to_use)

        # ====================================================
        # 3. สร้าง Map และ Nodes (โค้ดดั้งเดิมของคุณ)
        # ====================================================
        size_val = getattr(app, 'selected_board', 'Size_S')
        map_w, map_h = 9600, 5400
        self.current_dimension = getattr(app, 'selected_dimension', '2D')

        map_data = MapGenerator.generate_data(size_val, map_w, map_h)
        nodes_data = map_data['w_nodes'] + map_data['b_nodes']
        all_edges = map_data['white_edges'] + map_data['black_edges']
        if map_data['cross_edge']:
            all_edges.append(map_data['cross_edge'])
        self.current_all_edges = all_edges
        # ====================================================
        # 🟢 กรณีเป็นโหมด 2D CLASSIC CAMPAIGN
        # ====================================================
        if self.current_dimension == '2D':
            self.scroll_view.opacity = 1
            self.scroll_view.disabled = False

            # --- สร้าง Layer ---
            bg_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            line_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            prop_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))

            # ===================================================
            # 🎨 1. ระบบวาดพื้นดิน 2D ตาม Logic 3D (Procedural Canvas)
            # ===================================================
            tile_size = 200  # ปรับขนาดความละเอียดของช่อง ยิ่งน้อยยิ่งเนียนแต่โหลดนานขึ้น
            cols = int(map_w / tile_size)
            rows = int(map_h / tile_size)
            total_area = rows * cols
            r_snow = math.sqrt((0.18 * total_area) / (2 * math.pi))
            r_desert = math.sqrt((0.18 * total_area) / (3 * math.pi))
            
            # กำหนดจุดศูนย์กลางหิมะ
            snow_centers = []
            for _ in range(2):
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                margin = 5 
                if edge == 'top': pt = (random.uniform(0, cols), random.uniform(rows - margin, rows))
                elif edge == 'bottom': pt = (random.uniform(0, cols), random.uniform(0, margin))
                elif edge == 'left': pt = (random.uniform(0, margin), random.uniform(0, rows))
                else: pt = (random.uniform(cols - margin, cols), random.uniform(0, rows))
                snow_centers.append(pt)
            
            # กำหนดจุดศูนย์กลางทะเลทราย
            desert_centers = []
            for _ in range(3):
                for _ in range(100):
                    edge = random.choice(['top', 'bottom', 'left', 'right'])
                    margin = 5 
                    if edge == 'top': pt = (random.uniform(0, cols), random.uniform(rows - margin, rows))
                    elif edge == 'bottom': pt = (random.uniform(0, cols), random.uniform(0, margin))
                    elif edge == 'left': pt = (random.uniform(0, margin), random.uniform(0, rows))
                    else: pt = (random.uniform(cols - margin, cols), random.uniform(0, rows))
                    
                    if all(math.hypot(pt[0] - sx, pt[1] - sy) > (cols * 0.3) for sx, sy in snow_centers):
                        desert_centers.append(pt)
                        break
                else:
                    desert_centers.append(pt)

            # (สมมติว่าคุณมีฟังก์ชัน noise_gen.noise2d ใช้งานอยู่)
            # ถ้าไม่มี สามารถข้ามเรื่อง 'e' (ความสูง) ไปก่อน หรือใช้ random ชั่วคราว
            with bg_layer.canvas.before:
                for r in range(rows):
                    for c in range(cols):
                        # คำนวณระยะห่างเพื่อกำหนดสี
                        s_val = min([math.hypot(c - cx, r - cy) for cx, cy in snow_centers])
                        d_val = min([math.hypot(c - cx, r - cy) for cx, cy in desert_centers])
                        
                        # รหัสสีตามที่ระบุ
                        c_snow = (0.85, 0.85, 0.9, 1)
                        c_desert = (0.76, 0.7, 0.5, 1)
                        c_forest_base = (0.35, 0.55, 0.3, 1)     
                        c_forest_warm = (0.45, 0.55, 0.2, 1)    
                        c_forest_cool = (0.25, 0.55, 0.4, 1)    
                        
                        inf_radius = 6.0
                        base_grass_color = list(c_forest_base)
                        
                        if s_val < r_snow + inf_radius:
                            t_inf = max(0, min(1, (r_snow + inf_radius - s_val) / inf_radius))
                            base_grass_color = [c_forest_base[i] + (c_forest_cool[i] - c_forest_base[i]) * t_inf for i in range(4)]
                        elif d_val < r_desert + inf_radius:
                            t_inf = max(0, min(1, (r_desert + inf_radius - d_val) / inf_radius))
                            base_grass_color = [c_forest_base[i] + (c_forest_warm[i] - c_forest_base[i]) * t_inf for i in range(4)]

                        color = list(base_grass_color)
                        if s_val < r_snow:
                            t = max(0, min(1, (r_snow - s_val) / 5.0))
                            color = [base_grass_color[i] + (c_snow[i] - base_grass_color[i]) * t for i in range(4)]
                        elif d_val < r_desert:
                            t = max(0, min(1, (r_desert - d_val) / 5.0))
                            color = [base_grass_color[i] + (c_desert[i] - base_grass_color[i]) * t for i in range(4)]

                        # วาดสี่เหลี่ยมลงบนแผนที่
                        Color(*color)
                        Rectangle(pos=(c * tile_size, r * tile_size), size=(tile_size, tile_size))

            # --- 2. วาดเส้นทาง (Edges) ลงบน line_layer ---
            with line_layer.canvas:
                Color(0.85, 0.75, 0.3, 0.8)
                for u, v in map_data['white_edges'] + map_data['black_edges']:
                    Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4)
                    
                if map_data['cross_edge']:
                    u, v = map_data['cross_edge']
                    Color(0.9, 0.4, 0.2, 0.9)
                    Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=8)

            # --- นำ Layer ทั้ง 3 มาซ้อนกันบน map_content ตามลำดับ ---
            self.map_content.add_widget(bg_layer)
            self.map_content.add_widget(line_layer)
            self.map_content.add_widget(prop_layer)

            # --- 1. คำนวณสภาพแวดล้อม ---
            tiles, props = EnvironmentGenerator.generate_environment(map_w, map_h, nodes_data, all_edges)

            # --- 2. สร้าง Layer เพื่อแก้ปัญหาการทับซ้อน (Z-Index) ---
            bg_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            line_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))
            prop_layer = FloatLayout(size=(map_w, map_h), size_hint=(None, None))

            # --- 3. วาง Background Tiles ลงใน bg_layer ---
            with bg_layer.canvas.before:
                for t_data in tiles:
                    Color(*t_data['color'])
                    Rectangle(pos=(t_data['x'], t_data['y']), size=(t_data['w'], t_data['h']))

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
            for i, data in enumerate(nodes_data): # ✨ เปลี่ยนเป็น enumerate เพื่อดึง Index
                node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'], app=app)
                node.base_pos = data['pos']
                node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
                # ✨ โหลดข้อมูลสถานะตึก (Building) และ Cooldown กลับเข้ามา
                if save_data and 'nodes' in save_data:
                    saved_nodes = save_data['nodes']
                    if i < len(saved_nodes):
                        node.building_state = saved_nodes[i].get('building_state')
                        node.wallbuilder_cooldown = saved_nodes[i].get('wallbuilder_cooldown', 0)
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
                
                # ✨ ดึงภาพมาแสดงทันทีสำหรับโหมด 2D หากปราสาทนั้นเคยสร้างเสร็จไว้แล้ว
                if hasattr(node, 'building_state') and node.building_state in ['market', 'makerspace', 'wallbuilder']:
                    if hasattr(node, 'update_building_visual'):
                        node.update_building_visual()
                
            self.scroll_view.scroll_x, self.scroll_view.scroll_y = 0.5, 0.5
            self.jump_to_base(None)

        # ====================================================
        # 🔴 โหมด 2.5D (3D) MACRO MAP
        # ====================================================
        else:
            self.scroll_view.opacity = 0
            self.scroll_view.disabled = True

            grid_size = 16 if size_val == 'Size_S' else (24 if size_val == 'Size_M' else 32)
            self.macro_3d = MacroBoard3D(map_size=(grid_size, grid_size), size_hint=(1, 1))

            # ✨ 1. สร้าง Layout UI ซ้ายและขวา ให้เรียงเป็น Column
            if hasattr(self, 'left_panel') and self.left_panel in self.ui_layer.children:
                self.ui_layer.remove_widget(self.left_panel)
            if hasattr(self, 'right_panel') and self.right_panel in self.ui_layer.children:
                self.ui_layer.remove_widget(self.right_panel)

            self.left_panel = ScrollView(size_hint=(None, 0.8), width=dp(160), pos_hint={'x': 0.02, 'y': 0.1})
            self.left_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(5))
            self.left_box.bind(minimum_height=self.left_box.setter('height'))
            self.left_panel.add_widget(self.left_box)
            
            self.right_panel = ScrollView(size_hint=(None, 0.8), width=dp(160), pos_hint={'right': 0.98, 'y': 0.1})
            self.right_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(5))
            self.right_box.bind(minimum_height=self.right_box.setter('height'))
            self.right_panel.add_widget(self.right_box)

            self.ui_layer.add_widget(self.left_panel)
            self.ui_layer.add_widget(self.right_panel)

            self.remove_widget(self.ui_layer)
            self.add_widget(self.macro_3d)
            self.add_widget(self.ui_layer)

            # ✨ 2. สุ่มชื่อเมือง 14 ชื่อไม่ซ้ำกัน
            name_pool = [
                "Avalon", "Lordaeron", "Camelot", "Gondor", "Rohan", "Winterfell", "Rivendell", 
                "Asgard", "Midgard", "Valhalla", "Olympus", "Elysium", "Troy", "Sparta"
            ]
            random_names = random.sample(name_pool, 14)
            name_idx = 0

            self.active_banners = []
            self.nodes_3d_pos = {}
            nodes_dict = {}

            # ลูปที่ 1: สร้าง Node และประทับตราชื่อเมือง
            for i, data in enumerate(nodes_data): # ✨ เปลี่ยนเป็น enumerate เช่นกัน
                node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'], app=app)
                node.base_pos = data['pos']
                
                # แปะชื่อเมืองให้ Node ฝังไว้ในออบเจ็กต์เลย
                node.city_name = random_names[name_idx % len(random_names)]
                name_idx += 1
                
                # ✨ โหลดข้อมูลสถานะตึก (Building) และ Cooldown กลับเข้ามา
                if save_data and 'nodes' in save_data:
                    saved_nodes = save_data['nodes']
                    if i < len(saved_nodes):
                        node.building_state = saved_nodes[i].get('building_state')
                        node.wallbuilder_cooldown = saved_nodes[i].get('wallbuilder_cooldown', 0)
                
                self.nodes_list.append(node)
                nodes_dict[data['id']] = node
                
                # คำนวณ 3D (เอาไว้วาดปราสาทลงบนแมพ)
                scale_factor = 4.0 
                cx = (node.base_pos[0] / 9600.0) * (grid_size * scale_factor)
                cz = (node.base_pos[1] / 5400.0) * (grid_size * scale_factor)
                c_play, r_play = cx + 40, cz + 40
                
                world_x = c_play - (((grid_size * scale_factor) + 80) / 2.0)
                world_z = r_play - (((grid_size * scale_factor) + 80) / 2.0)
                world_y = self.macro_3d.get_height_at(c_play, r_play)
                
                self.nodes_3d_pos[node.node_id] = (world_x, world_y, world_z)

            # เชื่อม Edge ให้ระบบรับรู้ Neighbor
            for u, v in all_edges:
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])
            
            # ✨ [เพิ่มใหม่] ดึงข้อมูลเส้นเชื่อมข้าม "ฝั่ง" ของจริงมาจาก map_data
            cross_edge_ids = None
            if map_data['cross_edge']:
                u, v = map_data['cross_edge']
                cross_edge_ids = (u['id'], v['id'])
                
            # ✨ ส่ง cross_edge_ids เข้าไปวาดเพื่อไม่ให้มันไปเช็คสี Faction มั่วๆ
            self.macro_3d.draw_paths(all_edges, self.nodes_3d_pos, self.nodes_list, cross_edge_ids)
            self.macro_3d.draw_structures(self.nodes_list, self.nodes_3d_pos, all_edges)

            # ✨ 3. เรียกฟังก์ชันแสดงผลธงลงบนหน้าจอ!
            self.refresh_banners()

        # ====================================================
        # 4. คืนค่าสถานะตึก ทหาร และความเป็นเจ้าของให้แต่ละ Node
        # ====================================================
        if save_data:
            if 'nodes' in save_data:
                for i, n_data in enumerate(save_data['nodes']):
                    if i < len(self.nodes_list):
                        node = self.nodes_list[i]
                        node.faction = n_data['faction']
                        node.loyalty = n_data['loyalty']
                        node.fatigue = n_data['fatigue']
                        node.building_state = n_data['building_state']
                        node.wallbuilder_cooldown = n_data['wallbuilder_cooldown']

                        import json
                        if n_data.get('market_trend'): node.market_trend = json.loads(n_data['market_trend'])
                        if n_data.get('market_activity'): node.market_activity = json.loads(n_data['market_activity'])
                        if n_data.get('market_timer'): node.market_timer = json.loads(n_data['market_timer'])
                        if n_data.get('market_rates'): node.market_rates = json.loads(n_data['market_rates'])
                        
                        if not hasattr(node, 'addons'): node.addons = {}
                        node.addons['farm'] = n_data['farm_lvl']
                        node.addons['tavern'] = n_data['tavern_lvl']
                        node.addons['special'] = n_data['special_type']
                        node.addons['special_lvl'] = n_data['special_lvl']
                        
                        # ล้างทหารตั้งต้นที่สร้างมาจาก MapGenerator ทิ้ง เพื่อป้องกันการซ้อนทับ
                        node.army_pieces = []

                        # รีเฟรชภาพ UI หากเป็นโหมด 2D แล้วตึกเคยสร้างเสร็จ
                        if self.current_dimension == '2D' and node.building_state in ['market', 'makerspace', 'wallbuilder']:
                            if hasattr(node, 'update_building_visual'):
                                node.update_building_visual()

            if 'units' in save_data:
                from logic.campaign_helpers import generate_piece
                # สร้าง Map ระหว่าง id ของ DB กับ node_index
                node_db_to_index = {n['id']: n['node_index'] for n in save_data['nodes']}
                
                for u_data in save_data['units']:
                    n_idx = node_db_to_index.get(u_data['node_id'])
                    if n_idx is not None and n_idx < len(self.nodes_list):
                        target_node = self.nodes_list[n_idx]
                        
                        new_piece = generate_piece(u_data['piece_class'].lower(), target_node.faction, app)
                        new_piece.upgrade_level = u_data['upgrade_level']
                        if u_data['is_commander']:
                            new_piece.is_header = True
                            
                        target_node.army_pieces.append(new_piece)

        self.hide_loading()
        # กระตุ้น AI
        if save_data and app.current_map_turn == 'black' and getattr(app, 'match_type', '') == 'PVE':
            self.ai_turn_active = True
            self.campaign_ai.execute_turn(self, 'black')

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

            # ✨ สิ่งที่ต้องเพิ่ม: ทรัพยากรใหม่ (ต้องมี 2 บรรทัดนี้)
            app.supplies_points = {'white': 0, 'black': 0} 
            app.wood_points = {'white': 0, 'black': 0}

            # ทรัพยากรสำหรับ Mine
            app.coal_points = {'white': 0, 'black': 0} 
            app.silver_points = {'white': 0, 'black': 0} 
            app.gold_points = {'white': 0, 'black': 0}
            app.iron_points = {'white': 0, 'black': 0} # 🟢 เพิ่มเหล็กตรงนี้

            # 🗡️ เพิ่มตัวแปรสำหรับเก็บอาวุธ
            app.weapon_t1_points = {'white': 0, 'black': 0}
            app.weapon_t2_points = {'white': 0, 'black': 0}
            app.weapon_t3_points = {'white': 0, 'black': 0}
            
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

    def on_banner_click(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()

        target_node = getattr(instance, 'node', None)
        if not target_node: return

        # ========================================================
        # 🟢 โหมด: กำลังสั่งเดินทัพ (กดปุ่ม MARCH / ATTACK มาแล้ว)
        # ========================================================
        if self.marching_from_node:
            # เช็คก่อนว่าเมืองที่คลิก (ธงที่คลิก) มีเส้นทางเชื่อมกับเมืองหลักหรือไม่
            if target_node in self.marching_from_node.neighbors:
                if target_node.faction == self.marching_from_node.faction:
                    # 1. ย้ายทัพเข้าเมืองตัวเอง
                    target_node.army_pieces.extend(app.combat_marching_army)
                    self.marching_from_node = None
                    self.status_lbl.text = "TROOPS RELOCATED SUCCESSFULLY."
                    self.end_turn(None)
                else:
                    # 2. โจมตีเมืองศัตรู
                    self.initiate_combat(self.marching_from_node, target_node)
            else:
                # 3. เมืองไม่ได้เชื่อมกัน
                self.status_lbl.text = "[color=ff0000]TARGET NOT CONNECTED! SELECT ADJACENT CITY.[/color]"
                
        # ========================================================
        # 🔵 โหมด: ปกติ (คลิกเพื่อดูรายละเอียดเมือง)
        # ========================================================
        else:
            if hasattr(self, 'army_panel'):
                # เปิด Panel ด้านล่าง เหมือนโหมด 2D
                self.army_panel.open_for_node(target_node)

    # 1. เพิ่มฟังก์ชันรีเฟรชธงแยกออกมาเพื่อให้เรียกอัปเดตง่ายๆ
    def refresh_banners(self):
        app = App.get_running_app()
        if not hasattr(self, 'left_box'): return
        
        # เคลียร์ของเก่าทิ้ง
        if hasattr(self, 'active_banners'):
            for banner in self.active_banners: banner.destroy()
        self.left_box.clear_widgets()
        self.right_box.clear_widgets()
        self.active_banners = []

        current_faction = app.current_map_turn
        
        # กรองหาเมืองฝ่ายเรา
        friendly_nodes = [n for n in self.nodes_list if n.faction == current_faction]
        
        # กรองหาเมืองฝ่ายศัตรู "ที่เชื่อมต่อกับเมืองฝ่ายเราเท่านั้น"
        enemy_nodes = set()
        for fn in friendly_nodes:
            for neighbor in fn.neighbors:
                if neighbor.faction != current_faction:
                    enemy_nodes.add(neighbor)

        # แปะธงซ้าย (เมืองเรา)
        for fn in friendly_nodes:
            banner = MapBanner(node=fn, city_name=getattr(fn, 'city_name', 'Unknown'), map_screen_ref=self)
            self.left_box.add_widget(banner)
            self.active_banners.append(banner)

        # แปะธงขวา (เป้าหมายศัตรู)
        for en in enemy_nodes:
            banner = MapBanner(node=en, city_name=getattr(en, 'city_name', 'Unknown'), map_screen_ref=self)
            self.right_box.add_widget(banner)
            self.active_banners.append(banner)


    # ----------------------------------------------------
    # 2. แก้ไข Logic เมื่อธงถูกคลิก ให้เชื่อมกับ Campaign Panel
    # ----------------------------------------------------
    def on_banner_click(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()

        target_node = instance.node

        # ⚔️ ถ้าอยู่ในสถานะกำลัง "เดินทัพ/โจมตี" (กดปุ่มมาจาก Panel แล้ว)
        if self.marching_from_node:
            if target_node in self.marching_from_node.neighbors:
                if target_node.faction == self.marching_from_node.faction:
                    # เดินเข้าเมืองตัวเอง (Merge Army)
                    target_node.army_pieces.extend(app.combat_marching_army)
                    self.marching_from_node = None
                    self.status_lbl.text = f"MARCHED TO {instance.city_name.upper()}"
                    self.refresh_banners()
                    self.end_turn(None) # บังคับจบเทิร์นหลังเดิน หรือจะเอาออกถ้าอยากให้เดินต่อได้
                else:
                    # โจมตีศัตรู! (Attack)
                    self.initiate_combat(self.marching_from_node, target_node)
            else:
                self.status_lbl.text = "[color=ff0000]TARGET NOT CONNECTED![/color]"
                # คืนทหารกลับเข้าเมืองเดิม ถ้ายกเลิก/กดผิด
                self.marching_from_node.army_pieces.extend(app.combat_marching_army)
                self.marching_from_node = None
        else:
            # 🏠 ถ้าอยู่ในสถานะปกติ (คลิกดูข้อมูล)
            if target_node.faction == app.current_map_turn:
                # เมืองเรา -> เปิด Panel ขึ้นมาให้จัดการ (เมื่อกด March จาก Panel มันจะเซ็ต self.marching_from_node)
                if hasattr(self, 'army_panel'):
                    self.army_panel.open_for_node(target_node)
            else:
                # เมืองศัตรู -> โชว์แค่ชื่อ
                self.status_lbl.text = f"[color=ff8800]ENEMY BASE: {instance.city_name.upper()}[/color]"

    def update_resource_display(self):
        app = App.get_running_app()
        fac = app.current_map_turn
        t = app.tax_points.get(fac, 0)
        
        if getattr(app, 'selected_economic_system', False):
            s = getattr(app, 'supplies_points', {}).get(fac, 0)
            w = getattr(app, 'wood_points', {}).get(fac, 0)
            c = getattr(app, 'coal_points', {}).get(fac, 0)
            sv = getattr(app, 'silver_points', {}).get(fac, 0)
            g = getattr(app, 'gold_points', {}).get(fac, 0)
            i = getattr(app, 'iron_points', {}).get(fac, 0)

            # ใช้การเว้นช่องไฟและตัวย่อให้ UI ดูคลีน ไม่รกตา
            self.resource_lbl.text = (
                f"[color=d4af37]Tax: {t}[/color]  |  "
                f"[color=ffffff]Sup: {s}[/color]  |  "
                f"[color=cd853f]Wood: {w}[/color]  |  "
                f"[color=808080]Coal: {c}[/color]  |  "
                f"[color=c0c0c0]Silv: {sv}[/color]  |  "
                f"[color=ffd700]Gold: {g}[/color]  |  "
                f"[color=8f8f8f]Iron: {i}[/color]"
            )
        else:
            self.resource_lbl.text = f"[color=d4af37]Tax: {t}[/color]"

    def generate_market_rates(self, node=None):
        rates = {
            'wood': random.randint(1, 2),
            'coal': random.randint(2, 5),
            'silver': random.randint(3, 9),
            'iron': random.randint(4, 7),
            'gold': random.randint(7, 12),
            'weapon_t1': random.randint(14, 16),
            'weapon_t2': random.randint(16, 18),
            'weapon_t3': random.randint(22, 24)
        }
        
        if node is None:
            return rates
            
        # สร้างตัวแปรเก็บ Trend, ประวัติการซื้อขาย และ Timer นับเทิร์น[cite: 2]
        if not hasattr(node, 'market_trend'):
            node.market_trend = {k: 0 for k in rates.keys()}
        if not hasattr(node, 'market_activity'):
            node.market_activity = {k: 0 for k in rates.keys()}
        if not hasattr(node, 'market_timer'):
            node.market_timer = {k: 0 for k in rates.keys()} 
            
        dynamic_items = ['wood', 'coal', 'silver', 'iron', 'gold']
        
        for item in dynamic_items:
            activity = node.market_activity.get(item, 0)
            current_trend = node.market_trend.get(item, 0)
            timer = node.market_timer.get(item, 0)
            
            # --- อัปเดต Trend และ ตัวนับเวลา ---
            if activity >= 5: 
                # ซื้อเยอะ ดันราคาขึ้น 1 ขั้น
                new_trend = current_trend + 1 if current_trend < 1 else 1
                node.market_trend[item] = new_trend
                
                # ✨ แก้ไขจาก 1 เป็น 2 เพื่อให้ Rate คงอยู่ต่อไปอีก 2 เทิร์น
                node.market_timer[item] = 2 if new_trend != 0 else 0 
            
            elif activity <= -5: 
                # ขายเยอะ ดันราคาลง 1 ขั้น
                new_trend = current_trend - 1 if current_trend > -1 else -1
                node.market_trend[item] = new_trend
                
                # ✨ แก้ไขจาก 1 เป็น 2 เพื่อให้ Rate คงอยู่ต่อไปอีก 2 เทิร์น
                node.market_timer[item] = 2 if new_trend != 0 else 0
            
            else:
                # กรณีซื้อขายไม่ถึง 5 ชิ้น (ไม่มีการกระแทกตลาด)
                if current_trend != 0:
                    if timer > 0:
                        node.market_timer[item] -= 1 # นับถอยหลังไปเรื่อยๆ (เทิร์นที่ 1 และ 2)
                    else:
                        node.market_trend[item] = 0 # ครบกำหนด (เทิร์นที่ 3) Rate กลับเป็นปกติ
                else:
                    node.market_timer[item] = 0
            
            # --- ปรับราคาสุดท้ายตาม Trend ---[cite: 2]
            final_trend = node.market_trend[item]
            
            if final_trend == 1: # เรทแพง[cite: 2]
                if item == 'wood': rates[item] = random.randint(2, 4)
                elif item == 'coal': rates[item] = random.randint(5, 7)
                elif item == 'silver': rates[item] = random.randint(9, 10)
                elif item == 'iron': rates[item] = random.randint(6, 8)
                elif item == 'gold': rates[item] = random.randint(12, 16)
            elif final_trend == -1: # เรทถูก[cite: 2]
                if item == 'wood': rates[item] = random.randint(1, 1)
                elif item == 'coal': rates[item] = random.randint(1, 2)
                elif item == 'silver': rates[item] = random.randint(1, 4)
                elif item == 'iron': rates[item] = random.randint(2, 5)
                elif item == 'gold': rates[item] = random.randint(6, 7)
                
            # เคลียร์ยอดซื้อขายประจำเทิร์นทิ้ง[cite: 2]
            node.market_activity[item] = 0
            
        return rates

    # เพิ่มเมธอดนี้ในคลาส CampaignMapScreen 
    def on_leave(self, *args):
        # ล้างแบนเนอร์และปลดอีเวนต์เมาส์เมื่อออกจากหน้าจอ
        if hasattr(self, 'active_banners'):
            for banner in self.active_banners:
                if hasattr(banner, 'destroy'):
                    banner.destroy()
            self.active_banners.clear()
            
        # ล้าง Layout ซ้ายขวาไม่ให้แสดงค้าง
        if hasattr(self, 'left_box'):
            self.left_box.clear_widgets()
        if hasattr(self, 'right_box'):
            self.right_box.clear_widgets()
            
        if hasattr(self, 'army_panel'):
            self.army_panel.close_panel()

    def on_quit_campaign(self):
        # บันทึกสถานะปัจจุบันเป็นแบบ Suspended (ยังเล่นไม่จบเทิร์น)
        app = App.get_running_app()
        save_game(app, self, save_name="", is_autosave=True, is_suspended=True)
        
        # ตัดเข้าสู่หน้า Main Menu
        self.manager.current = 'main_menu'