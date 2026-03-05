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
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

from logic.board import ChessBoard
from logic.ai_logic import ChessAI
from components.chess_square import ChessSquare
from components.sidebar_ui import SidebarUI
from components.unit_card import UnitCard
from components.item_tooltip import ItemTooltip
from components.crash_overlay import CrashOverlay
from logic.crash_logic import simulate_ai_crash_result

try: from logic.maps.forest_map import ForestMap
except ImportError: ForestMap = None
try: from logic.maps.desert_map import DesertMap
except ImportError: DesertMap = None
try: from logic.maps.tundra_map import TundraMap
except ImportError: TundraMap = None

class InventorySlot(ButtonBehavior, BoxLayout):
    def __init__(self, img_path='', is_selected=False, **kwargs):
        super().__init__(padding=dp(5), **kwargs)
        with self.canvas.before:
            self.bg_color = Color(0.15, 0.2, 0.15, 0.85) if is_selected else Color(0.1, 0.1, 0.12, 0.7)
            self.bg_rect = RoundedRectangle(radius=[10])
            self.border_color = Color(0.83, 0.68, 0.21, 1) if is_selected else Color(0.3, 0.3, 0.35, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 10], width=2.0 if is_selected else 1.2)
            
        self.bind(pos=self._update_bg, size=self._update_bg)
        if img_path: self.add_widget(Image(source=img_path, allow_stretch=True, keep_ratio=True))
        
    def _update_bg(self, instance, value):
        self.bg_rect.pos, self.bg_rect.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, 10]

