# screens/gameplay_screen.py
import random # ✨ เพิ่มนำเข้า random
from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout

from logic.board import ChessBoard
from logic.ai_logic import ChessAI
from components.chess_square import ChessSquare
from components.sidebar_ui import SidebarUI

# นำเข้า Components ที่แยกออกมา
from components.unit_card import UnitCard
from components.item_tooltip import ItemTooltip
from components.crash_overlay import CrashOverlay
from logic.crash_logic import simulate_ai_crash_result

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

class PromotionPopup(ModalView):
    def __init__(self, color, callback, **kwargs):
        super().__init__(size_hint=(0.6, 0.2), auto_dismiss=False, **kwargs)
        layout = GridLayout(cols=4, padding=10, spacing=10)
        from logic.pieces import Queen, Rook, Bishop, Knight
        ops = [Queen, Rook, Bishop, Knight]
        names = ['queen', 'rook', 'bishop', 'knight']
        
        app = App.get_running_app()
        if color == 'white':
            theme = getattr(app, 'selected_unit_white', 'Medieval Knights')
        else:
            theme = getattr(app, 'selected_unit_black', 'Demon')
        
        for cls, n in zip(ops, names):
            if theme == "Ayothaya":
                mapping = {'queen': 'chess ayothaya2.png', 'rook': 'chess ayothaya3.png', 'bishop': 'chess ayothaya5.png', 'knight': 'chess ayothaya4.png'}
                path = f"assets/pieces/ayothaya/{color}/{mapping[n]}"
            elif theme == "Demon":
                mapping = {'queen': 'chess demon2.png', 'rook': 'chess demon3.png', 'bishop': 'chess demon5.png', 'knight': 'chess demon4.png'}
                path = f"assets/pieces/demon/{color}/{mapping[n]}"
            elif theme == "Heaven":
                mapping = {'queen': 'chess heaven2.png', 'rook': 'chess heaven3.png', 'bishop': 'chess heaven5.png', 'knight': 'chess heaven4.png'}
                path = f"assets/pieces/heaven/{color}/{mapping[n]}"
            else:
                mapping = {'queen': 'chess medieval2.png', 'rook': 'chess medieval3.png', 'bishop': 'chess medieval5.png', 'knight': 'chess medieval4.png'}
                path = f"assets/pieces/medieval/{color}/{mapping[n]}"

            btn = Button(background_normal=path)
            btn.bind(on_release=lambda b, c=cls: callback(c))
            layout.add_widget(btn)
        self.add_widget(layout)

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.main_layout = BoxLayout(orientation='horizontal')
        self.root_layout.add_widget(self.main_layout)
        self.add_widget(self.root_layout)
        self.status_popup = None
        self.crash_popup = None 
        self.item_tooltip = None
        self.selected_item = None

    def get_tribe_name(self, color):
        app = App.get_running_app()
        theme = getattr(app, f'selected_unit_{color}', 'Medieval Knights')
        if theme == "Ayothaya": return "ayothaya"
        elif theme == "Demon": return "demon"
        elif theme == "Heaven": return "heaven"
        else: return "medieval"

    def setup_game(self, mode):
        self.main_layout.clear_widgets()
        self.game_mode = mode
        app = App.get_running_app()
        
        # ✨ รับชื่อด่านที่เลือกมาจากตัวแปรส่วนกลาง
        chosen_map = getattr(app, 'selected_board', 'Classic Board')
        
        # 🎲 Logic การสุ่มด่าน: ถ้าเลือก Random Board ให้สุ่มด่านจริงๆ ขึ้นมาแทน
        if chosen_map == "Random Board":
            actual_maps = ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra']
            chosen_map = random.choice(actual_maps)
            print(f"DEBUG: Randomly selected map -> {chosen_map}")

        # ตรวจสอบและเลือกด่าน (ถ้ามีไฟล์คลาสเฉพาะ)
        if chosen_map == 'Enchanted Forest' and ForestMap is not None: self.game = ForestMap()
        elif chosen_map == 'Desert Ruins' and DesertMap is not None: self.game = DesertMap()
        elif chosen_map == 'Frozen Tundra' and TundraMap is not None: self.game = TundraMap()
        else:
            white_tribe = self.get_tribe_name('white')
            black_tribe = self.get_tribe_name('black')
            # ✨ ส่งค่า chosen_map เข้าไปใน ChessBoard เพื่อเปลี่ยนรูปพื้นหลัง
            self.game = ChessBoard(white_tribe, black_tribe, map_name=chosen_map)
            
        self.selected = None
        self.board_area = BoxLayout(orientation='vertical', size_hint_x=0.75)
        self.info_label = Label(text="WHITE'S TURN", size_hint_y=0.1, color=(0.9, 0.8, 0.5, 1), bold=True, font_size='20sp', markup=True)        
        self.board_area.add_widget(self.info_label)
        
        self.container = BoxLayout(orientation='horizontal')
        self.board_area.add_widget(self.container)
        self.inventory_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, padding=[10, 5, 10, 5], spacing=10)
        self.board_area.add_widget(self.inventory_layout)
        self.main_layout.add_widget(self.board_area)

        self.sidebar = SidebarUI(on_undo_callback=self.on_undo_click, on_quit_callback=self.on_quit)
        self.main_layout.add_widget(self.sidebar)
        self.init_board_ui()

    def get_piece_image_path(self, piece):
        app = App.get_running_app()
        p_color = piece.color
        p_name = piece.__class__.__name__.lower()

        if p_name == 'obstacle':
            obstacle_type = piece.name.lower()
            if obstacle_type == 'thorn': return "assets/pieces/event/event1.png"      
            elif obstacle_type == 'sandstorm': return "assets/pieces/event/event2.png"      
            else: return "assets/pieces/event/event3.png"      
                
        if p_color == 'white': theme = getattr(app, 'selected_unit_white', 'Medieval Knights')
        else: theme = getattr(app, 'selected_unit_black', 'Demon')
        
        if theme == "Ayothaya": theme_folder = "ayothaya"
        elif theme == "Demon": theme_folder = "demon"
        elif theme == "Heaven": theme_folder = "heaven"
        else: theme_folder = "medieval"

        if p_name == 'pawn':
            num = getattr(piece, 'variant', 6)
        else:
            piece_map = {'king': 1, 'queen': 2, 'rook': 3, 'knight': 4, 'bishop': 5}
            num = piece_map.get(p_name, 1)

        return f"assets/pieces/{theme_folder}/{p_color}/chess {theme_folder}{num}.png"

    def on_quit(self):
        self.manager.current = 'setup'

    def init_board_ui(self):
        self.container.clear_widgets()

        view_perspective = 'white' if getattr(self, 'game_mode', 'PVP') == 'PVE' else self.game.current_turn

        ranks = GridLayout(cols=1, size_hint_x=0.05)
        rank_order = range(8, 0, -1) if view_perspective == 'white' else range(1, 9)
        for i in rank_order:
            ranks.add_widget(Label(text=str(i), color=(0.8, 0.7, 0.4, 1), bold=True))
        self.container.add_widget(ranks)
        
        self.board_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        self.grid = GridLayout(cols=8, rows=8, size_hint=(None, None))
        self.board_anchor.add_widget(self.grid)
        self.container.add_widget(self.board_anchor)
        
        self.board_anchor.bind(size=self._keep_grid_square)

        if hasattr(self.game, 'bg_image') and self.game.bg_image != '':
            with self.grid.canvas.before:
                Color(1, 1, 1, 1)
                self.bg_rect = Rectangle(source=self.game.bg_image, pos=self.grid.pos, size=self.grid.size)
            self.grid.bind(pos=self._update_bg, size=self._update_bg)

        self.squares = {}
        row_order = range(8) if view_perspective == 'white' else range(7, -1, -1)
        col_order = range(8) if view_perspective == 'white' else range(7, -1, -1)
        for r in row_order:
            for c in col_order:
                sq = ChessSquare(row=r, col=c)
                sq.bind(on_release=self.on_square_tap)
                self.grid.add_widget(sq)
                self.squares[(r, c)] = sq
        self.refresh_ui()

    def _keep_grid_square(self, instance, value):
        stretch_ratio = 1.0
        h = instance.height
        w = h * stretch_ratio
        if w > instance.width:
            w = instance.width
            h = w / stretch_ratio
        self.grid.size = (int(w), int(h))

    def _update_bg(self, instance, value):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size

    def refresh_ui(self, legal_moves=[]):
        self.update_inventory_ui()
        if self.game.game_result: self.info_label.text = self.game.game_result
        else: self.info_label.text = f"{self.game.current_turn.upper()}'S TURN"
        
        check_pos = self.game.find_king(self.game.current_turn) if self.game.is_in_check(self.game.current_turn) else None
        for (r, c), sq in self.squares.items():
            is_last = (r, c) in self.game.last_move if self.game.last_move else False
            sq.update_square_style(highlight=(self.selected == (r, c)), is_legal=((r,c) in legal_moves), is_check=((r,c) == check_pos), is_last=is_last)
            p = self.game.board[r][c]
            path = self.get_piece_image_path(p) if p else None
            is_frozen = getattr(p, 'freeze_timer', 0) > 0 if p else False
            sq.set_piece_icon(path, is_frozen=is_frozen, piece=p)
        self.sidebar.update_history_text(self.game.history.move_text_history)

    def on_undo_click(self):
        if self.game.undo_move():
            self.selected = None
            self.hide_piece_status() 
            self.init_board_ui()

    def on_square_tap(self, instance):
        if self.game.game_result: return
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black': return

        r, c = instance.row, instance.col
        piece = self.game.board[r][c]

        if self.selected_item:
            if piece and piece.color == self.game.current_turn:
                piece.item = self.selected_item
                if piece.item.id == 6: 
                    piece.coins += 1
                    piece.base_points = max(0, piece.base_points - 1)
                elif piece.item.id == 10 and piece.__class__.__name__.lower() == 'pawn': 
                    piece.base_points = 5  
                    piece.coins = 3
                
                inv = getattr(self.game, f'inventory_{self.game.current_turn}')
                if self.selected_item in inv: inv.remove(self.selected_item)
                
                self.selected_item = None
                self.hide_item_tooltip()
                self.refresh_ui()
                self.show_piece_status(piece) 
            else:
                self.selected_item = None
                self.hide_item_tooltip()
                self.refresh_ui()
            return
            
        if self.selected is None:
            if piece and piece.color == self.game.current_turn:
                self.selected = (r, c)
                self.refresh_ui(self.game.get_legal_moves((r, c)))
                self.show_piece_status(piece)
        else:
            sr, sc = self.selected
            res = self.game.move_piece(sr, sc, r, c)

            if isinstance(res, tuple) and res[0] == "crash":
                _, attacker, defender = res
                self.show_crash_overlay(attacker, defender, (sr, sc), (r, c))
                return
            
            if res == "promote":
                self.hide_piece_status() 
                def do_p(cls):
                    self.game.promote_pawn(r, c, cls)
                    pop.dismiss()
                    self.init_board_ui()
                    self.check_ai_turn()
                pop = PromotionPopup(self.game.board[r][c].color, do_p)
                pop.open()

            elif res == True:
                self.selected = None
                self.hide_piece_status() 
                self.init_board_ui()
                self.check_ai_turn()
            else:
                self.selected = None
                self.hide_piece_status() 
                self.refresh_ui()

    # ย้ายระบบโชว์ Popup ไปใช้ Component
    def show_piece_status(self, piece):
        self.hide_piece_status()
        self.status_popup = UnitCard(piece, self.get_piece_image_path(piece))
        self.root_layout.add_widget(self.status_popup)

    def hide_piece_status(self):
        if self.status_popup:
            self.root_layout.remove_widget(self.status_popup)
            self.status_popup = None

    def show_item_tooltip(self, item):
        self.hide_item_tooltip()
        self.item_tooltip = ItemTooltip(item)
        self.root_layout.add_widget(self.item_tooltip)

    def hide_item_tooltip(self):
        if self.item_tooltip:
            self.root_layout.remove_widget(self.item_tooltip)
            self.item_tooltip = None

    # ย้ายระบบ Crash ไปใช้ Component
    def show_crash_overlay(self, attacker, defender, start_pos, end_pos):
        self.hide_piece_status()
        self.cancel_crash()
        
        self.refresh_ui()
        self.squares[start_pos].update_square_style(highlight=True)
        self.squares[end_pos].update_square_style(is_check=True)

        a_faction = self.get_tribe_name(attacker.color)
        d_faction = self.get_tribe_name(defender.color)
        
        self.crash_popup = CrashOverlay(
            attacker=attacker, defender=defender,
            start_pos=start_pos, end_pos=end_pos,
            a_faction=a_faction, d_faction=d_faction,
            get_img_path_func=self.get_piece_image_path,
            on_finish=self.execute_board_move,
            on_cancel=self.cancel_crash
        )
        self.root_layout.add_widget(self.crash_popup)

    def cancel_crash(self):
        if self.crash_popup:
            if hasattr(self.crash_popup, 'force_cancel'):
                self.crash_popup.force_cancel()
            self.root_layout.remove_widget(self.crash_popup)
            self.crash_popup = None
        self.selected = None
        self.refresh_ui()

    def execute_board_move(self, start_pos, end_pos, crash_status):
        self.cancel_crash()
        
        if crash_status == "blocked":
            # กรณีถูกบล็อกด้วย Mirage Shield
            attacker = self.game.board[start_pos[0]][start_pos[1]]
            defender = self.game.board[end_pos[0]][end_pos[1]]
            defender.item = None
            attacker.has_moved = True 
            self.game.history.save_state(self.game, "Mirage Shield Blocked!")
            self.game.complete_turn() 
            self.refresh_ui()
            self.check_ai_turn() 
            return
            
        is_attacker_won = (crash_status == "won")
        
        res = self.game.move_piece(start_pos[0], start_pos[1], end_pos[0], end_pos[1], resolve_crash=True, crash_won=(crash_status if crash_status == "died" else is_attacker_won))

        if res == "promote":
            def do_p(cls):
                self.game.promote_pawn(end_pos[0], end_pos[1], cls)
                pop.dismiss()
                self.init_board_ui()
                self.check_ai_turn()
            pop = PromotionPopup(self.game.board[end_pos[0]][end_pos[1]].color, do_p)
            pop.open()
            
        elif res == True or res == "died":
            self.selected = None
            self.init_board_ui()
            self.check_ai_turn()
        else:
            self.selected = None
            self.refresh_ui()
            self.check_ai_turn()

    def update_inventory_ui(self):
        self.inventory_layout.clear_widgets()
        inv_label = Label(text=f"INVENTORY\n({self.game.current_turn.upper()})", size_hint_x=0.2, bold=True, color=(0.8, 0.8, 0.8, 1), halign="center")
        self.inventory_layout.add_widget(inv_label)
        inv = getattr(self.game, f'inventory_{self.game.current_turn}', [])
        for i in range(5):
            if i < len(inv):
                item = inv[i]
                btn = Button(background_normal=item.image_path)
                if self.selected_item == item: btn.background_color = (0.5, 1, 0.5, 1) 
                btn.bind(on_release=lambda instance, it=item: self.on_item_click(it))
                self.inventory_layout.add_widget(btn)
            else:
                empty_btn = Button(background_normal='', background_color=(0.2, 0.2, 0.2, 1), text="Empty slot", color=(0.5, 0.5, 0.5, 1))
                self.inventory_layout.add_widget(empty_btn)

    def on_item_click(self, item):
        if self.selected_item == item:
            self.selected_item = None
            self.hide_item_tooltip()
        else:
            self.selected_item = item
            self.show_item_tooltip(item)
        self.update_inventory_ui() 

    def check_ai_turn(self):
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black' and not self.game.game_result:
            Clock.schedule_once(self.trigger_ai_move, 0.8)

    def trigger_ai_move(self, dt):
        move = ChessAI.get_best_move(self.game, ai_color='black')
        if move:
            (sr, sc), (er, ec) = move
            res = self.game.move_piece(sr, sc, er, ec)
            
            if isinstance(res, tuple) and res[0] == "crash":
                attacker, defender = res[1], res[2]
                
                if getattr(defender, 'item', None) and defender.item.id == 4:
                    defender.item = None
                    attacker.has_moved = True 
                    self.game.history.save_state(self.game, "Mirage Shield Blocked!")
                    self.game.complete_turn()
                    self.init_board_ui()
                    return 
                    
                a_faction = self.get_tribe_name(attacker.color)
                d_faction = self.get_tribe_name(defender.color)
                
                # เรียกใช้ Logic AI ที่แยกไว้
                result = simulate_ai_crash_result(attacker, defender, a_faction, d_faction)
                crash_status = result if result == "died" else (result == "win")
                
                res = self.game.move_piece(sr, sc, er, ec, resolve_crash=True, crash_won=crash_status)
            
            if res == "promote":
                from logic.pieces import Queen
                self.game.promote_pawn(er, ec, Queen)
            
            self.init_board_ui()