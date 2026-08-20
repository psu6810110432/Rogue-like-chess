# screens/gameplay_screen.py
import os
import random
from logic.image_utils import safe_piece_path
from kivy.app import App
from kivy.graphics import Rectangle, Color, Line
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from kivy.animation import Animation
from components.piece_card import PieceCard
from components.board_3d import Board3D
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from components.bottom_ui_manager import BottomUIManager


from logic.board import ChessBoard
from components.chess_square import ChessSquare
from components.sidebar_ui import SidebarUI
from components.unit_card import UnitCard
from components.item_tooltip import ItemTooltip
from components.crash_overlay import CrashOverlay
from components.inventory_ui import InventorySlot
from components.gameplay_popups import PromotionPopup, RetreatPopup

# Import Managers ที่เราแยกไว้
from components.deployment_manager import DeploymentManager
from logic.ai_controller import AIController
from controllers.local_controller import LocalGameController

try:
    from logic.maps.forest_map import ForestMap
except ImportError:
    ForestMap = None
try:
    from logic.maps.desert_map import DesertMap
except ImportError:
    DesertMap = None
try:
    from logic.maps.tundra_map import TundraMap
except ImportError:
    TundraMap = None

class CameraBoard(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drag_start = None
        self.start_pos = None

    def on_touch_down(self, touch):
        # ฟีเจอร์ที่ 1: ตรวจสอบการคลิกขวา (right click)
        if touch.button == 'right':
            touch.grab(self)
            self.drag_start = touch.pos
            self.start_pos = self.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        # คำนวณระยะที่เลื่อนและเปลี่ยนตำแหน่งกระดาน
        if touch.grab_current is self and self.drag_start and self.start_pos:
            dx = touch.x - self.drag_start[0]
            dy = touch.y - self.drag_start[1]
            self.pos = (self.start_pos[0] + dx, self.start_pos[1] + dy)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.drag_start = None
            self.start_pos = None
            return True
        return super().on_touch_up(touch)

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        
        # เรียกใช้งาน Managers
        self.deployment_manager = DeploymentManager(self)
        self.ai_controller = AIController(self)
        
        with self.root_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.main_bg_image = Rectangle(source='assets/ui/backgrounds/sky.png', pos=self.pos, size=self.size)
            Color(0.02, 0.02, 0.04, 0.9)
            self.main_bg_overlay = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self._update_main_bg, size=self._update_main_bg)
        self.main_layout = BoxLayout(orientation='horizontal')
        self.root_layout.add_widget(self.main_layout)
        self.add_widget(self.root_layout)
        self.status_popup = self.crash_popup = self.item_tooltip = self.selected_item = None
        self._game_over_scheduled = False
        self.countdown_event = None
        self.countdown_time = 0
        # Turn Timer state
        self.turn_timer_event = None
        self.turn_timer_remaining = 0
        self.turn_timer_limit = 0

    def _update_main_bg(self, *args):
        self.main_bg_image.pos, self.main_bg_image.size = self.pos, self.size
        self.main_bg_overlay.pos, self.main_bg_overlay.size = self.pos, self.size

    def get_tribe_name(self, color):
        theme = getattr(App.get_running_app(), f'selected_unit_{color}', 'the knight company')
        theme_map = {
            "Medieval Knights": "the knight company",
            "Heaven": "the ancient runes",
            "Ayothaya": "the chaos mankind",
            "Demon": "the deep anomaly",
            "Bandit": "bandit"
        }
        return theme_map.get(theme, theme.lower())

    def setup_game(self, mode):
        self.main_layout.clear_widgets()
        self.deployment_manager.remove_layer()
        self.hide_item_tooltip()
        self.fast_forward_ai = False
        self.status_popup = self.crash_popup = self.item_tooltip = self.selected_item = None
        self.game_mode, self._game_over_scheduled, self.selected = mode, False, None
        self.is_input_locked = False 
        self.ai_event = None
        self.battle_phase = 'playing' 
        
        if hasattr(self, 'countdown_event') and self.countdown_event:
            self.countdown_event.cancel()
            self.countdown_event = None
        self.countdown_time = 0
        
        self.stop_turn_timer()

        app = App.get_running_app()
        chosen_map = getattr(app, 'selected_board', 'Classic Board')
        if chosen_map == "Random Board": chosen_map = random.choice(['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra'])
        
        if chosen_map == 'Enchanted Forest' and ForestMap: self.game = ForestMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Desert Ruins' and DesertMap: self.game = DesertMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Frozen Tundra' and TundraMap: self.game = TundraMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        else: self.game = ChessBoard(self.get_tribe_name('white'), self.get_tribe_name('black'), map_name=chosen_map)
        
        self.controller = LocalGameController(self.game)
        
        # ✨ ประกาศใช้ BottomUIManager
        self.bottom_ui = BottomUIManager(self)
        
        if mode == 'Divide_Conquer':
            self.setup_divide_conquer_board(app)

        # ✨ 2. สร้างปุ่ม Fast Forward (FF)
        if hasattr(self, 'ff_btn') and self.ff_btn in self.root_layout.children:
            self.root_layout.remove_widget(self.ff_btn)
            
        self.ff_btn = Button(
            text="FF: OFF", font_size='14sp', bold=True,
            size_hint=(None, None), size=(dp(80), dp(40)),
            pos_hint={'right': 0.95, 'top': 0.98}, # วางไว้มุมขวาบน
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        self.ff_btn.bind(on_release=self.toggle_fast_forward)
        self.root_layout.add_widget(self.ff_btn)
            
        self.board_area = BoxLayout(orientation='vertical', size_hint_x=0.75)
        
        app_timer = getattr(app, 'selected_time_limit', 0) or 0
        self.turn_timer_limit = app_timer
        self.turn_timer_remaining = app_timer
        
        self.info_label = Label(
            text="WHITE'S TURN", color=(0.83, 0.68, 0.21, 1),
            bold=True, font_size='22sp', markup=True, size_hint_y=0.08
        )
        self.board_area.add_widget(self.info_label)
        
        self.play_area = BoxLayout(orientation='vertical', size_hint_y=0.92)
        
        # ส่วนพื้นที่กระดานหลัก
        self.board_anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.75)
        self.play_area.add_widget(self.board_anchor)

        # ✨ พื้นที่สำหรับ UI ด้านล่าง (สลับ 2D / 3D ทีหลัง)
        self.bottom_area = BoxLayout(orientation='vertical', size_hint_y=0.25)
        self.play_area.add_widget(self.bottom_area)
        
        # ✨ แอด play_area ลงใน board_area แค่รอบเดียวเท่านั้น (แก้บั๊ก Add ซ้ำ)
        self.board_area.add_widget(self.play_area)
        self.main_layout.add_widget(self.board_area)
        
        self.sidebar_panel = BoxLayout(orientation='vertical', size_hint_x=0.25, padding=10, spacing=10)
        with self.sidebar_panel.canvas.before:
            Color(0.03, 0.03, 0.05, 0.85); self.sb_bg = Rectangle(pos=self.sidebar_panel.pos, size=self.sidebar_panel.size)
        self.sidebar_panel.bind(pos=self._update_sb_bg, size=self._update_sb_bg)
        
        self.info_zone = BoxLayout(orientation='vertical', size_hint_y=0.45); self.sidebar_panel.add_widget(self.info_zone)
        self.divider = Widget(size_hint_y=None, height=dp(2))
        with self.divider.canvas.before:
            Color(0.3, 0.3, 0.35, 1); self.div_rect = Rectangle(pos=self.divider.pos, size=self.divider.size)
        self.divider.bind(pos=self._update_div_bg, size=self._update_div_bg)
        
        def on_quit_action():
            self.on_quit()
                
        self.sidebar = SidebarUI(on_undo_callback=self.on_undo_click, on_quit_callback=on_quit_action, game_mode=mode)
        self.sidebar.size_hint_y = 0.55; self.sidebar_panel.add_widget(self.sidebar); self.main_layout.add_widget(self.sidebar_panel)
        
        self.init_board_ui()
        if mode == 'Divide_Conquer':
            self.deployment_manager.setup_deployment_ui()
        
        if self.turn_timer_limit > 0:
            self.start_turn_timer()

    def highlight_headers(self):
        for (r, c), square in self.squares.items():
            if hasattr(square, 'header_line') and square.header_line in square.canvas.after.children:
                square.canvas.after.remove(square.header_line)
            if hasattr(square, 'header_color') and square.header_color in square.canvas.after.children:
                square.canvas.after.remove(square.header_color)
            piece = self.game.board[r][c]
            if piece and getattr(piece, 'is_header', False):
                with square.canvas.after:
                    square.header_color = Color(1, 0.9, 0, 1)
                    square.header_line = Line(rectangle=(square.x, square.y, square.width, square.height), width=dp(2.5))
                
                def update_line(inst, val, s=square):
                    if hasattr(s, 'header_line'):
                        s.header_line.rectangle = (s.x, s.y, s.width, s.height)
                square.bind(pos=update_line, size=update_line)

    def setup_divide_conquer_board(self, app):
        self.game.board = [[None for _ in range(8)] for _ in range(8)]
        
        # Defender spawns at TOP (ranks 0, 1, 2)
        enemy_army_list = app.combat_target_army
        valid_coords = [(r, c) for r in range(3) for c in range(8)]
        random.shuffle(valid_coords)
        for p, (r, c) in zip(enemy_army_list, valid_coords):
            p.color = 'black'
            p.forward_dir = 1
            self.game.board[r][c] = p
            
        # Attacker spawns at BOTTOM (ranks 7, 6, 5)
        player_army_list = app.combat_marching_army
        coords = [(r, c) for r in range(7, 4, -1) for c in range(8)] 
        for p, (r, c) in zip(player_army_list, coords):
            p.color = 'white'
            p.forward_dir = -1
            self.game.board[r][c] = p
            
        self.game.current_turn = 'white'
        

    def _update_inv_bg(self, instance, value): self.inv_bg.pos, self.inv_bg.size = instance.pos, instance.size
    def _update_sb_bg(self, instance, value): self.sb_bg.pos, self.sb_bg.size = instance.pos, instance.size
    def _update_div_bg(self, instance, value): self.div_rect.pos, self.div_rect.size = instance.pos, instance.size
    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect') and hasattr(self, 'grid'):
            self.bg_rect.pos, self.bg_rect.size = self.grid.pos, self.grid.size

    def init_board_ui(self):
        saved_camera = None
        if hasattr(self, 'board_3d') and self.board_3d in self.board_anchor.children:
            saved_camera = (self.board_3d.rot_x, self.board_3d.rot_y, self.board_3d.cam_dist)
        self.board_anchor.clear_widgets()
        gm = getattr(self, 'game_mode', 'PVP')
        
        is_bot = False
        app = App.get_running_app()
        match_type = getattr(app, 'match_type', 'PVE')
        
        if gm == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'white') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            current_faction = attacker_faction if self.game.current_turn == 'white' else defender_faction
            
            if match_type == 'PVE':
                player_involved = (attacker_faction == 'white' or defender_faction == 'white')
                if not player_involved: is_bot = True
                elif current_faction != 'white': is_bot = True
            elif match_type == 'LOCAL_PVP':
                if current_faction == 'red': is_bot = True
        else:
            if match_type == 'PVE' and self.game.current_turn == 'black':
                is_bot = True
                
        phase = getattr(self, 'battle_phase', 'playing')
        
        if phase == 'playing':
            vp = 'white' if is_bot else self.game.current_turn 
        elif phase == 'deployment_arrange_def':
            vp = 'black'
        else:
            vp = 'white'
            
        if hasattr(self, 'current_vp') and self.current_vp == vp:
            # ✨ แก้ไข: เช็คว่าถ้ามีกระดาน 3D อยู่แล้ว ก็ให้ข้ามการสร้างใหม่ไปเลย กล้องจะได้ไม่รีเซ็ต
            if (hasattr(self, 'grid') and self.grid in self.board_anchor.children) or \
               (hasattr(self, 'board_3d') and self.board_3d in self.board_anchor.children):
                self.refresh_ui()
                return
            
        self.current_vp = vp
        
        # ดึงค่า Dimension จาก Options
        self.current_dimension = getattr(App.get_running_app(), 'selected_dimension', '2D')
        map_name = getattr(self.game, 'map_name', 'Classic Board')

        # สีพื้นตาราง
        if ForestMap and isinstance(self.game, ForestMap): t_light, t_dark = (0.55, 0.65, 0.55, 1), (0.35, 0.45, 0.35, 1)
        elif DesertMap and isinstance(self.game, DesertMap): t_light, t_dark = (0.9, 0.65, 0.2, 1), (0.7, 0.45, 0.1, 1)
        elif TundraMap and isinstance(self.game, TundraMap): t_light, t_dark = (0.5, 0.8, 0.95, 1), (0.15, 0.4, 0.75, 1)
        else: t_light, t_dark = (0.8, 0.8, 0.8, 1), (0.4, 0.4, 0.4, 1)

        # ✨ เคลียร์ UI ด้านล่างเก่าทิ้งก่อน
        self.bottom_area.clear_widgets()

        # ====================================================
        # 🟢 กรณีเป็นโหมด 2D CLASSIC
        # ====================================================
        if self.current_dimension == '2D':
            self.board_anchor.size_hint_y = 0.82
            self.bottom_area.size_hint_y = 0.18
            
            # 1. วาดกระดาน 2D
            self.grid = GridLayout(cols=8, rows=8, size_hint=(None, None), spacing=0, padding=0)
            self.board_anchor.add_widget(self.grid)
            self.board_anchor.bind(size=self._keep_grid_square)
            if self.board_anchor.width > 0: self._keep_grid_square(self.board_anchor, self.board_anchor.size)
            
            if hasattr(self.game, 'bg_image') and self.game.bg_image != '':
                with self.grid.canvas.before:
                    Color(1, 1, 1, 1)
                    self.bg_rect = Rectangle(source=self.game.bg_image, pos=self.grid.pos, size=self.grid.size)
                self.grid.bind(pos=self._update_bg, size=self._update_bg)
                
            self.squares = {}
            for r in (range(8) if vp == 'white' else range(7, -1, -1)):
                for c in (range(8) if vp == 'white' else range(7, -1, -1)):
                    sq = ChessSquare(row=r, col=c, is_2d=True)
                    sq.bind(on_release=self.on_square_tap)
                    self.grid.add_widget(sq)
                    self.squares[(r, c)] = sq

            # 2. วาด Inventory แบบเก่า (2D)
            self.inv_anchor = AnchorLayout(anchor_x='center', anchor_y='top', padding=[0, dp(10), 0, dp(20)])
            self.inventory_layout = BoxLayout(orientation='horizontal', size_hint_x=0.85, spacing=dp(10), padding=dp(10))
            with self.inventory_layout.canvas.before:
                Color(0.05, 0.05, 0.07, 0.6)
                self.inv_bg = Rectangle(pos=self.inventory_layout.pos, size=self.inventory_layout.size)
            self.inventory_layout.bind(pos=self._update_inv_bg, size=self._update_inv_bg)
            self.inv_anchor.add_widget(self.inventory_layout)
            self.bottom_area.add_widget(self.inv_anchor)

        # ====================================================
        # 🟡 กรณีเป็นโหมด 2D ISO (Isometric ดั้งเดิม)
        # ====================================================
        elif self.current_dimension == '2D iso':
            self.board_anchor.size_hint_y = 0.82
            self.bottom_area.size_hint_y = 0.18
            
            tile_w = dp(160)
            tile_h = dp(80)
            board_width = tile_w * 8
            board_height = tile_h * 8

            self.grid = CameraBoard(size_hint=(None, None), size=(board_width, board_height))
            self.board_layer = FloatLayout(size_hint=(1, 1))
            self.piece_layer = FloatLayout(size_hint=(1, 1))
            self.grid.add_widget(self.board_layer)
            self.grid.add_widget(self.piece_layer)
            self.board_anchor.add_widget(self.grid)
                
            self.squares = {}
            offset_x = self.grid.width / 2
            offset_y = dp(50) 
            
            def get_render_rc(r, c):
                return (r, c) if vp == 'white' else (7 - r, 7 - c)
                
            coords = [(r, c) for r in range(8) for c in range(8)]
            coords.sort(key=lambda coord: get_render_rc(coord[0], coord[1])[0] + get_render_rc(coord[0], coord[1])[1])
            
            for r, c in coords:
                sq = ChessSquare(row=r, col=c, is_2d=False, piece_layer=self.piece_layer, tile_color_light=t_light, tile_color_dark=t_dark)
                sq.bind(on_release=self.on_square_tap)
                
                rr, rc = get_render_rc(r, c)
                iso_x = (rr - rc) * (tile_w / 2)
                iso_y = (14 - (rr + rc)) * (tile_h / 2)
                
                sq.size_hint = (None, None)
                sq.size = (tile_w, tile_h)
                sq.pos = (iso_x + offset_x - (tile_w / 2), iso_y + offset_y)
                
                self.board_layer.add_widget(sq)
                self.squares[(r, c)] = sq

            # ✨ นำโค้ดส่วนนี้กลับมาวางต่อท้าย เพื่อสร้างกล่อง Inventory ให้โหมดนี้
            self.inv_anchor = AnchorLayout(anchor_x='center', anchor_y='top', padding=[0, dp(10), 0, dp(20)])
            self.inventory_layout = BoxLayout(orientation='horizontal', size_hint_x=0.85, spacing=dp(10), padding=dp(10))
            with self.inventory_layout.canvas.before:
                Color(0.05, 0.05, 0.07, 0.6)
                self.inv_bg = Rectangle(pos=self.inventory_layout.pos, size=self.inventory_layout.size)
            self.inventory_layout.bind(pos=self._update_inv_bg, size=self._update_inv_bg)
            self.inv_anchor.add_widget(self.inventory_layout)
            self.bottom_area.add_widget(self.inv_anchor)


        # ====================================================
        # 🔴 กรณีเป็นโหมด 2.5D (3D)
        # ====================================================
        else:
            # ✨ 1. แก้ปัญหาการ์ดแหว่ง โดยใช้ Fixed Height แทน %
            self.bottom_area.size_hint_y = None
            self.bottom_area.height = dp(320) # ล็อกความสูงให้พอดีกับการ์ด + เมนู
            self.board_anchor.size_hint_y = 1 # ให้กระดาน 3D ยืดใช้พื้นที่ที่เหลือทั้งหมด

            # วาดกระดาน 3D (รวมพารามิเตอร์สีและลบการบรรทัดที่สร้างซ้ำทิ้ง)
            self.board_3d = Board3D(
                map_name=map_name, 
                on_square_click=self.handle_3d_click, 
                tile_color_light=t_light, 
                tile_color_dark=t_dark, 
                size_hint=(1, 1)
            )
            
            if saved_camera:
                self.board_3d.rot_x = saved_camera[0]
                self.board_3d.rot_y = saved_camera[1]
                self.board_3d.cam_dist = saved_camera[2]
            self.board_anchor.add_widget(self.board_3d)

            from kivy.uix.scrollview import ScrollView
            
            # ✨ 2. เพิ่มโซน Action Menu (โผล่มาเหนือไพ่เวลาจะเดิน)
            self.action_menu_container = ScrollView(size_hint=(1, 0.25), do_scroll_y=False, do_scroll_x=True)
            self.action_menu_layout = BoxLayout(orientation='horizontal', size_hint_x=None, spacing=dp(10), padding=[dp(10), 0])
            self.action_menu_layout.bind(minimum_width=self.action_menu_layout.setter('width'))
            self.action_menu_container.add_widget(self.action_menu_layout)
            self.bottom_area.add_widget(self.action_menu_container)

            # 3. โซนไพ่ในมือและปุ่มกระเป๋า
            hand_container = FloatLayout(size_hint=(1, 0.75))
            
            self.hand_scroll = ScrollView(size_hint=(0.85, 1), pos_hint={'right': 1, 'y': 0}, do_scroll_y=False, do_scroll_x=True)
            self.hand_layout = BoxLayout(orientation='horizontal', size_hint_x=None, spacing=dp(10), padding=dp(10))
            self.hand_layout.bind(minimum_width=self.hand_layout.setter('width'))
            self.hand_scroll.add_widget(self.hand_layout)
            hand_container.add_widget(self.hand_scroll)
            
            self.bag_btn = Button(
                text="BAG\n(Items)", font_size='12sp', bold=True, halign='center',
                size_hint=(0.12, 0.8), pos_hint={'x': 0.02, 'center_y': 0.5},
                background_color=(0.15, 0.15, 0.2, 0.9)
            )
            self.bag_btn.bind(on_release=self.bottom_ui.open_bag_popup) 
            hand_container.add_widget(self.bag_btn)
            
            self.bottom_area.add_widget(hand_container)
            
        # ====================================================
        # เคลียร์ปุ่ม Toggle เก่าทิ้งก่อน เพื่อป้องกันปุ่มซ้อนกัน
        # ====================================================
        if hasattr(self, 'sidebar_toggle_btn') and self.sidebar_toggle_btn in self.root_layout.children:
            self.root_layout.remove_widget(self.sidebar_toggle_btn)
        if hasattr(self, 'inv_toggle_btn') and self.inv_toggle_btn in self.root_layout.children:
            self.root_layout.remove_widget(self.inv_toggle_btn)

        # --- ส่วนที่ 1: ปุ่มเปิด/ปิด Sidebar ---
        self.sidebar_is_open = True
        self.sidebar_toggle_btn = Button(
            text=">", font_size='24sp', bold=True,
            size_hint=(None, None), size=(dp(30), dp(60)),
            pos_hint={'right': 1, 'center_y': 0.5},
            background_color=(0.1, 0.1, 0.1, 0.8)
        )
        self.sidebar_toggle_btn.bind(on_release=self.toggle_sidebar)
        self.root_layout.add_widget(self.sidebar_toggle_btn)

        # --- ส่วนที่ 2: ปุ่มเปิด/ปิด Inventory (แสดงบนโหมด 2D และ 2D iso) ---
        if self.current_dimension in ['2D', '2D iso']:
            self.inv_is_open = True
            self.inv_toggle_btn = Button(
                text="v", font_size='24sp', bold=True,
                size_hint=(None, None), size=(dp(60), dp(30)),
                pos_hint={'center_x': 0.5, 'y': 0}, # 🟢 เปลี่ยนเป็น 0 ให้อยู่ขอบล่างเสมอ
                background_color=(0.1, 0.1, 0.1, 0.8)
            )
            self.inv_toggle_btn.bind(on_release=self.toggle_inventory)
            self.root_layout.add_widget(self.inv_toggle_btn)
            
        self.refresh_ui()


    def handle_3d_click(self, row, col):
        # ปั้นโครงสร้างพารามิเตอร์หลอกเพื่อโยนให้ฟังก์ชัน on_square_tap เดิมของคุณประมวลผลต่อ
        class DummyInstance:
            def __init__(self, r, c):
                self.row = r
                self.col = c
        self.on_square_tap(DummyInstance(row, col))

    # ฟังก์ชันสไลด์ Sidebar[cite: 9]
    def toggle_sidebar(self, instance):
        if self.sidebar_is_open:
            # เลื่อนออกไปทางขวาจนพ้นจอ
            anim = Animation(x=self.width, duration=0.3, transition='out_expo')
            anim.start(self.sidebar_panel)
            instance.text = "<"
            # ขยับปุ่มลูกศรตามไปด้วย
            anim_btn = Animation(x=self.width - instance.width, duration=0.3, transition='out_expo')
            anim_btn.start(instance)
        else:
            # เลื่อนกลับมาตำแหน่งเดิม
            anim = Animation(x=self.width - self.sidebar_panel.width, duration=0.3, transition='out_expo')
            anim.start(self.sidebar_panel)
            instance.text = ">"
            # ขยับปุ่มลูกศรกลับมา
            anim_btn = Animation(x=self.width - self.sidebar_panel.width - instance.width, duration=0.3, transition='out_expo')
            anim_btn.start(instance)
            
        self.sidebar_is_open = not self.sidebar_is_open

    # ฟังก์ชันสไลด์ Inventory[cite: 10]
    def toggle_inventory(self, instance):
        if self.inv_is_open:
            # เลื่อนลงล่างให้ซ่อนไป
            anim = Animation(y=-self.inventory_layout.height, duration=0.3, transition='out_expo')
            anim.start(self.inventory_layout)
            instance.text = "^"
            # 🟢 เอาโค้ดแอนิเมชันขยับปุ่มออก ปล่อยให้ปุ่มอยู่ขอบล่างจอไปเลย
        else:
            # เลื่อนกลับขึ้นมา
            anim = Animation(y=0, duration=0.3, transition='out_expo') 
            anim.start(self.inventory_layout)
            instance.text = "v"
            # 🟢 เอาโค้ดแอนิเมชันขยับปุ่มออกเช่นกัน
            
        self.inv_is_open = not self.inv_is_open

    def _keep_grid_square(self, instance, value):
        side = (int(min(instance.width, instance.height)) // 8) * 8
        if hasattr(self, 'grid'): self.grid.size = (side, side); Clock.schedule_once(self._update_bg, 0)

    def update_countdown(self, dt):
        self.countdown_time -= 1
        if self.countdown_time <= 0:
            if self.countdown_event:
                self.countdown_event.cancel()
                self.countdown_event = None
            self.auto_quit_to_setup(0)
        else:
            self.info_label.text = f"[color=ff3333][b]{self.game.game_result}[/b][/color]\n[color=ffff00][size=16sp]Returning to map in {self.countdown_time}s...[/size][/color]"

    def refresh_ui(self, legal_moves=None):
        if legal_moves is None:
            legal_moves = []

        # ✨ เพิ่ม '2D iso' เข้าไปในรายการอนุญาตให้อัปเดต Inventory
        current_dim = getattr(self, 'current_dimension', '2D')
        if current_dim in ['2D', '2D iso']:
            self.update_inventory_ui()
        else:
            self.update_hand_ui()

        # ✨ สร้างปุ่มเดิน/สลับตำแหน่ง (Action Menu) สำหรับโหมด 3D
            if hasattr(self, 'action_menu_layout'):
                self.action_menu_layout.clear_widgets()
                if self.selected and legal_moves:
                    phase = getattr(self, 'battle_phase', 'playing')
                    
                    for r, c in legal_moves:
                        # 1. จัดข้อความบนปุ่ม (ถ้าอยู่ในช่วงจัดทัพให้ใช้คำว่า SWAP)
                        if phase in ['deployment_arrange_atk', 'deployment_arrange_def']:
                            btn_text = f"SWAP\n{chr(65+c)}{r+1}"
                            bg_col = (0.8, 0.4, 0.1, 1) # สีส้มสำหรับสลับที่
                        else:
                            btn_text = f"MOVE\n{chr(65+c)}{r+1}"
                            bg_col = (0.2, 0.6, 0.8, 1) # สีฟ้าสำหรับเดินปกติ
                            
                        # 2. สร้างปุ่มลงไปเรียงกัน
                        btn = Button(
                            text=btn_text, 
                            size_hint=(None, 1), 
                            width=dp(70),
                            background_color=bg_col,
                            bold=True,
                            halign='center'
                        )
                        # 3. จำลองพฤติกรรมให้เหมือนผู้เล่นเอานิ้วไปจิ้มกระดานตรงๆ
                        btn.bind(on_release=lambda x, row=r, col=c: self.handle_3d_click(row, col))
                        self.action_menu_layout.add_widget(btn)
        
        phase = getattr(self, 'battle_phase', 'playing')
        
        # 1. จัดการเรื่อง UI ข้อความและสถานะเกม
        if self.game.game_result:
            self.stop_turn_timer()
            if not getattr(self, '_end_played', False):
                if "WHITE WINS" in self.game.game_result.upper() and getattr(self, 'game_mode', 'PVP') in ['PVE', 'Divide_Conquer']:
                    App.get_running_app().play_victory_sound()
                elif "BLACK WINS" in self.game.game_result.upper() and getattr(self, 'game_mode', 'PVP') in ['PVE', 'Divide_Conquer']:
                    App.get_running_app().play_lose_sound()
                self._end_played = True
                
            if not getattr(self, '_game_over_scheduled', False): 
                self._game_over_scheduled = True
                self.countdown_time = 10
                self.countdown_event = Clock.schedule_interval(self.update_countdown, 1.0)
                if hasattr(self.sidebar, 'action_btn_layout'):
                    for child in self.sidebar.action_btn_layout.children:
                        if isinstance(child, Button) and ("Quit" in child.text or "Retreat" in child.text):
                            child.text = "Skip Countdown"
                            child.background_color = (0.2, 0.6, 0.2, 1)
            
            if getattr(self, 'countdown_time', 0) > 0:
                self.info_label.text = f"[color=ff3333][b]{self.game.game_result}[/b][/color]\n[color=ffff00][size=16sp]Returning to map in {self.countdown_time}s...[/size][/color]"
            else:
                self.info_label.text = f"[color=ff3333][b]{self.game.game_result}[/b][/color]"

        # 3. แยกการทำงานระหว่าง 2D และ 3D (ตัด return ออกเพื่อให้ UI ทำงานครบถ้วน)
        if hasattr(self, 'board_3d') and self.board_3d in self.board_anchor.children:
            # อัปเดตตัวหมากในโหมด 3D
            self.board_3d.draw_pieces(
                self.game.board, 
                lambda piece: self.get_piece_image_path(piece),
                selected=self.selected,
                legal_moves=legal_moves,
                last_move=getattr(self.game, 'last_move', []),
                game_mode=getattr(self, 'game_mode', 'classic'), # ✨ โยนเข้ากระดาน 3D
                phase=phase,                                     # ✨ โยนเข้ากระดาน 3D
                current_player=self.game.current_turn            # ✨ โยนเข้ากระดาน 3D
            )
            
        elif hasattr(self, 'squares'):
            # อัปเดตกระดานและตัวหมากในโหมด 2D และ 2D iso
            cp = self.game.find_king(self.game.current_turn) if self.game.is_in_check(self.game.current_turn) else None
            
            if phase == 'deployment_arrange_atk':
                for (r, c), sq in self.squares.items():
                    is_deploy_zone = (r >= 5)
                    is_enemy_zone = (r <= 2) # โซนฝ่ายรับที่ยังเป็นความลับ
                    is_legal_deploy = (is_deploy_zone and self.selected is not None and (r, c) != self.selected)
                    
                    sq.update_square_style(highlight=(self.selected == (r, c)), is_legal=('move' if is_legal_deploy else False), is_check=False, is_last=False)
                    p = self.game.board[r][c]
                    
                    # ✨ ถ้าเป็น 2D iso ให้ตั้งภาพ hidden_enemy แทนแผ่นดำ
                    if is_enemy_zone and getattr(self, 'current_dimension', '2D') == '2D iso':
                        sq.set_piece_icon('assets/ui/hidden_enemy.png', piece=None)
                    elif not is_deploy_zone: 
                        sq.set_piece_icon(None, piece=None)
                    else: 
                        sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
                        
            elif phase == 'deployment_arrange_def':
                for (r, c), sq in self.squares.items():
                    is_deploy_zone = (r <= 2)
                    is_legal_deploy = (is_deploy_zone and self.selected is not None and (r, c) != self.selected)
                    
                    sq.update_square_style(highlight=(self.selected == (r, c)), is_legal=('move' if is_legal_deploy else False), is_check=False, is_last=False)
                    p = self.game.board[r][c]
                    
                    # ✨ Logic ใหม่: ฝ่ายรับต้องมองเห็นทหารฝ่ายบุก (แถว 5+) ที่จัดทัพเสร็จแล้ว
                    if not is_deploy_zone and not (r >= 5): 
                        # ตรงกลาง (แถว 3-4) ให้ว่างเปล่า
                        sq.set_piece_icon(None, piece=None)
                    else: 
                        # แสดงทหารฝั่งตัวเอง (0-2) และฝั่งบุก (5-7) ตามปกติ ไม่มี Hidden Enemy
                        sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
                        
            elif phase == 'deployment_reveal':
                enemy_header_pos = None
                for r in range(8):
                    for c in range(8):
                        p = self.game.board[r][c]
                        if p and p.color == 'black':
                            if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False):
                                enemy_header_pos = (r, c); break
                    if enemy_header_pos: break
                for (r, c), sq in self.squares.items():
                    is_king = ((r, c) == enemy_header_pos)
                    sq.update_square_style(highlight=False, is_legal=False, is_check=is_king, is_last=False)
                    p = self.game.board[r][c]
                    sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
            else:
                for (r, c), sq in self.squares.items():
                    il = (r, c) in (self.game.last_move or [])
                    is_legal = (r, c) in legal_moves
                    is_attack = False
                    
                    if is_legal and self.selected:
                        target_piece = self.game.board[r][c]
                        selected_piece = self.game.board[self.selected[0]][self.selected[1]]
                        if target_piece and target_piece.color != selected_piece.color:
                            is_attack = True
                        elif not target_piece and hasattr(selected_piece, 'type') and selected_piece.type == 'pawn':
                            sr, sc = self.selected
                            if sc != c: is_attack = True
                    sq.update_square_style(
                        highlight=(self.selected == (r, c)), 
                        is_legal=('attack' if is_attack else is_legal), 
                        is_check=((r,c) == cp), 
                        is_last=il
                    )
                    p = self.game.board[r][c]
                    flip_piece = False if p and p.color != self.current_vp else True
                    sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p, flip=flip_piece)
                    
                    # --- ❄️ เริ่ม: เพิ่มระบบวางรูปแช่แข็งทับตัวละคร ---
                    # ลบรูปแช่แข็งเก่าออกก่อน (ถ้ามี) เพื่อป้องกันการซ้อนทับกันหลายชั้น
                    if hasattr(sq, 'freeze_icon') and sq.freeze_icon:
                        if sq.freeze_icon.parent:
                            sq.freeze_icon.parent.remove_widget(sq.freeze_icon)
                        sq.freeze_icon = None
                        
                    if p and getattr(p, 'freeze_timer', 0) > 0:
                        is_iso = getattr(self, 'current_dimension', '2D') == '2D iso'
                        
                        if is_iso:
                            # โหมด ISO: ดึงภาพไปวางบน piece_layer เพื่อให้ทับตัวหมากได้
                            # ปรับขนาด dp ให้ใหญ่ขึ้นเพื่อให้คลุมหมากมิด 
                            icon_size = (dp(140), dp(140))
                            sq.freeze_icon = Image(
                                source=f"assets/pieces/event/event4.png",
                                size_hint=(None, None),
                                size=icon_size,
                                # ขยับตำแหน่ง Y ขึ้น (dp(25)) เพื่อให้ภาพอยู่ตรงกลางตัวหมากพอดี (ไม่จมลงฐาน)
                                pos=(sq.center_x - icon_size[0]/2, sq.center_y - icon_size[1]/2 + dp(25))
                            )
                            # ต้องเพิ่มลงใน piece_layer ภาพถึงจะทับตัวละครได้
                            self.piece_layer.add_widget(sq.freeze_icon)
                        else:
                            # โหมด 2D ปกติ
                            sq.freeze_icon = Image(
                                source=f"assets/pieces/event/event4.png",
                                size_hint=(1.2, 1.2), # ขยายจาก 0.9 เป็น 1.2 ให้ใหญ่ล้นกรอบนิดๆ
                                pos_hint={'center_x': 0.5, 'center_y': 0.5}
                            )
                            sq.add_widget(sq.freeze_icon)
                    # --- จบ: ระบบแช่แข็ง ---
                
                self.highlight_headers()

    def show_item_tooltip(self, item):
        self.hide_item_tooltip(); self.item_tooltip = ItemTooltip(item); self.root_layout.add_widget(self.item_tooltip)
        
    def hide_item_tooltip(self):
        if self.item_tooltip: self.root_layout.remove_widget(self.item_tooltip); self.item_tooltip = None

    def get_piece_image_path(self, piece):
        if not piece: return None
        p_n = piece.__class__.__name__.lower()
        if p_n == 'obstacle':
            ot = piece.name.lower()
            # ✨ เพิ่มเงื่อนไขเพื่อใช้รูปลูกบาศก์น้ำแข็ง (event5) สำหรับด่าน Tundra
            if ot == 'ice':
                return f"assets/pieces/event/event5.png"
            return f"assets/pieces/event/event{'1' if ot=='thorn' else '2' if ot=='sandstorm' else '3'}.png"
            
        # 1. ดึงสีและเผ่าดั้งเดิมของ Backend (ระบบจะมองเป็น white/black เสมอ)
        display_color = piece.color
        tf = getattr(piece, 'tribe', self.get_tribe_name(display_color))
        
        # 2. ภาพลวงตา: สับเปลี่ยนสีเฉพาะการแสดงผลในโหมด Divide & Conquer
        if getattr(self, 'game_mode', '') == 'Divide_Conquer':
            app = App.get_running_app()
            
            # ถ้าหมากเป็นสีขาว (หมายถึงฝ่ายบุก) ให้ดึงสีและเผ่าจริงจาก combat_source
            if piece.color == 'white':
                real_faction = getattr(app.combat_source, 'faction', 'white') if hasattr(app, 'combat_source') else 'white'
                display_color = real_faction
                # ✨ แก้ไข: บังคับหาชื่อเผ่าจาก Faction จริง ห้ามดึงของเก่ามาใช้
                tf = self.get_tribe_name(real_faction) 
                
            # ถ้าหมากเป็นสีดำ (หมายถึงฝ่ายกัน) ให้ดึงสีและเผ่าจริงจาก combat_target
            elif piece.color == 'black':
                real_faction = getattr(app.combat_target, 'faction', 'black') if hasattr(app, 'combat_target') else 'black'
                display_color = real_faction
                # จัดการกรณีสีแดง (หมู่บ้าน/Rebel)
                if display_color == 'red':
                    # ✨ แก้ไข: บังคับเผ่าโจร 100% ถ้าเป็นฝั่งสีแดง
                    tf = 'bandit' 
                else:
                    # ✨ แก้ไข: บังคับหาชื่อเผ่าจาก Faction จริง ห้ามดึงของเก่ามาใช้
                    tf = self.get_tribe_name(real_faction)

        return safe_piece_path(piece, tf, display_color)

    def on_square_tap(self, instance):
        if getattr(self.game, 'game_result', None): return
        
        App.get_running_app().play_click_sound()
        r, c = instance.row, instance.col
        
        phase = getattr(self, 'battle_phase', 'playing')
        piece = self.game.board[r][c]
        print(f"[DEBUG] Click Event - current_turn: {self.game.current_turn}, clicked_piece_color: {getattr(piece, 'color', None)}, is_input_locked: {getattr(self, 'is_input_locked', False)}, phase: {phase}")
        
        # ==========================================
        # 🟢 โหมดจัดทัพฝ่ายบุก (Attacker - 3 แถวล่าง)
        # ==========================================
        if phase == 'deployment_arrange_atk':
            if r < 5: return # ห้ามคลิกเกิน 3 แถว
            
            if self.selected is None:
                piece = self.game.board[r][c]
                if piece and piece.color == self.game.current_turn:
                    self.selected = (r, c)
                    # ✨ 1. สร้างพื้นที่เดินให้ครอบคลุม 3 แถว (แถว 5, 6, 7) และส่งให้ UI แสดงแสงไฮไลต์
                    legal_moves = [(dr, dc) for dr in range(5, 8) for dc in range(8) if (dr, dc) != (r, c)]
                    self.refresh_ui(legal_moves)
                    self.show_piece_status(piece)
            else:
                sr, sc = self.selected
                if (r, c) == (sr, sc): 
                    self.selected = None; self.hide_piece_status(); self.refresh_ui(); return
                
                # ✨ 2. ระบบสลับที่ (Swap) ไม่ว่าช่องเป้าหมายจะว่างหรือมีทหารอยู่ ก็สลับที่กันได้เลย
                target_piece = self.game.board[r][c]
                self.game.board[r][c] = self.game.board[sr][sc]
                self.game.board[sr][sc] = target_piece
                self.selected = None; self.hide_piece_status(); self.refresh_ui()
            return
            
        # ==========================================
        # 🔴 โหมดจัดทัพฝ่ายรับ (Defender - 3 แถวบน)
        # ==========================================
        elif phase == 'deployment_arrange_def':
            if r > 2: return # ห้ามคลิกเกิน 3 แถว
            
            if self.selected is None:
                piece = self.game.board[r][c]
                if piece and piece.color == 'black': 
                    self.selected = (r, c)
                    # ✨ 1. สร้างพื้นที่เดินให้ครอบคลุม 3 แถว (แถว 0, 1, 2)
                    legal_moves = [(dr, dc) for dr in range(3) for dc in range(8) if (dr, dc) != (r, c)]
                    self.refresh_ui(legal_moves)
                    self.show_piece_status(piece)
            else:
                sr, sc = self.selected
                if (r, c) == (sr, sc): 
                    self.selected = None; self.hide_piece_status(); self.refresh_ui(); return
                
                # ✨ 2. ระบบสลับที่ (Swap) ฝั่งตั้งรับ
                target_piece = self.game.board[r][c]
                self.game.board[r][c] = self.game.board[sr][sc]
                self.game.board[sr][sc] = target_piece
                self.selected = None; self.hide_piece_status(); self.refresh_ui()
            return
            
        elif phase == 'deployment_reveal':
            return 
            
        if getattr(self, 'is_input_locked', False): return 
        if getattr(self, 'crash_popup', None): return
        
        piece = self.game.board[r][c]
        #if piece and getattr(piece, 'macro_faction', None) == 'red': return
        
        if getattr(self.game, 'game_result', None): 
            if not self.selected_item: return
            

        
        if self.selected_item:
            if piece and piece.color == self.game.current_turn:
                if getattr(piece, 'item', None) is not None:
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                if self.selected_item.id == 9 and piece.__class__.__name__.lower() == 'knight':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                if self.selected_item.id == 10 and piece.__class__.__name__.lower() != 'pawn':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                    
                self.controller.submit_item_use(self.selected_item, piece, self.game.current_turn)
                self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); self.show_piece_status(piece)
            else: self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui()
            return
            
        if getattr(self.game, 'game_result', None): return
            
        if self.selected is None:
            if piece and piece.color == self.game.current_turn:
                self.selected = (r, c); self.refresh_ui(self.game.get_legal_moves((r, c))); self.show_piece_status(piece)
        else:
            sr, sc = self.selected
            if sr == r and sc == c: self.selected = None; self.hide_piece_status(); self.refresh_ui(); return
            
            atk_piece = self.game.board[sr][sc]
            if atk_piece and atk_piece.__class__.__name__.lower() == 'menatarm':
                bonus = atk_piece.consume_charge_for_attack()
                if bonus > 0:
                    atk_piece.coins += bonus
                    atk_piece.temp_bonus_coins = bonus
                    
            res = self.controller.submit_move(sr, sc, r, c)
            if isinstance(res, tuple) and res[0] == "crash": 
                self.show_crash_overlay(res[1], res[2], (sr, sc), (r, c)); return
                
            if atk_piece and hasattr(atk_piece, 'temp_bonus_coins') and atk_piece.temp_bonus_coins > 0:
                atk_piece.coins -= atk_piece.temp_bonus_coins
                atk_piece.temp_bonus_coins = 0

            if atk_piece:
                atk_piece.mark_moved()
                if hasattr(atk_piece, 'reset_movement_stacks'): atk_piece.reset_movement_stacks()
                
            if res == True and atk_piece and atk_piece.__class__.__name__.lower() == 'levies':
                if (atk_piece.color == 'white' and r == 0) or (atk_piece.color == 'black' and r == 7):
                    res = "promote"
                    
            if res in [True, "promote", "died"]: App.get_running_app().play_move_sound()
            old_color = 'white' if self.game.current_turn == 'black' else 'black'
            
            if res == "promote":
                self.hide_piece_status(); promoted_pawn = self.game.board[r][c] 
                ptribe = getattr(promoted_pawn, 'tribe', self.get_tribe_name(promoted_pawn.color))
                
                is_prince = any(getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False) for row in self.game.board for p in row if p and p.color == promoted_pawn.color)
                is_levies = promoted_pawn.__class__.__name__.lower() == 'levies'
                
                if is_levies and not is_prince:
                    self.selected = None; self.init_board_ui(); self.trigger_end_turn_logic(old_color); return
                    
                def do_p(cls): 
                    self.controller.submit_promotion(r, c, cls)
                    pop.dismiss(); self.init_board_ui(); self.trigger_end_turn_logic(old_color)
                    
                pop = PromotionPopup(promoted_pawn.color, ptribe, do_p, is_prince=is_prince)
                pop.open()
            elif res in [True, "died"]: 
                self.selected = None; self.hide_piece_status(); self.init_board_ui(); self.trigger_end_turn_logic(old_color)
            else: self.selected = None; self.hide_piece_status(); self.refresh_ui()

    def execute_board_move(self, start_pos, end_pos, crash_status):
        self.cancel_crash()
        if crash_status in ["won", "died"]: App.get_running_app().play_crash_win_sound()
        elif crash_status == "draw": App.get_running_app().play_draw_sound()
        
        atk_piece = self.game.board[start_pos[0]][start_pos[1]]
        if atk_piece:
            if hasattr(atk_piece, 'temp_bonus_coins') and atk_piece.temp_bonus_coins > 0:
                atk_piece.coins -= atk_piece.temp_bonus_coins
                atk_piece.temp_bonus_coins = 0
            atk_piece.mark_moved()
            if hasattr(atk_piece, 'reset_movement_stacks'): atk_piece.reset_movement_stacks()
            
        if crash_status == "blocked":
            atk = self.game.board[start_pos[0]][start_pos[1]]
            self.controller.submit_shield_block(start_pos, end_pos)
            self.init_board_ui()
            self.trigger_end_turn_logic(atk.color if atk else 'white')
            return
            
        res = self.controller.submit_crash_resolve(start_pos[0], start_pos[1], end_pos[0], end_pos[1], crash_won=crash_status)
        end_piece = self.game.board[end_pos[0]][end_pos[1]]
        
        if crash_status == "won" and end_piece:
            if end_piece.__class__.__name__.lower() == 'praetorian': end_piece.on_attack_win()
            if end_piece.__class__.__name__.lower() == 'royalguard': end_piece.on_crash_win()
        elif crash_status == "died" and end_piece:
            if end_piece.__class__.__name__.lower() == 'royalguard': end_piece.on_crash_win()
            
        if res in [True, "survived", "defender_survived"] and end_piece and end_piece.__class__.__name__.lower() == 'levies':
            if (end_piece.color == 'white' and end_pos[0] == 0) or (end_piece.color == 'black' and end_pos[0] == 7):
                res = "promote"
                
        if res in [True, "promote", "died"]: App.get_running_app().play_move_sound()
        old_color = 'white' if self.game.current_turn == 'black' else 'black'
        
        if res == "promote":
            pcolor = end_piece.color
            ptribe = getattr(end_piece, 'tribe', self.get_tribe_name(pcolor))
            
            is_prince = any(getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False) for row in self.game.board for p in row if p and p.color == pcolor)
            is_levies = end_piece.__class__.__name__.lower() == 'levies'
            
            if is_levies and not is_prince:
                self.selected = None; self.init_board_ui(); self.trigger_end_turn_logic(old_color); return
                
            if getattr(self, 'game_mode', 'PVP') in ['PVE', 'Divide_Conquer'] and pcolor == 'black':
                from logic.pieces import Queen, Princess
                self.controller.submit_promotion(end_pos[0], end_pos[1], Queen)
                self.init_board_ui(); self.trigger_end_turn_logic(old_color)
            else:
                def do_p(cls): 
                    self.controller.submit_promotion(end_pos[0], end_pos[1], cls); pop.dismiss(); self.init_board_ui(); self.trigger_end_turn_logic(old_color)
                pop = PromotionPopup(pcolor, ptribe, do_p, is_prince=is_prince)
                pop.open()
        elif res in [True, "died", "survived", "defender_survived"]: 
            self.selected = None; self.init_board_ui(); self.trigger_end_turn_logic(old_color)
        else: 
            self.selected = None; self.refresh_ui(); self.trigger_end_turn_logic(old_color)

    def update_inventory_ui(self):
        if not hasattr(self, 'inventory_layout'): 
            return
        self.inventory_layout.clear_widgets()
        info_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(50))
        info_box.add_widget(Label(text="INVENTORY", bold=True, font_size='14sp', color=(0.8, 0.8, 0.8, 1)))
        
        display_color = self.game.current_turn
        
        info_box.add_widget(Label(text=f"[{display_color.upper()}]", bold=True, font_size='16sp', color=(0.83, 0.68, 0.21, 1)))
        self.inventory_layout.add_widget(info_box)
        inv = getattr(self.game, f'inventory_{display_color}', [])
        
        for i in range(5):
            if i < len(inv):
                slot = InventorySlot(img_path=inv[i].image_path, is_selected=(self.selected_item and self.selected_item is inv[i]))
                slot.bind(on_release=lambda x, it=inv[i]: self.on_item_click(it))
                self.inventory_layout.add_widget(slot)
            else: self.inventory_layout.add_widget(InventorySlot())

    def update_hand_ui(self):
        """ สแกนกระดานและวาดการ์ดตัวละครขึ้นมือ (แทนที่ inventory) """
        if not hasattr(self, 'hand_layout'): return
        self.hand_layout.clear_widgets()
        
        # ดึงสีของฝ่ายที่กำลังเข้าเทิร์น
        current_color = self.game.current_turn
        
        # สแกนหาตัวหมากของฝ่ายตัวเองบนกระดาน
        alive_pieces = []
        for r in range(8):
            for c in range(8):
                piece = self.game.board[r][c]
                if piece and piece.color == current_color:
                    alive_pieces.append((piece, r, c))
                    
        # จัดเรียงไพ่ตามประเภท (King ขึ้นก่อน ตามด้วยตัวโหดๆ และ Pawn)
        alive_pieces.sort(key=lambda x: self._get_piece_sort_value(x[0]), reverse=True)
        
        for piece, r, c in alive_pieces:
            img_path = self.get_piece_image_path(piece)
            
            # ✨ 1. คำนวณหาสีที่แท้จริงของ Faction
            display_color = piece.color
            game_mode_str = getattr(self, 'game_mode', 'classic')
            
            if game_mode_str == 'Divide_Conquer':
                app = App.get_running_app()
                if piece.color == 'white':
                    # ฝ่ายบุก (Attacker)
                    display_color = getattr(app.combat_source, 'faction', 'white') if hasattr(app, 'combat_source') else 'white'
                elif piece.color == 'black':
                    # ฝ่ายรับ (Defender)
                    display_color = getattr(app.combat_target, 'faction', 'black') if hasattr(app, 'combat_target') else 'black'

            if img_path:
                # สร้างการ์ดและผูก Event เมื่อถูกเลือก
                card = PieceCard(
                    piece=piece, 
                    image_path=img_path, 
                    row=r, # ✨ ส่งพิกัดแถวให้การ์ด
                    col=c, # ✨ ส่งพิกัดคอลัมน์ให้การ์ด
                    on_select=lambda c_instance, row=r, col=c: self.on_card_selected(c_instance, row, col),
                    on_hover=self.handle_card_hover, # ✨ ผูก Event Hover เข้ากับฟังก์ชันใหม่
                    game_mode=game_mode_str,      
                    display_color=display_color   
                )
                if self.selected == (r, c):
                    card.set_selected_visuals()
                self.hand_layout.add_widget(card)

    def _get_piece_sort_value(self, piece):
        """ ฟังก์ชันย่อยสำหรับจัดเรียงลำดับความสำคัญการ์ดในมือ """
        name = piece.__class__.__name__.lower()
        if name == 'king' or getattr(piece, 'name', '') == 'Prince': return 100
        if name == 'queen': return 90
        if name == 'rook': return 80
        if name == 'bishop': return 70
        if name == 'knight': return 60
        return 10 # พวก Pawn หรือทหารเลว

    def on_card_selected(self, card_instance, r, c):
        """ เมื่อผู้เล่นคลิกการ์ดในมือ """
        App.get_running_app().play_click_sound()
        
        # ล้างการเรืองแสงของการ์ดใบอื่นๆ ก่อน
        for child in self.hand_layout.children:
            if isinstance(child, PieceCard) and child != card_instance:
                child.deselect()
                
        # อัปเดตพิกัดเป็น "ตัวที่เลือก" ในระบบ (เสมือนคลิกตัวหมาก)
        self.selected = (r, c)
        
        # ส่งต่อให้ระบบเก่าโชว์ Status
        self.show_piece_status(card_instance.piece)
        
        # ✨ เช็ค Phase และสร้างพื้นที่เดินแบบอิสระ (Free Swap)
        phase = getattr(self, 'battle_phase', 'playing')
        if phase == 'deployment_arrange_atk':
            # ฝั่งบุก ขยับได้อิสระในแถว 5, 6, 7 (หมายเลข 6, 7, 8 หน้ากระดาน)
            legal_moves = [(dr, dc) for dr in range(5, 8) for dc in range(8) if (dr, dc) != (r, c)]
        elif phase == 'deployment_arrange_def':
            # ฝั่งตั้งรับ ขยับได้อิสระในแถว 0, 1, 2
            legal_moves = [(dr, dc) for dr in range(3) for dc in range(8) if (dr, dc) != (r, c)]
        else:
            # ถ้าเป็นโหมดต่อสู้ปกติ ค่อยใช้กฎหมากรุก
            legal_moves = self.game.get_legal_moves((r, c))
            
        # รีเฟรช UI ให้กระดานแสดงช่องสีฟ้าทั่วทั้ง 3 แถว
        self.refresh_ui(legal_moves)

    def on_item_click(self, item):
        if getattr(self.game, 'game_result', None): return
        App.get_running_app().play_click_sound()
        if getattr(self, 'is_input_locked', False): return 
        if getattr(self, 'crash_popup', None): return
            
        if self.selected_item is item: self.selected_item = None; self.hide_item_tooltip()
        else: self.selected_item = item; self.show_item_tooltip(item)
        self.update_inventory_ui() 

    def trigger_end_turn_logic(self, finished_color):
        for row in self.game.board:
            for p in row:
                if p and p.color == finished_color:
                    if hasattr(p, 'tick_turn'): p.tick_turn()
        
        for row in self.game.board:
            for p in row:
                if p and getattr(p, 'cannot_get_items', False):
                    p.item = None
        
        # Reset the turn timer for the new turn
        self.reset_turn_timer()
                    
        self.ai_controller.check_ai_turn()

    # ---- Turn Timer System ----
    def start_turn_timer(self):
        """Start the per-turn countdown timer."""
        self.turn_timer_remaining = self.turn_timer_limit
        self._update_timer_label()
        if self.turn_timer_event:
            self.turn_timer_event.cancel()
        self.turn_timer_event = Clock.schedule_interval(self._tick_turn_timer, 1.0)

    def stop_turn_timer(self):
        """Stop and clear the turn timer completely."""
        if hasattr(self, 'turn_timer_event') and self.turn_timer_event:
            self.turn_timer_event.cancel()
            self.turn_timer_event = None

    def reset_turn_timer(self):
        """Reset the timer back to full at the start of a new turn."""
        if self.turn_timer_limit <= 0:
            return
        self.turn_timer_remaining = self.turn_timer_limit
        self._update_timer_label()
        # Restart the interval if it was stopped
        if not self.turn_timer_event:
            self.turn_timer_event = Clock.schedule_interval(self._tick_turn_timer, 1.0)

    def on_touch_down(self, touch):
        # We must ALWAYS allow super().on_touch_down to run so UI buttons (like Retreat, Skip) 
        # get the touch events since they are on higher Z-indexes.
        res = super(GameplayScreen, self).on_touch_down(touch)
        
        if res: 
            return True # Touch was absorbed by a UI button/widget
            
        # Stop propagating to other background handlers if game is over
        if getattr(self.game, 'game_result', None): 
            return True
            
        if getattr(self, 'battle_phase', 'playing') != 'playing':
            return False # Let deployment logic handle it
            
        return False

    def _tick_turn_timer(self, dt):
        """Called every second to decrement the turn timer."""
        # Don't tick during non-playing phases or if game is over
        if getattr(self, 'battle_phase', 'playing') != 'playing':
            return
        if getattr(self.game, 'game_result', None):
            self.stop_turn_timer()
            return
        
        self.turn_timer_remaining -= 1
        self._update_timer_label()
        
        if self.turn_timer_remaining <= 0:
            self._on_timer_timeout()

    def _update_timer_label(self):
        """Update the info_label to include the timer inline."""
        if self.turn_timer_limit <= 0:
            return
        if getattr(self.game, 'game_result', None):
            return  # Don't overwrite game-over text
        t = max(0, self.turn_timer_remaining)
        mins, secs = divmod(t, 60)
        # Color shifts: gold -> orange (<=30s) -> red (<=10s)
        if t <= 10:
            timer_color = 'ff3333'
        elif t <= 30:
            timer_color = 'ffaa33'
        else:
            timer_color = 'ffdd55'
        turn_text = f"{self.game.current_turn.upper()}'S TURN"
        self.info_label.text = f"{turn_text}   [color=aaaaaa]|[/color]   [color={timer_color}]{mins:02d}:{secs:02d}[/color]"

    def _on_timer_timeout(self):
        """Handle timer reaching 00:00 — the current player loses."""
        self.stop_turn_timer()
        loser = self.game.current_turn
        if loser == 'white':
            self.game.game_result = "BLACK WINS (Time Out)"
        else:
            self.game.game_result = "WHITE WINS (Time Out)"
        self.init_board_ui()

    def pause_timer(self):
        """Pause the turn timer (e.g., during crash/coin-toss events)."""
        if hasattr(self, 'turn_timer_event') and self.turn_timer_event:
            self.turn_timer_event.cancel()
            self.turn_timer_event = None

    def resume_timer(self):
        """Resume the turn timer after a pause."""
        if self.turn_timer_limit > 0 and self.turn_timer_remaining > 0 and not self.turn_timer_event:
            if not getattr(self.game, 'game_result', None):
                self.turn_timer_event = Clock.schedule_interval(self._tick_turn_timer, 1.0)

    def on_quit(self):
        app = App.get_running_app()
        
        # =======================================================
        # 🟢 1. เช็คว่าเกมจบหรือยัง ถ้าจบแล้ว (สถานะ Skip Countdown) 
        # ให้ทำงานได้ทันทีโดยไม่ต้องสนใจว่าเป็นเทิร์นใคร
        # =======================================================
        if getattr(self.game, 'game_result', None):
            if hasattr(self, 'countdown_event') and self.countdown_event:
                self.countdown_event.cancel()
                self.countdown_event = None
            self.auto_quit_to_setup(0)
            return

        # =======================================================
        # 🔴 2. ป้องกันผู้เล่นกด Retreat แทนบอทในเทิร์นของ AI (เฉพาะตอนเกมยังเล่นอยู่)
        # =======================================================
        is_bot_turn = False
        game_mode = getattr(self, 'game_mode', 'PVP')
        match_type = getattr(app, 'match_type', 'PVE')
        
        if game_mode == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'white') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            current_faction = attacker_faction if self.game.current_turn == 'white' else defender_faction
            
            if match_type == 'PVE':
                player_involved = (attacker_faction == 'white' or defender_faction == 'white')
                if not player_involved:
                    is_bot_turn = True
                elif current_faction != 'white':
                    is_bot_turn = True
            elif match_type == 'LOCAL_PVP':
                if current_faction == 'red':
                    is_bot_turn = True
        else:
            if match_type == 'PVE' and self.game.current_turn == 'black':
                is_bot_turn = True

        if is_bot_turn:
            return  # ❌ ถ้าเป็นเทิร์นบอท ห้ามกด Retreat เด็ดขาด!
            
        # =======================================================
        # Bypass input locks so the player can retreat at any time
        # (หมายเหตุ: ลบบล็อกเช็ค game_result ตรงนี้ออกไปแล้วเพราะย้ายขึ้นบนสุด)

        if getattr(self, 'game_mode', '') == 'Divide_Conquer':
            target_node = getattr(app, 'combat_target', None)
            
            is_defender_turn = (self.game.current_turn == 'black')
            
            if is_defender_turn and target_node and getattr(target_node, 'is_main_base', False):
                self.info_label.text = "[color=ff0000]CANNOT RETREAT FROM MAIN BASE![/color]"
                return
            
            if getattr(self, 'battle_phase', '') == 'deployment_arrange_def' or (getattr(self, 'battle_phase', '') != 'playing' and is_defender_turn):
                return

            app.play_click_sound()
            if getattr(self, 'crash_popup', None): self.crash_popup.force_cancel()
            
            # Cancel both halves of the AI turn loop so no move fires after retreat.
            if getattr(self, 'ai_event', None): self.ai_event.cancel()
            Clock.unschedule(self.ai_controller._schedule_next_ai_turn)
            Clock.unschedule(self.ai_controller.trigger_ai_move)
            self.is_input_locked = False
            self.hide_item_tooltip()
            
            retreating_color = self.game.current_turn
            dead_count = 0
            for r in range(8):
                for c in range(8):
                    p = self.game.board[r][c]
                    if p and p.color == retreating_color and p.__class__.__name__.lower() == 'pawn':
                        if random.random() < 0.5: 
                            self.game.board[r][c] = None
                            dead_count += 1
                            
            self.game.game_result = "BLACK WINS" if retreating_color == 'white' else "WHITE WINS"
            
            def proceed_to_map(): self.auto_quit_to_setup(0)
            RetreatPopup(dead_count, proceed_to_map).open()
        else:
            self.auto_quit_to_setup(0)
            
    def auto_quit_to_setup(self, dt):
        self.hide_item_tooltip()
        self.selected_item = None
        if hasattr(self, 'countdown_event') and self.countdown_event:
            self.countdown_event.cancel()
            self.countdown_event = None
            
        if getattr(self, 'game_mode', '') == 'Divide_Conquer':
            app = App.get_running_app()
            app.battle_finished = True
            
            res_str = self.game.game_result.upper() if self.game.game_result else ""
            if "WHITE WINS" in res_str: app.battle_winner = 'attacker'
            elif "BLACK WINS" in res_str: app.battle_winner = 'defender'
            else: app.battle_winner = 'draw'
            
            surv_atk, surv_def = [], []
            for r in range(8):
                for c in range(8):
                    p = self.game.board[r][c]
                    if p:
                        if p.color == 'white': surv_atk.append(p)
                        elif p.color == 'black': surv_def.append(p)
                        
            app.survivors_atk = surv_atk
            app.survivors_def = surv_def
            
            self.deployment_manager.remove_layer()
            
            self.manager.current = 'campaign_map'
        else:
            self.manager.current = 'setup'

    def on_undo_click(self):
        App.get_running_app().play_click_sound()
        if getattr(self, 'crash_popup', None): return
        if self.controller.submit_undo(): self.selected = None; self.init_board_ui()
            
    def show_piece_status(self, piece):
        if self.crash_popup: return 
        self.info_zone.clear_widgets(); self.status_popup = UnitCard(piece, self.get_piece_image_path(piece))
        self.info_zone.add_widget(self.status_popup)
            
    def hide_piece_status(self):
        if not self.crash_popup: self.info_zone.clear_widgets(); self.status_popup = None
            
    def snap_piece_ui(self, attacker, start, end):
        """Visually teleport the attacker icon from start → end.

        NOTE: Do NOT call this on crash/capture moves.  move_piece() returns
        ("crash", ...) without touching the board array, meaning both pieces
        still exist in self.game.board.  If we overwrite the destination
        square here, the defender's icon disappears before the crash animation
        plays — which is exactly the bug we want to avoid.

        This helper is only appropriate for non-capture moves where you want
        an instant visual repositioning without a full init_board_ui() rebuild.
        """
        if not hasattr(self, 'squares'):
            return
        sq_start = self.squares.get(start)
        sq_end   = self.squares.get(end)
        if sq_start and sq_end:
            atk_path = self.get_piece_image_path(attacker)
            sq_end.set_piece_icon(atk_path, piece=attacker)
            sq_start.set_piece_icon(None, piece=None)

    def show_crash_overlay(self, attacker, defender, start, end):
        self.info_zone.clear_widgets() # เคลียร์ขยะเผื่อค้าง
        App.get_running_app().play_coin_sound()

        # Both piece icons are intentionally left untouched on the board.
        # move_piece() returned ("crash", ...) without modifying self.game.board,
        # so both attacker and defender are still visible at their original squares.
        # The crash overlay will reveal the outcome; only after execute_board_move()
        # calls init_board_ui() will the losing piece finally be removed from view.

        atk_tribe = getattr(attacker, 'tribe', self.get_tribe_name(attacker.color))
        def_tribe = getattr(defender, 'tribe', self.get_tribe_name(defender.color))
        
        self.crash_popup = CrashOverlay(
            attacker, defender, start, end, atk_tribe, def_tribe, 
            self.get_piece_image_path, self.execute_board_move, self.cancel_crash, 
            game_mode=getattr(self, 'game_mode', 'PVP')
        )
        # แก้ตรงนี้: นำไปใส่ใน root_layout เพื่อให้เต็มหน้าจอเกม
        self.root_layout.add_widget(self.crash_popup)
        
    def cancel_crash(self):
        # ลบหน้าต่างออกเมื่อ Crash จบ
        if self.crash_popup and self.crash_popup in self.root_layout.children:
            self.root_layout.remove_widget(self.crash_popup)
        self.crash_popup = None
        self.refresh_ui()
    def handle_card_hover(self, row, col, is_hovering):
        if hasattr(self, 'board_3d'):
            if is_hovering:
                # สั่งวาดสีม่วงที่กระดาน 3D ตรงพิกัด row, col
                self.board_3d.highlight_purple(row, col)
            else:
                # สั่งลบสีม่วง
                self.board_3d.clear_purple_highlight()

    def toggle_fast_forward(self, instance):
        """สลับสถานะโหมดเร่งความเร็ว AI"""
        self.fast_forward_ai = not self.fast_forward_ai
        if self.fast_forward_ai:
            instance.text = "FF: ON"
            instance.background_color = (0.8, 0.4, 0.1, 1) # เปลี่ยนเป็นสีส้มเมื่อเปิดใช้งาน
        else:
            instance.text = "FF: OFF"
            instance.background_color = (0.3, 0.3, 0.3, 0.8)