class PromotionPopup(ModalView):
    def __init__(self, color, callback, **kwargs):
        super().__init__(size_hint=(0.6, 0.2), auto_dismiss=False, **kwargs)
        layout = GridLayout(cols=4, padding=10, spacing=10)
        from logic.pieces import Queen, Rook, Bishop, Knight
        ops, names = [Queen, Rook, Bishop, Knight], ['queen', 'rook', 'bishop', 'knight']
        theme = getattr(App.get_running_app(), f'selected_unit_{color}', 'Medieval Knights')
        for cls, n in zip(ops, names):
            tf = "ayothaya" if theme=="Ayothaya" else "demon" if theme=="Demon" else "heaven" if theme=="Heaven" else "medieval"
            mapping = {'queen': '2', 'rook': '3', 'knight': '4', 'bishop': '5'}
            path = f"assets/pieces/{tf}/{color}/chess {tf}{mapping[n]}.png"
            btn = Button(background_normal=path)
            btn.bind(on_release=lambda b, c=cls: (App.get_running_app().play_click_sound(), callback(c)))
            layout.add_widget(btn)
        self.add_widget(layout)

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

    def _update_main_bg(self, *args):
        self.main_bg_image.pos = self.pos
        self.main_bg_image.size = self.size
        self.main_bg_overlay.pos = self.pos
        self.main_bg_overlay.size = self.size

    def get_tribe_name(self, color):
        theme = getattr(App.get_running_app(), f'selected_unit_{color}', 'Medieval Knights')
        return theme.lower().replace(" ", "") if theme != "Medieval Knights" else "medieval"

    def setup_game(self, mode):
        self.main_layout.clear_widgets()
        self.game_mode, self._game_over_scheduled, self.selected = mode, False, None
        app = App.get_running_app()
        chosen_map = getattr(app, 'selected_board', 'Classic Board')
        if chosen_map == "Random Board": chosen_map = random.choice(['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra'])
        
        if chosen_map == 'Enchanted Forest' and ForestMap: 
            self.game = ForestMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Desert Ruins' and DesertMap: 
            self.game = DesertMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        elif chosen_map == 'Frozen Tundra' and TundraMap: 
            self.game = TundraMap(self.get_tribe_name('white'), self.get_tribe_name('black'))
        else: 
            self.game = ChessBoard(self.get_tribe_name('white'), self.get_tribe_name('black'), map_name=chosen_map)

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
        self.sidebar = SidebarUI(on_undo_callback=self.on_undo_click, on_quit_callback=self.on_quit)
        self.sidebar.size_hint_y = 0.55; self.sidebar_panel.add_widget(self.sidebar); self.main_layout.add_widget(self.sidebar_panel)
        self.init_board_ui()

    def _update_inv_bg(self, instance, value): self.inv_bg.pos, self.inv_bg.size = instance.pos, instance.size
    def _update_sb_bg(self, instance, value): self.sb_bg.pos, self.sb_bg.size = instance.pos, instance.size
    def _update_div_bg(self, instance, value): self.div_rect.pos, self.div_rect.size = instance.pos, instance.size

    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect') and hasattr(self, 'grid'):
            self.bg_rect.pos, self.bg_rect.size = self.grid.pos, self.grid.size

    def init_board_ui(self):
        self.board_anchor.clear_widgets()
        gm = getattr(self, 'game_mode', 'PVP')
        vp = 'white' if gm in ['TUTORIAL', 'PVE'] else self.game.current_turn
        
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

    def refresh_ui(self, legal_moves=[]):
        self.update_inventory_ui()
        if self.game.game_result:
            self.info_label.text = f"[color=ff3333][b]{self.game.game_result}[/b][/color]"
            if not getattr(self, '_end_played', False):
                if "WHITE WINS" in self.game.game_result.upper() and getattr(self, 'game_mode', 'PVP') == 'PVE':
                    App.get_running_app().play_victory_sound()
                elif "BLACK WINS" in self.game.game_result.upper() and getattr(self, 'game_mode', 'PVP') == 'PVE':
                    App.get_running_app().play_lose_sound()
                self._end_played = True

            if not self._game_over_scheduled: 
                self._game_over_scheduled = True
                Clock.schedule_once(self.auto_quit_to_setup, 2.5)
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

    def show_item_tooltip(self, item):
        self.hide_item_tooltip(); self.item_tooltip = ItemTooltip(item); self.root_layout.add_widget(self.item_tooltip)
    def hide_item_tooltip(self):
        if self.item_tooltip: self.root_layout.remove_widget(self.item_tooltip); self.item_tooltip = None

    def get_piece_image_path(self, piece):
        if not piece: return None
        p_c, p_n = piece.color, piece.__class__.__name__.lower()
        if p_n == 'obstacle':
            ot = piece.name.lower(); return f"assets/pieces/event/event{'1' if ot=='thorn' else '2' if ot=='sandstorm' else '3'}.png"
        theme = getattr(App.get_running_app(), f'selected_unit_{p_c}', 'Medieval Knights')
        tf = "ayothaya" if theme=="Ayothaya" else "demon" if theme=="Demon" else "heaven" if theme=="Heaven" else "medieval"
        num = getattr(piece, 'variant', 6) if p_n == 'pawn' else {'king': 1, 'queen': 2, 'rook': 3, 'knight': 4, 'bishop': 5}.get(p_n, 1)
        return f"assets/pieces/{tf}/{p_c}/chess {tf}{num}.png"

    def on_square_tap(self, instance):
        App.get_running_app().play_click_sound() 
        
        if getattr(self, 'crash_popup', None): return
        if self.game.game_result: return
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black': return
        
        r, c = instance.row, instance.col; piece = self.game.board[r][c]
        
        # ✨ 🚫 ระบบไอเทมล็อก (Item Slot Lock)
        if self.selected_item:
            if piece and piece.color == self.game.current_turn:
                # ตรวจสอบว่าหมากมีไอเทมอยู่แล้วหรือไม่
                if getattr(piece, 'item', None) is not None:
                    # ถ้ามีไอเทมอยู่แล้ว ห้ามใส่ทับ (ยกเลิกการเลือก)
                    self.selected_item = None
                    self.hide_item_tooltip()
                    self.refresh_ui()
                    return

                if self.selected_item.id == 9 and piece.__class__.__name__.lower() == 'knight':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                if self.selected_item.id == 10 and piece.__class__.__name__.lower() != 'pawn':
                    self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); return
                
                piece.item = self.selected_item
                if piece.item.id == 6: 
                    piece.coins += 1; piece.base_points = max(0, piece.base_points - 1)
                elif piece.item.id == 10 and piece.__class__.__name__.lower() == 'pawn': 
                    piece.base_points, piece.coins = 5, 3
                    
                inv = getattr(self.game, f'inventory_{self.game.current_turn}')
                if self.selected_item in inv: inv.remove(self.selected_item)
                self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui(); self.show_piece_status(piece)
            else: self.selected_item = None; self.hide_item_tooltip(); self.refresh_ui()
            return
            
        if self.selected is None:
            if piece and piece.color == self.game.current_turn:
                self.selected = (r, c); self.refresh_ui(self.game.get_legal_moves((r, c))); self.show_piece_status(piece)
        else:
            sr, sc = self.selected
            if sr == r and sc == c:
                self.selected = None; self.hide_piece_status(); self.refresh_ui(); return
                
            res = self.game.move_piece(sr, sc, r, c)
            if isinstance(res, tuple) and res[0] == "crash": self.show_crash_overlay(res[1], res[2], (sr, sc), (r, c)); return
            
            if res in [True, "promote", "died"]: App.get_running_app().play_move_sound()

            if res == "promote":
                self.hide_piece_status()
                def do_p(cls): 
                    self.game.promote_pawn(r, c, cls); pop.dismiss(); self.init_board_ui(); self.check_ai_turn()
                pop = PromotionPopup(self.game.board[r][c].color, do_p); pop.open()
            elif res in [True, "died"]: 
                self.selected = None; self.hide_piece_status(); self.init_board_ui(); self.check_ai_turn()
            else: 
                self.selected = None; self.hide_piece_status(); self.refresh_ui()

    def execute_board_move(self, start_pos, end_pos, crash_status):
        self.cancel_crash()
        if crash_status in ["won", "died"]: App.get_running_app().play_crash_win_sound()
        elif crash_status == "draw": App.get_running_app().play_draw_sound()

        if crash_status == "blocked":
            atk, df = self.game.board[start_pos[0]][start_pos[1]], self.game.board[end_pos[0]][end_pos[1]]
            if df: df.item = None
            if atk: atk.has_moved = True
            self.game.history.save_state(self.game, "Shield Blocked!"); self.game.complete_turn(); self.init_board_ui(); self.check_ai_turn()
            return
            
        res = self.game.move_piece(start_pos[0], start_pos[1], end_pos[0], end_pos[1], resolve_crash=True, crash_won=crash_status)
        if res in [True, "promote", "died"]: App.get_running_app().play_move_sound()

        if res == "promote":
            def do_p(cls): 
                self.game.promote_pawn(end_pos[0], end_pos[1], cls); pop.dismiss(); self.init_board_ui(); self.check_ai_turn()
            pop = PromotionPopup(self.game.board[end_pos[0]][end_pos[1]].color, do_p); pop.open()
        elif res in [True, "died", "survived", "defender_survived"]: 
            self.selected = None; self.init_board_ui(); self.check_ai_turn()
        else: 
            self.selected = None; self.refresh_ui(); self.check_ai_turn()

    def update_inventory_ui(self):
        self.inventory_layout.clear_widgets()
        info_box = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(120))
        info_box.add_widget(Label(text="INVENTORY", bold=True, font_size='14sp', color=(0.8, 0.8, 0.8, 1)))
        info_box.add_widget(Label(text=f"[{self.game.current_turn.upper()}]", bold=True, font_size='16sp', color=(0.83, 0.68, 0.21, 1)))
        self.inventory_layout.add_widget(info_box)
        inv = getattr(self.game, f'inventory_{self.game.current_turn}', [])
        for i in range(5):
            if i < len(inv):
                slot = InventorySlot(img_path=inv[i].image_path, is_selected=(self.selected_item and self.selected_item is inv[i]))
                slot.bind(on_release=lambda x, it=inv[i]: self.on_item_click(it)); self.inventory_layout.add_widget(slot)
            else: self.inventory_layout.add_widget(InventorySlot())

    def on_item_click(self, item):
        App.get_running_app().play_click_sound()
        if getattr(self, 'crash_popup', None): return
            
        if self.selected_item is item: self.selected_item = None; self.hide_item_tooltip()
        else: self.selected_item = item; self.show_item_tooltip(item)
        self.update_inventory_ui() 

    def check_ai_turn(self):
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black' and not self.game.game_result: 
            Clock.schedule_once(self.trigger_ai_move, 0.8)

    def trigger_ai_move(self, dt):
        move = ChessAI.get_best_move(self.game, ai_color='black')
        if move:
            (sr, sc), (er, ec) = move; res = self.game.move_piece(sr, sc, er, ec)
            if isinstance(res, tuple) and res[0] == "crash":
                atk, df = res[1], res[2]
                if not atk or not df: return
                
                if getattr(df, 'item', None) and df.item.id == 4:
                    df.item = None; atk.has_moved = True; self.game.history.save_state(self.game, "Shield Blocked!"); self.game.complete_turn(); self.init_board_ui(); return 
                
                r = simulate_ai_crash_result(atk, df, self.get_tribe_name(atk.color), self.get_tribe_name(df.color))
                res = self.game.move_piece(sr, sc, er, ec, resolve_crash=True, crash_won=r)
                
                if r in ["win", "died"]: App.get_running_app().play_crash_win_sound()
                elif r == "draw": App.get_running_app().play_draw_sound()
                
            if res == "promote":
                from logic.pieces import Queen; self.game.promote_pawn(er, ec, Queen)
                
            if res in [True, "promote", "died"]: App.get_running_app().play_move_sound()
            self.init_board_ui()

    def on_quit(self): 
        App.get_running_app().play_click_sound()
        self.manager.current = 'setup'
        
    def auto_quit_to_setup(self, dt): self.manager.current = 'setup'
    
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
        self.crash_popup = CrashOverlay(attacker, defender, start, end, self.get_tribe_name(attacker.color), self.get_tribe_name(defender.color), self.get_piece_image_path, self.execute_board_move, self.cancel_crash)
        self.info_zone.add_widget(self.crash_popup)
        
    def cancel_crash(self): self.info_zone.clear_widgets(); self.crash_popup = None; self.refresh_ui()