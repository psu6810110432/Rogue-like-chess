# screens/gameplay_screen.py
import random
from kivy.app import App
from kivy.graphics import Rectangle, Color, Line, RoundedRectangle
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

from logic.board import ChessBoard
from logic.ai_logic import ChessAI
from components.chess_square import ChessSquare
from components.sidebar_ui import SidebarUI
from components.unit_card import UnitCard
from components.item_tooltip import ItemTooltip
from components.crash_overlay import CrashOverlay
from logic.crash_logic import simulate_ai_crash_result
from components.inventory_ui import InventorySlot
from components.gameplay_popups import PromotionPopup, RetreatPopup

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

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        
        with self.root_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.main_bg_image = Rectangle(source='assets/ui/backgrounds/menu_bg.png', pos=self.pos, size=self.size)
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
        if hasattr(self, 'deployment_layer') and self.deployment_layer in self.root_layout.children:
            self.root_layout.remove_widget(self.deployment_layer)
        self.hide_item_tooltip()
        self.status_popup = self.crash_popup = self.item_tooltip = self.selected_item = None
        self.game_mode, self._game_over_scheduled, self.selected = mode, False, None
        self.is_input_locked = False 
        self.ai_event = None
        self.battle_phase = 'playing' 
        
        if hasattr(self, 'countdown_event') and self.countdown_event:
            self.countdown_event.cancel()
            self.countdown_event = None
        self.countdown_time = 0

        app = App.get_running_app()
        chosen_map = getattr(app, 'selected_board', 'Classic Board')
        if chosen_map == "Random Board": chosen_map = random.choice(['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra'])
        
        if chosen_map == 'Enchanted Forest' and ForestMap: self.game = ForestMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Desert Ruins' and DesertMap: self.game = DesertMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Frozen Tundra' and TundraMap: self.game = TundraMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        else: self.game = ChessBoard(self.get_tribe_name('white'), self.get_tribe_name('black'), map_name=chosen_map)
        
        if mode == 'Divide_Conquer':
            self.setup_divide_conquer_board(app)
            
        self.board_area = BoxLayout(orientation='vertical', size_hint_x=0.75)
        self.info_label = Label(text="WHITE'S TURN", size_hint_y=0.08, color=(0.83, 0.68, 0.21, 1), bold=True, font_size='22sp', markup=True)
        self.board_area.add_widget(self.info_label)
        self.play_area = BoxLayout(orientation='vertical', size_hint_y=0.92)
        self.board_anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.82)
        self.play_area.add_widget(self.board_anchor)
        self.inv_anchor = AnchorLayout(anchor_x='center', anchor_y='top', size_hint_y=0.18, padding=[0, dp(10), 0, dp(20)])
        self.inventory_layout = BoxLayout(orientation='horizontal', size_hint_x=0.85, spacing=dp(10), padding=dp(10))
        with self.inventory_layout.canvas.before:
            Color(0.05, 0.05, 0.07, 0.6); self.inv_bg = Rectangle(pos=self.inventory_layout.pos, size=self.inventory_layout.size)
        self.inventory_layout.bind(pos=self._update_inv_bg, size=self._update_inv_bg)
        self.inv_anchor.add_widget(self.inventory_layout)
        self.play_area.add_widget(self.inv_anchor); self.board_area.add_widget(self.play_area)
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
            if getattr(self, 'is_input_locked', False): return
            
            if getattr(self.game, 'game_result', None):
                if hasattr(self, 'countdown_event') and self.countdown_event:
                    self.countdown_event.cancel()
                    self.countdown_event = None
                self.auto_quit_to_setup(0)
                return

            if getattr(self, 'game_mode', '') == 'Divide_Conquer':
                App.get_running_app().play_click_sound()
                if getattr(self, 'crash_popup', None): self.crash_popup.force_cancel()
                if getattr(self, 'ai_event', None): self.ai_event.cancel()
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
                self.on_quit()
                
        self.sidebar = SidebarUI(on_undo_callback=self.on_undo_click, on_quit_callback=on_quit_action, game_mode=mode)
        self.sidebar.size_hint_y = 0.55; self.sidebar_panel.add_widget(self.sidebar); self.main_layout.add_widget(self.sidebar_panel)
        
        self.init_board_ui()
        if mode == 'Divide_Conquer':
            self.setup_deployment_ui()

    def setup_deployment_ui(self):
        if hasattr(self, 'deployment_layer') and self.deployment_layer:
            self.root_layout.remove_widget(self.deployment_layer)
            
        self.battle_phase = 'deployment_arrange'
        
        self.deployment_layer = FloatLayout()
        self.root_layout.add_widget(self.deployment_layer)
        
        if hasattr(self.sidebar, 'hide_buttons'):
            self.sidebar.hide_buttons()

        self.black_mask = Widget()
        with self.black_mask.canvas.before:
            Color(0, 0, 0, 1) 
            self.mask_rect = Rectangle()
            
        def update_mask(*args):
            if hasattr(self, 'grid') and self.grid:
                self.mask_rect.pos = (self.grid.x, self.grid.y + self.grid.height * 3 / 8)
                self.mask_rect.size = (self.grid.width, self.grid.height * 5 / 8)
                
        if hasattr(self, 'grid'):
            self.grid.bind(pos=update_mask, size=update_mask)
            update_mask()
            
        self.deployment_layer.add_widget(self.black_mask)
        
        self.deploy_lbl = Label(
            text="[b]PHASE 1: DEPLOYMENT[/b]\nArrange your units (Bottom 3 rows)", 
            markup=True, halign='center', pos_hint={'center_x': 0.5, 'center_y': 0.7}, 
            font_size='24sp', color=(1, 0.8, 0, 1)
        )
        self.deployment_layer.add_widget(self.deploy_lbl)
        
        self.deployment_btn_box = BoxLayout(
            orientation='horizontal', size_hint=(None, None), 
            size=(dp(400), dp(60)), pos_hint={'center_x': 0.5, 'y': 0.1}, spacing=dp(20)
        )
        
        btn_retreat = Button(text="[b]RETREAT[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1), font_size='18sp')
        btn_retreat.bind(on_release=self.deployment_retreat) 
        
        btn_confirm = Button(text="[b]CONFIRM SETUP[/b]", markup=True, background_color=(0.2, 0.6, 0.8, 1), font_size='18sp')
        btn_confirm.bind(on_release=self.show_reveal_phase)
        
        self.deployment_btn_box.add_widget(btn_retreat)
        self.deployment_btn_box.add_widget(btn_confirm)
        self.deployment_layer.add_widget(self.deployment_btn_box)
        
        self.refresh_ui()

    def deployment_retreat(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        
        app.battle_finished = True
        app.battle_winner = 'draw'
        app.survivors_atk = app.combat_marching_army
        app.survivors_def = app.combat_target_army
        
        self.manager.current = 'campaign_map'

    def show_reveal_phase(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        
        self.battle_phase = 'deployment_reveal'
        self.selected = None
        
        if hasattr(self.sidebar, 'show_buttons'):
            self.sidebar.show_buttons()

        if self.black_mask in self.deployment_layer.children:
            self.deployment_layer.remove_widget(self.black_mask)
            
        self.deploy_lbl.text = "[b]PHASE 2: ENEMY REVEALED[/b]\nObserve the enemy Commander's position!"
        self.deploy_lbl.color = (1, 0.4, 0.4, 1)
        
        self.deployment_btn_box.clear_widgets()
        btn_ready = Button(text="[b]READY TO BATTLE[/b]", markup=True, background_color=(0.2, 0.8, 0.2, 1), font_size='18sp')
        btn_ready.bind(on_release=self.start_battle_phase)
        self.deployment_btn_box.add_widget(btn_ready)
        
        self.refresh_ui()

    def start_battle_phase(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        
        self.battle_phase = 'playing'
        self.selected = None
        
        if hasattr(self, 'deployment_layer') and self.deployment_layer:
            self.root_layout.remove_widget(self.deployment_layer)
            self.deployment_layer = None
            
        self.refresh_ui()
        self.check_ai_turn()

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
        
        enemy_army_list = app.combat_target_army
        valid_coords = [(r, c) for r in range(3) for c in range(8)]
        random.shuffle(valid_coords)
        for p, (r, c) in zip(enemy_army_list, valid_coords):
            p.color = 'black'
            self.game.board[r][c] = p
            
        player_army_list = app.combat_marching_army
        coords = [(r, c) for r in range(7, 4, -1) for c in range(8)] 
        for p, (r, c) in zip(player_army_list, coords):
            p.color = 'white'
            self.game.board[r][c] = p
            
        self.game.current_turn = 'white'

    def _update_inv_bg(self, instance, value): self.inv_bg.pos, self.inv_bg.size = instance.pos, instance.size
    def _update_sb_bg(self, instance, value): self.sb_bg.pos, self.sb_bg.size = instance.pos, instance.size
    def _update_div_bg(self, instance, value): self.div_rect.pos, self.div_rect.size = instance.pos, instance.size
    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect') and hasattr(self, 'grid'):
            self.bg_rect.pos, self.bg_rect.size = self.grid.pos, self.grid.size

    def init_board_ui(self):
        self.board_anchor.clear_widgets()
        gm = getattr(self, 'game_mode', 'PVP')
        
        is_bot = False
        app = App.get_running_app()
        if gm == 'PVE' and self.game.current_turn == 'black': 
            is_bot = True
        elif gm == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'red') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            
            if self.game.current_turn == 'white' and attacker_faction == 'red':
                is_bot = True
            elif self.game.current_turn == 'black' and defender_faction == 'red':
                is_bot = True
                
        phase = getattr(self, 'battle_phase', 'playing')
        if phase == 'playing' and not is_bot:
            vp = self.game.current_turn
        else:
            vp = 'white'
            
        if hasattr(self, 'current_vp') and self.current_vp == vp and hasattr(self, 'grid') and self.grid in self.board_anchor.children:
            self.refresh_ui(); return
            
        self.current_vp = vp
        self.grid = GridLayout(cols=8, rows=8, size_hint=(None, None), spacing=0, padding=0)
        self.board_anchor.add_widget(self.grid); self.board_anchor.bind(size=self._keep_grid_square)
        if self.board_anchor.width > 0: self._keep_grid_square(self.board_anchor, self.board_anchor.size)
        
        if hasattr(self.game, 'bg_image') and self.game.bg_image != '':
            with self.grid.canvas.before:
                Color(1, 1, 1, 1); self.bg_rect = Rectangle(source=self.game.bg_image, pos=self.grid.pos, size=self.grid.size)
            self.grid.bind(pos=self._update_bg, size=self._update_bg)
            
        self.squares = {}
        for r in (range(8) if vp == 'white' else range(7, -1, -1)):
            for c in (range(8) if vp == 'white' else range(7, -1, -1)):
                sq = ChessSquare(row=r, col=c); sq.bind(on_release=self.on_square_tap)
                self.grid.add_widget(sq); self.squares[(r, c)] = sq
        self.refresh_ui()

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
        self.update_inventory_ui()
        
        phase = getattr(self, 'battle_phase', 'playing')
        
        if phase == 'deployment_arrange':
            self.info_label.text = "[color=00ffff]PHASE 1: Arrange your units (Bottom 3 rows)[/color]"
            for (r, c), sq in self.squares.items():
                is_deploy_zone = (r >= 5)
                is_legal_deploy = (is_deploy_zone and self.selected is not None and (r, c) != self.selected)
                sq.update_square_style(highlight=(self.selected == (r, c)), is_legal=('move' if is_legal_deploy else False), is_check=False, is_last=False)
                
                p = self.game.board[r][c]
                if not is_deploy_zone:
                    sq.set_piece_icon(None, piece=None)
                else:
                    sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
            return
            
        elif phase == 'deployment_reveal':
            self.info_label.text = "[color=ffaa00]PHASE 2: Enemy Revealed! Observe their position.[/color]"
            
            enemy_header_pos = None
            for r in range(8):
                for c in range(8):
                    p = self.game.board[r][c]
                    if p and p.color == 'black':
                        if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False):
                            enemy_header_pos = (r, c)
                            break
                if enemy_header_pos: break

            for (r, c), sq in self.squares.items():
                is_king = ((r, c) == enemy_header_pos)
                sq.update_square_style(highlight=False, is_legal=False, is_check=is_king, is_last=False)
                p = self.game.board[r][c]
                sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
            return

        if self.game.game_result:
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
        else: 
            self.info_label.text = f"{self.game.current_turn.upper()}'S TURN"
            self._end_played = False 

        cp = self.game.find_king(self.game.current_turn) if self.game.is_in_check(self.game.current_turn) else None
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
            p = self.game.board[r][c]; sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
        self.sidebar.update_history_text(self.game.history.move_text_history)
        
        if getattr(self, 'battle_phase', 'playing') == 'playing':
            self.highlight_headers()

    def show_item_tooltip(self, item):
        self.hide_item_tooltip(); self.item_tooltip = ItemTooltip(item); self.root_layout.add_widget(self.item_tooltip)
        
    def hide_item_tooltip(self):
        if self.item_tooltip: self.root_layout.remove_widget(self.item_tooltip); self.item_tooltip = None

    def get_piece_image_path(self, piece):
        if not piece: return None
        p_c, p_n = piece.color, piece.__class__.__name__.lower()
        if p_n == 'obstacle':
            ot = piece.name.lower(); return f"assets/pieces/event/event{'1' if ot=='thorn' else '2' if ot=='sandstorm' else '3'}.png"
            
        tf = getattr(piece, 'tribe', 'the knight company')
        
        stage_folder = "1base"
        lvl = getattr(piece, 'upgrade_level', 0)
        path = getattr(piece, 'upgrade_path', 'standard')
        
        if lvl > 0:
            if path == 'standard':
                stage_folder = "2upATK" if lvl == 1 else "3upDEF"
            elif path == 'special':
                stage_folder = "4up_rehidden" if lvl == 1 else "5up_reroll_ATK_DEF"
                
        if p_n in ['pawn', 'hastati', 'levies']:
            num = getattr(piece, 'variant', 1) 
            filename = f"{p_n}{num}.png"
        else:
            filename = f"{p_n}.png"
            
        return f"assets/pieces/{tf}/{p_c}/{stage_folder}/{filename}"

    def on_square_tap(self, instance):
        App.get_running_app().play_click_sound()
        r, c = instance.row, instance.col
        
        phase = getattr(self, 'battle_phase', 'playing')
        
        if phase == 'deployment_arrange':
            if r < 5: return 
            
            if self.selected is None:
                piece = self.game.board[r][c]
                if piece and piece.color == self.game.current_turn:
                    self.selected = (r, c); self.refresh_ui()
            else:
                sr, sc = self.selected
                if (r, c) == (sr, sc): self.selected = None; self.refresh_ui(); return
                
                target_piece = self.game.board[r][c]
                if not target_piece or target_piece.color == self.game.current_turn:
                    self.game.board[r][c] = self.game.board[sr][sc]
                    self.game.board[sr][sc] = target_piece
                    self.selected = None; self.init_board_ui()
            return
            
        elif phase == 'deployment_reveal':
            return 
            
        if getattr(self, 'is_input_locked', False): return 
        if getattr(self, 'crash_popup', None): return
        
        piece = self.game.board[r][c]
        
        if getattr(self.game, 'game_result', None): 
            if not self.selected_item: return
            
        if getattr(self.game, 'game_mode', 'PVP') in ['PVE', 'Divide_Conquer'] and getattr(self.game, 'current_turn', 'white') == 'black' and not getattr(self.game, 'game_result', None): 
            return
        
        if self.selected_item:
            if piece and piece.color == self.game.current_turn:
                if getattr(piece, 'item', None) is not None:
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                if self.selected_item.id == 9 and piece.__class__.__name__.lower() == 'knight':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                if self.selected_item.id == 10 and piece.__class__.__name__.lower() != 'pawn':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                    
                piece.item = self.selected_item
                if piece.item.id == 6: piece.coins += 1; piece.base_points = max(0, piece.base_points - 1)
                elif piece.item.id == 10 and piece.__class__.__name__.lower() == 'pawn': piece.base_points, piece.coins = 5, 3
                    
                inv = getattr(self.game, f'inventory_{self.game.current_turn}')
                if self.selected_item in inv: inv.remove(self.selected_item)
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
                    
            res = self.game.move_piece(sr, sc, r, c)
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
                    self.game.promote_pawn(r, c, cls)
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
            atk, df = self.game.board[start_pos[0]][start_pos[1]], self.game.board[end_pos[0]][end_pos[1]]
            if df: df.item = None
            if atk: atk.has_moved = True
            self.game.en_passant_target = None
            self.game.history.save_state(self.game, "Shield Blocked!"); self.game.complete_turn(); self.init_board_ui()
            self.trigger_end_turn_logic(atk.color)
            return
            
        res = self.game.move_piece(start_pos[0], start_pos[1], end_pos[0], end_pos[1], resolve_crash=True, crash_won=crash_status)
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
                self.game.promote_pawn(end_pos[0], end_pos[1], Queen)
                self.init_board_ui(); self.trigger_end_turn_logic(old_color)
            else:
                def do_p(cls): 
                    self.game.promote_pawn(end_pos[0], end_pos[1], cls); pop.dismiss(); self.init_board_ui(); self.trigger_end_turn_logic(old_color)
                pop = PromotionPopup(pcolor, ptribe, do_p, is_prince=is_prince)
                pop.open()
        elif res in [True, "died", "survived", "defender_survived"]: 
            self.selected = None; self.init_board_ui(); self.trigger_end_turn_logic(old_color)
        else: 
            self.selected = None; self.refresh_ui(); self.trigger_end_turn_logic(old_color)

    def update_inventory_ui(self):
        self.inventory_layout.clear_widgets()
        info_box = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(120))
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

    def on_item_click(self, item):
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
                    
        self.check_ai_turn()

    def check_ai_turn(self):
        app = App.get_running_app()
        is_bot_turn = False
        
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black': 
            is_bot_turn = True
        elif getattr(self, 'game_mode', 'PVP') == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'red') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            
            if self.game.current_turn == 'white' and attacker_faction == 'red':
                is_bot_turn = True
            elif self.game.current_turn == 'black' and defender_faction == 'red':
                is_bot_turn = True
                
        if is_bot_turn and not self.game.game_result: 
            self.is_input_locked = True 
            self.ai_event = Clock.schedule_once(self.trigger_ai_move, 0.8)
        else:
            self.is_input_locked = False 

    def trigger_ai_move(self, dt):
        if self.game.game_result: return
        
        difficulty = getattr(App.get_running_app(), 'ai_difficulty', 'normal')
        ai_color = self.game.current_turn
        
        if getattr(self, 'game_mode', 'PVP') == 'Divide_Conquer':
            from logic.dac_ai import DACBot
            
            target_piece, item_to_use = DACBot.decide_item_usage(self.game, ai_color, difficulty)
            if target_piece and item_to_use:
                target_piece.item = item_to_use
                if item_to_use.id == 6: 
                    target_piece.coins += 1
                    target_piece.base_points = max(0, target_piece.base_points - 1)
                elif item_to_use.id == 10 and target_piece.__class__.__name__.lower() == 'pawn': 
                    target_piece.base_points = 5
                    target_piece.coins = 3
                    
                getattr(self.game, f'inventory_{ai_color}').remove(item_to_use)
                App.get_running_app().play_click_sound()
                self.init_board_ui()
                self.update_inventory_ui()
            move = DACBot.get_best_move(self.game, ai_color)
            
        else:
            from logic.ai_logic import ChessAI
            
            inv = getattr(self.game, f'inventory_{ai_color}', [])
            if inv:
                import random
                use_chance = 0.6 if difficulty == 'hard' else 0.4 if difficulty == 'normal' else 0.25
                if len(inv) >= 5 or random.random() < use_chance:
                    item_to_use = random.choice(inv)
                    valid_pieces = [p for row in self.game.board for p in row if p and p.color == ai_color and getattr(p, 'item', None) is None]
                    if valid_pieces:
                        chosen_piece = random.choice(valid_pieces)
                        chosen_piece.item = item_to_use
                        if item_to_use.id == 6: 
                            chosen_piece.coins += 1; chosen_piece.base_points = max(0, chosen_piece.base_points - 1)
                        elif item_to_use.id == 10 and chosen_piece.__class__.__name__.lower() == 'pawn': 
                            chosen_piece.base_points, chosen_piece.coins = 5, 3
                            
                        inv.remove(item_to_use)
                        App.get_running_app().play_click_sound()
                        self.init_board_ui()
                        self.update_inventory_ui()
            move = ChessAI.get_best_move(self.game, ai_color=ai_color)
            
        if move:
            (sr, sc), (er, ec) = move
            res = self.game.move_piece(sr, sc, er, ec)
            
            if isinstance(res, tuple) and res[0] == "crash":
                atk, df = res[1], res[2]
                if not atk or not df: return
                if getattr(df, 'item', None) and df.item.id == 4:
                    df.item = None
                    atk.has_moved = True
                    self.game.history.save_state(self.game, "Shield Blocked!")
                    self.game.complete_turn()
                    self.init_board_ui()
                    return 
                self.show_crash_overlay(atk, df, (sr, sc), (er, ec))
                return
                
            if res == "promote":
                from logic.pieces import Queen
                self.game.promote_pawn(er, ec, Queen)
                
            if res in [True, "promote", "died"]: 
                App.get_running_app().play_move_sound()
            self.init_board_ui()
            
        self.ai_event = None
        self.check_ai_turn()

    def on_quit(self):
        App.get_running_app().play_click_sound()
        self.hide_item_tooltip()
        self.selected_item = None
        if hasattr(self, 'countdown_event') and self.countdown_event:
            self.countdown_event.cancel()
            self.countdown_event = None
        if getattr(self, 'crash_popup', None): self.crash_popup.force_cancel(); self.crash_popup = None
        if getattr(self, 'ai_event', None): self.ai_event.cancel()
        self.status_popup = self.item_tooltip = self.selected_item = None
        self.is_input_locked = False
        if getattr(self, 'game_mode', '') == 'Divide_Conquer':
            self.manager.current = 'campaign_map'
        else:
            self.manager.current = 'setup'
            
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
            self.manager.current = 'campaign_map'
        else:
            self.manager.current = 'setup'

    def on_undo_click(self):
        App.get_running_app().play_click_sound()
        if getattr(self, 'crash_popup', None): return
        if self.game.undo_move(): self.selected = None; self.init_board_ui()
            
    def show_piece_status(self, piece):
        if self.crash_popup: return 
        self.info_zone.clear_widgets(); self.status_popup = UnitCard(piece, self.get_piece_image_path(piece))
        self.info_zone.add_widget(self.status_popup)
            
    def hide_piece_status(self):
        if not self.crash_popup: self.info_zone.clear_widgets(); self.status_popup = None
            
    def show_crash_overlay(self, attacker, defender, start, end):
        self.info_zone.clear_widgets()
        App.get_running_app().play_coin_sound()
        atk_tribe = getattr(attacker, 'tribe', self.get_tribe_name(attacker.color))
        def_tribe = getattr(defender, 'tribe', self.get_tribe_name(defender.color))
        
        self.crash_popup = CrashOverlay(
            attacker, defender, start, end, atk_tribe, def_tribe, 
            self.get_piece_image_path, self.execute_board_move, self.cancel_crash, 
            game_mode=getattr(self, 'game_mode', 'PVP')
        )
        self.info_zone.add_widget(self.crash_popup)
            
    def cancel_crash(self): self.info_zone.clear_widgets(); self.crash_popup = None; self.refresh_ui()