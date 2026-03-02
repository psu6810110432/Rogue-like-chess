# screens/gameplay_screen.py
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

from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image

from logic.board import ChessBoard
from logic.ai_logic import ChessAI
from components.chess_square import ChessSquare
from components.sidebar_ui import SidebarUI

try:
    from logic.maps.forest_map import ForestMap
except ImportError:
    ForestMap = None

try:
    from logic.maps.desert_map import DesertMap
except ImportError:
    DesertMap = None

# ✨ ดึง TundraMap เข้ามา
try:
    from logic.maps.tundra_map import TundraMap
except ImportError:
    TundraMap = None

class PromotionPopup(ModalView):
    # ✨ ลบ parameter theme ออก เพราะเราจะให้ Popup ดึงค่าเองตามสี (color)
    def __init__(self, color, callback, **kwargs):
        super().__init__(size_hint=(0.6, 0.2), auto_dismiss=False, **kwargs)
        layout = GridLayout(cols=4, padding=10, spacing=10)
        from logic.pieces import Queen, Rook, Bishop, Knight
        ops = [Queen, Rook, Bishop, Knight]
        names = ['queen', 'rook', 'bishop', 'knight']
        
        # ✨ ดึง Theme ตามสีที่ได้โปรโมท
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
        self.crash_popup = None # ✨ เปลี่ยนตัวแปรจาก clash เป็น crash
        self.item_tooltip = None
        self.selected_item = None

    def get_tribe_name(self, color):
        """แปลงชื่อ faction เป็นชื่อ tribe"""
        app = App.get_running_app()
        theme = getattr(app, f'selected_unit_{color}', 'Medieval Knights')
        if theme == "Ayothaya": 
            return "ayothaya"
        elif theme == "Demon": 
            return "demon"
        elif theme == "Heaven": 
            return "heaven"
        else: 
            return "medieval"

    def setup_game(self, mode):
        self.main_layout.clear_widgets()
        self.game_mode = mode
        
        app = App.get_running_app()
        selected_board = getattr(app, 'selected_board', 'Classic Board')
        
        # ✨ เช็คเงื่อนไขให้ครบทุกด่าน
        if selected_board == 'Enchanted Forest' and ForestMap is not None:
            self.game = ForestMap()
        elif selected_board == 'Desert Ruins' and DesertMap is not None:
            self.game = DesertMap()
        elif selected_board == 'Frozen Tundra' and TundraMap is not None:
            self.game = TundraMap()
        else:
            # ดึงค่า tribe จากการเลือกของผู้เล่น
            white_tribe = self.get_tribe_name('white')
            black_tribe = self.get_tribe_name('black')
            self.game = ChessBoard(white_tribe, black_tribe)
            self.game.bg_image = 'assets/boards/classic.png'
            
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
        """✨ ฟังก์ชันสำหรับดึง Path รูปภาพหมากตามเผ่า (Theme) แบบแยกสี White/Black"""
        app = App.get_running_app()
        p_color = piece.color
        p_name = piece.__class__.__name__.lower()

        # ✨ คืนค่ารูปภาพสิ่งกีดขวาง (Map Events)
        if p_name == 'obstacle':
            obstacle_type = piece.name.lower()
            if obstacle_type == 'thorn':
                return "assets/pieces/event/event1.png"      # รูปหนามป่า
            elif obstacle_type == 'sandstorm':
                return "assets/pieces/event/event2.png"      # รูปพายุทะเลทราย
            else:
                return "assets/pieces/event/event3.png"      # เผื่อใช้กับ Event อื่นในอนาคต
                
        # ✨ เช็คสีของหมาก เพื่อดึง Theme ให้ตรงกับฝ่ายนั้น
        if p_color == 'white':
            theme = getattr(app, 'selected_unit_white', 'Medieval Knights')
        else:
            theme = getattr(app, 'selected_unit_black', 'Demon')
        
        # จัดการชื่อ folder ของแต่ละเผ่า
        if theme == "Ayothaya":
            theme_folder = "ayothaya"
        elif theme == "Demon":
            theme_folder = "demon"
        elif theme == "Heaven":
            theme_folder = "heaven"
        else:
            theme_folder = "medieval"

        # ✨ แยกการเช็คเบี้ย (Pawn) ออกมา เพื่อดึงเลขที่สุ่มไว้ (6-9)
        if p_name == 'pawn':
            # ดึงตัวเลข 6-9 ที่สุ่มเก็บไว้ในตัวหมาก (ถ้าหาไม่เจอให้ใช้ 6 เป็นค่าเริ่มต้น)
            num = getattr(piece, 'variant', 6)
        else:
            # แมปชื่อหมากตัวอื่นๆ เป็นตัวเลข
            piece_map = {
                'king': 1, 'queen': 2, 'rook': 3,
                'knight': 4, 'bishop': 5
            }
            num = piece_map.get(p_name, 1)

        # คืนค่า Path เต็มของรูปภาพ
        return f"assets/pieces/{theme_folder}/{p_color}/chess {theme_folder}{num}.png"

    def on_quit(self):
        self.manager.current = 'setup'

    def init_board_ui(self):
        self.container.clear_widgets()

        if getattr(self, 'game_mode', 'PVP') == 'PVE':
            view_perspective = 'white'
        else:
            view_perspective = self.game.current_turn

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
        turn_text = f"{self.game.current_turn.upper()}'S TURN"

        self.update_inventory_ui()

        if self.game.game_result: self.info_label.text = self.game.game_result
        else: self.info_label.text = f"{self.game.current_turn.upper()}'S TURN"
        
        check_pos = self.game.find_king(self.game.current_turn) if self.game.is_in_check(self.game.current_turn) else None
        for (r, c), sq in self.squares.items():
            is_last = (r, c) in self.game.last_move if self.game.last_move else False
            sq.update_square_style(highlight=(self.selected == (r, c)), is_legal=((r,c) in legal_moves), is_check=((r,c) == check_pos), is_last=is_last)
            p = self.game.board[r][c]
            path = self.get_piece_image_path(p) if p else None
            
            # ✨ เช็คว่าหมากตัวนี้ติดสถานะแช่แข็งอยู่หรือไม่ (ถ้าไม่มีหมากหรือไม่มีสถานะจะเป็น False)
            is_frozen = getattr(p, 'freeze_timer', 0) > 0 if p else False
            
            # ✨ ส่งค่า is_frozen ไปให้ ChessSquare เพื่อเปลี่ยนสี
            sq.set_piece_icon(path, is_frozen=is_frozen)
        self.sidebar.update_history_text(self.game.history.move_text_history)

    def on_undo_click(self):
        if self.game.undo_move():
            self.selected = None
            self.hide_piece_status() # ซ่อน Pop-up ถ้ายกเลิกการเดิน
            self.init_board_ui()

    def on_square_tap(self, instance):
        if self.game.game_result: return
        
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black':
            return

        r, c = instance.row, instance.col
        piece = self.game.board[r][c]

        if self.selected_item:
            if piece and piece.color == self.game.current_turn:
                # ✨ ใส่ไอเทมลงในหมาก
                piece.item = self.selected_item
                # ✨ เพิ่มโค้ดส่วนนี้: สเตตัสเปลี่ยนทันทีเมื่อสวมใส่
                if piece.item.id == 6: # Gambler's Coin
                    piece.coins += 1
                    piece.base_points = max(0, piece.base_points - 1)
                elif piece.item.id == 10 and piece.__class__.__name__.lower() == 'pawn': # Crown of the Usurper
                    piece.base_points = 5  # (สมมติให้ 50 เท่ากับ King)
                    piece.coins = 3
                
                # ✨ ลบไอเทมออกจากกระเป๋า
                inv = getattr(self.game, f'inventory_{self.game.current_turn}')
                if self.selected_item in inv:
                    inv.remove(self.selected_item)
                
                # เคลียร์สถานะการเลือกไอเทม
                self.selected_item = None
                self.hide_item_tooltip()
                self.refresh_ui()
                self.show_piece_status(piece) # โชว์สถานะอัปเดตทันที
            else:
                # ยกเลิกการเลือกไอเทมหากไปคลิกช่องว่างหรือฝั่งศัตรู
                self.selected_item = None
                self.hide_item_tooltip()
                self.refresh_ui()
            return
            
        if self.selected is None:
            piece = self.game.board[r][c]
            if piece and piece.color == self.game.current_turn:
                self.selected = (r, c)
                self.refresh_ui(self.game.get_legal_moves((r, c)))
                
                # โชว์ Pop-up ข้อมูลหมากทางด้านขวา เมื่อมีการกดเลือกหมาก
                self.show_piece_status(piece)
        else:
            sr, sc = self.selected
            res = self.game.move_piece(sr, sc, r, c)

            # ✨ เช็คสถานะการ CRASH
            if isinstance(res, tuple) and res[0] == "crash":
                _, attacker, defender = res
                self.show_crash_popup(attacker, defender, (sr, sc), (r, c))
                return
            
            if res == "promote":
                self.hide_piece_status() #  ซ่อน Pop-up
                def do_p(cls):
                    self.game.promote_pawn(r, c, cls)
                    pop.dismiss()
                    self.init_board_ui()
                    self.check_ai_turn()
                # ✨ ลบการดึง theme เพราะ PromotionPopup เช็คจากสีเองได้แล้ว
                pop = PromotionPopup(self.game.board[r][c].color, do_p)
                pop.open()

            elif res == True:
                self.selected = None
                self.hide_piece_status() #  ซ่อน Pop-up เมื่อเดินเสร็จ
                self.init_board_ui()
                self.check_ai_turn()
            else:
                self.selected = None
                self.hide_piece_status() #  ซ่อน Pop-up เมื่อกดที่อื่น (ยกเลิกการเลือก)
                self.refresh_ui()

# ✨ ฟังก์ชันสร้างหน้าต่าง CRASH (อัปเดตหน้าตาใหม่)
    def show_crash_popup(self, attacker, defender, start_pos, end_pos):
        self.hide_piece_status()
        self.cancel_crash()
        # ✨ เพิ่มบรรทัดนี้: รีเซ็ตจำนวนครั้งการติด Stagger เมื่อเริ่ม Crash ครั้งแรก
        self.crash_stagger_count = 0
        
        # ไฮไลท์ช่องบนกระดาน
        self.refresh_ui()
        self.squares[start_pos].update_square_style(highlight=True)
        self.squares[end_pos].update_square_style(is_check=True)
        
        # ขยายขนาด Popup เล็กน้อยเพื่อรองรับพื้นที่เหรียญ
        self.crash_popup = BoxLayout(orientation='vertical', size_hint=(None, None), size=(340, 400), 
            pos_hint={'right': 0.96, 'center_y': 0.5},
            padding=15,
            spacing=10)
        
        with self.crash_popup.canvas.before:
            Color(0.08, 0.08, 0.12, 0.98) 
            self.crash_popup.bg_rect = Rectangle(pos=self.crash_popup.pos, size=self.crash_popup.size)
        self.crash_popup.bind(pos=self._update_crash_bg, size=self._update_crash_bg)
        
        title_lbl = Label(text="CRASH!", bold=True, font_size='28sp', color=(1, 0.2, 0.2, 1), size_hint_y=0.15)
        self.crash_popup.add_widget(title_lbl)
        
        combatants_layout = BoxLayout(orientation='horizontal', size_hint_y=0.55)
        
        # 🚨 นำเข้า GridLayout
        from kivy.uix.gridlayout import GridLayout
        
        # === ฝ่ายโจมตี (Attacker) ===
        atk_box = BoxLayout(orientation='vertical', spacing=5)
        atk_img = Image(source=self.get_piece_image_path(attacker), size_hint_y=0.4)
        atk_pts = getattr(attacker, 'base_points', 5)
        atk_box.add_widget(atk_img)
        
        # ข้อมูล point (ห้ามแก้ไข)
        atk_box.add_widget(Label(text=f"point : {atk_pts}", font_size='14sp', color=(1, 0.8, 0.2, 1), size_hint_y=0.15))
        
        # 🚨 FIX: สร้าง GridLayout สำหรับวางรูปเหรียญของฝ่ายโจมตี (ลบโค้ด text 0 แบบเก่าทิ้ง)
        self.a_coins_layout = GridLayout(cols=3, spacing=2, size_hint_y=0.25)
        atk_box.add_widget(self.a_coins_layout)
        
        # ข้อมูล crash รวม (เปลี่ยนชื่อตัวแปรเป็น a_val_lbl เพื่อให้แอนิเมชันหาเจอ)
        self.a_val_lbl = Label(text=f"crash : {atk_pts}", font_size='16sp', color=(1, 0.4, 0.4, 1), bold=True, size_hint_y=0.2)
        atk_box.add_widget(self.a_val_lbl)
        
        self.vs_lbl = Label(text="VS", bold=True, font_size='24sp', color=(0.8, 0.8, 0.8, 1), size_hint_x=0.4, halign="center")
        
        # === ฝ่ายป้องกัน (Defender) ===
        def_box = BoxLayout(orientation='vertical', spacing=5)
        def_img = Image(source=self.get_piece_image_path(defender), size_hint_y=0.4)
        def_pts = getattr(defender, 'base_points', 5)
        def_box.add_widget(def_img)
        
        # ข้อมูล point (ห้ามแก้ไข)
        def_box.add_widget(Label(text=f"point : {def_pts}", font_size='14sp', color=(1, 0.8, 0.2, 1), size_hint_y=0.15))
        
        # 🚨 FIX: สร้าง GridLayout สำหรับวางรูปเหรียญของฝ่ายป้องกัน
        self.d_coins_layout = GridLayout(cols=3, spacing=2, size_hint_y=0.25)
        def_box.add_widget(self.d_coins_layout)
        
        # ข้อมูล crash รวม (เปลี่ยนชื่อตัวแปรเป็น d_val_lbl)
        self.d_val_lbl = Label(text=f"crash : {def_pts}", font_size='16sp', color=(0.4, 0.4, 1, 1), bold=True, size_hint_y=0.2)
        def_box.add_widget(self.d_val_lbl)
        
        combatants_layout.add_widget(atk_box)
        combatants_layout.add_widget(self.vs_lbl)
        combatants_layout.add_widget(def_box)
        
        self.crash_popup.add_widget(combatants_layout)
        
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=10, padding=[0, 10, 0, 0])
        
        # ปุ่มกดเริ่มทอยเหรียญ
        self.crash_btn = Button(text="CRASH!", bold=True, font_size='18sp', background_color=(0.8, 0.2, 0.2, 1))
        self.crash_btn.bind(on_release=lambda x: self.start_crash_animation(start_pos, end_pos))
        
        self.cancel_btn = Button(text="CANCEL", font_size='14sp', background_color=(0.3, 0.3, 0.3, 1))
        self.cancel_btn.bind(on_release=lambda x: self.cancel_crash(reset_selection=True))
        
        btn_layout.add_widget(self.crash_btn)
        btn_layout.add_widget(self.cancel_btn)
        
        self.crash_popup.add_widget(btn_layout)
        self.root_layout.add_widget(self.crash_popup)
        
        self.crash_popup.x += 30
        self.crash_popup.opacity = 0
        anim = Animation(x=self.crash_popup.x - 30, opacity=1, duration=0.2, t='out_quad')
        anim.start(self.crash_popup)

    # ✨ ฟังก์ชันอัปเดตพื้นหลังของหน้าต่าง Crash
    def _update_crash_bg(self, instance, value):
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size

    # ✨ ฟังก์ชันยกเลิกการต่อสู้ ปิดป๊อปอัป
    def cancel_crash(self, reset_selection=False):
        if hasattr(self, 'spin_event') and self.spin_event:
            self.spin_event.cancel()
        if self.crash_popup:
            self.root_layout.remove_widget(self.crash_popup)
            self.crash_popup = None
        
        if reset_selection:
            self.selected = None
            self.refresh_ui()

# ✨ ฟังก์ชันเตรียมแอนิเมชัน
    def start_crash_animation(self, start_pos, end_pos):
        self.crash_btn.disabled = True
        self.cancel_btn.disabled = True

        sr, sc = start_pos
        er, ec = end_pos
        attacker = self.game.board[sr][sc]
        defender = self.game.board[er][ec]

        # ✨ Item 4: Mirage Shield (ปัดป้องการแครช)
        if getattr(defender, 'item', None) and defender.item.id == 4:
            defender.item = None # ไอเทมพัง
            self.root_layout.remove_widget(self.crash_popup) # ปิดหน้าต่าง
            self.crash_popup = None
            
            attacker.has_moved = True # 🚨 FIX: ตั้งค่าว่าหมากตัวนี้เดินแล้ว
            self.game.history.save_state(self.game, "Mirage Shield Blocked!")
            self.game.complete_turn() 
            self.refresh_ui()
            self.check_ai_turn() 
            return 

        a_base = getattr(attacker, 'base_points', 5)
        a_coins = getattr(attacker, 'coins', 3)
        d_base = getattr(defender, 'base_points', 5)
        d_coins = getattr(defender, 'coins', 3)

        # ✨ Item 8: Aura of Misfortune 
        if getattr(defender, 'item', None) and defender.item.id == 8:
            a_coins = max(0, a_coins - 1)
        if getattr(attacker, 'item', None) and attacker.item.id == 8:
            d_coins = max(0, d_coins - 1)

        # ✨ Item 2: Clutch Protection 
        if getattr(defender, 'item', None) and defender.item.id == 2:
            a_coins = 0
            defender.item = None 

        from logic.crash_logic import calculate_total_points
        
        # ✨ ดึงค่า Theme/Faction ของทั้งสองฝ่าย
        app = App.get_running_app()
        def get_faction_name(color):
            theme = getattr(app, f'selected_unit_{color}', 'Medieval Knights')
            if theme == "Ayothaya": return "ayothaya"
            elif theme == "Demon": return "demon"
            elif theme == "Heaven": return "heaven"
            return "medieval"
            
        a_faction = get_faction_name(attacker.color)
        d_faction = get_faction_name(defender.color)

        self.a_final_total, self.a_results = calculate_total_points(a_base, a_coins, a_faction)
        self.d_final_total, self.d_results = calculate_total_points(d_base, d_coins, d_faction)

        # 🚨 FIX: อัปเดตข้อความแต้มรวมเริ่มต้น
        self.a_val_lbl.text = f"crash : {a_base}"
        self.d_val_lbl.text = f"crash : {d_base}"

        # 🚨 FIX: ล้างกระดานเหรียญเก่าและเสกรูปเหรียญเปล่า (coin10.png)
        self.a_coins_layout.clear_widgets()
        self.d_coins_layout.clear_widgets()
        self.a_coin_widgets = []
        self.d_coin_widgets = []

        for _ in range(a_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(32, 32))
            self.a_coin_widgets.append(img)
            self.a_coins_layout.add_widget(img)

        for _ in range(d_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(32, 32))
            self.d_coin_widgets.append(img)
            self.d_coins_layout.add_widget(img)

        # แปลงข้อความเป็นค่าตัวเลข เพื่อนำไปโชว์ตอนบวกแต้ม
        def get_pt(res_str, faction):
            if "Green" in res_str: return 100
            if "Cyan" in res_str: return 10
            if "Purple" in res_str: return 6
            if "Orange" in res_str: return 4
            if "Blue" in res_str: return 3
            if "Red" in res_str: return 2
            if "Yellow" in res_str: return 1
            if "Tails" in res_str and faction == "demon": return -3
            return 0

        self.a_pts_array = [get_pt(r, a_faction) for r in self.a_results]
        self.d_pts_array = [get_pt(r, d_faction) for r in self.d_results]

        # เก็บรอบของ Animation
        self.anim_state = {
            'side': 'atk',
            'coin_idx': 0,
            'ticks': 0,
            'max_ticks': 20, # ความยาวของการกระพริบต่อ 1 เหรียญ
            'a_current_total': a_base,
            'd_current_total': d_base,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'attacker': attacker,
            'defender': defender,
            'attacker_died': False,
            'a_faction': a_faction,
            'd_faction': d_faction
        }

        # เรียก Clock ให้หมุนเลขทุกๆ 0.05 วินาที
        self.spin_event = Clock.schedule_interval(self.animate_coin_step, 0.10)


    # ✨ ฟังก์ชันรันแอนิเมชันทีละเฟรม
    def animate_coin_step(self, dt):
        state = self.anim_state
        side = state['side']
        idx = state['coin_idx']
        
        # เลือกตัวแปรของฝั่งที่กำลังทอยเหรียญ
        if side == 'atk':
            pts_array = self.a_pts_array
            results = self.a_results
            faction = state['a_faction']
            coin_widgets = self.a_coin_widgets
            lbl_total = self.a_val_lbl
            current_total_key = 'a_current_total'
        else:
            pts_array = self.d_pts_array
            results = self.d_results
            faction = state['d_faction']
            coin_widgets = self.d_coin_widgets
            lbl_total = self.d_val_lbl
            current_total_key = 'd_current_total'

        # ถ้าทอยเหรียญฝั่งนี้ครบแล้ว ให้สลับฝั่ง หรือจบแอนิเมชัน
        if idx >= len(pts_array):
            if side == 'atk':
                state['side'] = 'def'
                state['coin_idx'] = 0
                state['ticks'] = 0
                return
            else:
                # 🚨 จบแอนิเมชันทั้ง 2 ฝั่ง ให้ไปรันคำสั่งประมวลผลผลลัพธ์ของระบบคุณต่อ
                self.spin_event.cancel()
                self.finish_crash_animation()  # ✨ เปลี่ยนมาเรียกฟังก์ชันที่เราสร้างไว้
                return

        # --- อนิเมชันกระพริบเหรียญ ---
        state['ticks'] += 1
        
        # ป้องกัน error กรณีไม่มี widget เหรียญ
        if idx < len(coin_widgets):
            img_widget = coin_widgets[idx]
            
            # 🚨 FIX: สลับความทึบให้เหรียญเปล่าดูเหมือนกำลังทอย
            img_widget.opacity = 1.0 if (state['ticks'] % 4) < 2 else 0.3
            
            if state['ticks'] >= state['max_ticks']:
                # 🚨 FIX: หงายเหรียญจริง และเลิกกระพริบ
                img_widget.opacity = 1.0
                img_widget.source = self._get_coin_img(results[idx], faction)
                
                # บวกแต้ม
                state[current_total_key] += pts_array[idx]
                lbl_total.text = f"crash : {state[current_total_key]}"
                
                # ขยับไปเหรียญถัดไป
                state['coin_idx'] += 1
                state['ticks'] = 0
        else:
            # ข้ามไปถ้า index เกิน
            state['coin_idx'] += 1
            state['ticks'] = 0

    def finish_crash_animation(self):
        a_tot = self.anim_state['a_current_total']
        d_tot = self.anim_state['d_current_total']

        if a_tot > d_tot:
            # ✨ โจมตีสำเร็จ
            result_text = "[color=00ff00]BREAKING[/color]"
            self.vs_lbl.text = result_text
            self.vs_lbl.font_size = '20sp'
            self.vs_lbl.markup = True
            Clock.schedule_once(self.execute_board_move, 1.5)
            
        elif a_tot == d_tot:
            # ✨ 1. เสมอ (Draw): วนลูปการทอยใหม่โดยอัตโนมัติ
            result_text = "[color=ffff00]DRAW[/color]"
            self.vs_lbl.text = result_text
            self.vs_lbl.font_size = '20sp'
            self.vs_lbl.markup = True
            
            # รันการต่อสู้ใหม่อีกครั้งหลังจากแสดงผล 1.5 วิ
            Clock.schedule_once(lambda dt: self.start_crash_animation(self.anim_state['start_pos'], self.anim_state['end_pos']), 1.5)
            
        else:
            # ✨ 2. โจมตีพลาด (a_tot < d_tot) 
            self.crash_stagger_count += 1
            if self.crash_stagger_count < 2:
                # พลาดครั้งแรก ให้ติดสถานะ STAGGER และทำการทอยสู้ต่อ
                result_text = "[color=ff8800]STAGGER[/color]" 
                self.vs_lbl.text = result_text
                self.vs_lbl.font_size = '20sp'
                self.vs_lbl.markup = True
                
                # รันการต่อสู้ใหม่อีกครั้ง
                Clock.schedule_once(lambda dt: self.start_crash_animation(self.anim_state['start_pos'], self.anim_state['end_pos']), 1.5)
            else:
                # พลาดครั้งที่สอง ติดสถานะ DISTORTION (หมากตาย)
                result_text = "[color=ff0000]DISTORTION[/color]" 
                self.vs_lbl.text = result_text
                self.vs_lbl.font_size = '20sp'
                self.vs_lbl.markup = True
                
                # ทำเครื่องหมายให้ตัวโจมตีตายและส่งผลให้กระดานทำงานต่อ
                self.anim_state['attacker_died'] = True 
                Clock.schedule_once(self.execute_board_move, 1.5)

    def execute_board_move(self, dt):
        start_pos = self.anim_state['start_pos']
        end_pos = self.anim_state['end_pos']
        attacker_died = self.anim_state.get('attacker_died', False) 
        
        a_tot = self.anim_state['a_current_total']
        d_tot = self.anim_state['d_current_total']

        is_attacker_won = (a_tot > d_tot)
        self.cancel_crash() # ปิดหน้าต่างต่อสู้

        # ระบุผลลัพธ์ว่า แครชชนะ หรือ ตีพลาดจนตาย
        crash_status = "died" if attacker_died else is_attacker_won
        
        # โยนภาระทั้งหมดให้ Board (Logic) จัดการ ทั้งเดิน แจกไอเทม สลับเทิร์น
        res = self.game.move_piece(start_pos[0], start_pos[1], end_pos[0], end_pos[1], resolve_crash=True, crash_won=crash_status)

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

    # ✨ ฟังก์ชันแสดง Card/Pop-up โชว์ชื่อและแต้มของหมาก (อัปเดตเป็น base_points และ coins)
    def show_piece_status(self, piece):
        self.hide_piece_status()
        # สร้าง Layout ของ Card Pop-up
        self.status_popup = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(420, 300),
            pos_hint={'right': 0.95, 'center_y': 0.5},
            padding=10,
            spacing=10
        )
        
        # วาดพื้นหลัง Card
        with self.status_popup.canvas.before:
            Color(0.1, 0.1, 0.1, 0.98) 
            self.status_popup.bg_rect = Rectangle(pos=self.status_popup.pos, size=self.status_popup.size)
        self.status_popup.bind(pos=self._update_popup_bg, size=self._update_popup_bg)
        
        img_path = self.get_piece_image_path(piece)
        img = Image(source=img_path, size_hint_x=0.4)
        self.status_popup.add_widget(img)
        text_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        # ชื่อหมาก
        name_lbl = Label(text=piece.__class__.__name__.upper(), bold=True, font_size='22sp', color=(1, 1, 1, 1), halign='left')
        text_layout.add_widget(name_lbl)
        
        # แต้มหมาก
        p_base = getattr(piece, 'base_points', 5)
        pts_lbl = Label(text=f"{p_base} Points", font_size='16sp', color=(1, 0.8, 0.2, 1), halign='left')
        pts_lbl.bind(size=pts_lbl.setter('text_size')) 
        text_layout.add_widget(pts_lbl)

        # จำนวนเหรียญที่มี
        p_coins = getattr(piece, 'coins', 3)
        coins_lbl = Label(text=f"Coins: {p_coins}", font_size='14sp', color=(0.7, 0.8, 1, 1), halign='left')
        coins_lbl.bind(size=coins_lbl.setter('text_size'))
        text_layout.add_widget(coins_lbl)
        
        # 🚨 [ส่วนที่แก้ไข] เพิ่มการแสดงผลรูปภาพไอเทมขนาด 48x48
        p_item = getattr(piece, 'item', None)
        item_container = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=10)
        
        if p_item:
            # มี Item: แสดงรูป 48x48 และชื่อ Item
            item_img = Image(
                source=p_item.image_path,
                size_hint=(None, None),
                size=(48, 48), # ล็อคขนาดภาพไม่ให้แตก
                keep_ratio=True,
                allow_stretch=True
            )
            item_lbl = Label(
                text=f"Eqp: {p_item.name}", 
                font_size='14sp', 
                color=(0.4, 1, 0.4, 1), 
                halign='left',
                valign='middle'
            )
            item_lbl.bind(size=item_lbl.setter('text_size'))
            
            item_container.add_widget(item_img)
            item_container.add_widget(item_lbl)
        else:
            # ไม่มี Item
            item_lbl = Label(
                text="Eqp: No Item", 
                font_size='14sp', 
                color=(0.5, 0.5, 0.5, 1), 
                halign='left',
                valign='middle'
            )
            item_lbl.bind(size=item_lbl.setter('text_size'))
            item_container.add_widget(item_lbl)

        text_layout.add_widget(item_container)
        # 🚨 [จบส่วนที่แก้ไข]

        self.status_popup.add_widget(text_layout)
        self.root_layout.add_widget(self.status_popup)
        
        # ทำแอนิเมชันให้การ์ดสไลด์เข้ามานิดหน่อยเพื่อความสมูท
        self.status_popup.x += 20
        self.status_popup.opacity = 0
        anim = Animation(x=self.status_popup.x - 20, opacity=1, duration=0.15)
        anim.start(self.status_popup)

    # ฟังก์ชันอัปเดตพื้นหลัง Pop-up
    def _update_popup_bg(self, instance, value):
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size

    def _get_coin_img(self, res_str, faction):
        """แปลงผลลัพธ์การทอยเหรียญเป็นไฟล์ภาพ"""
        if "Green" in res_str: return "assets/coin/coin9.png"
        if "Cyan" in res_str: return "assets/coin/coin8.png"
        if "Purple" in res_str: return "assets/coin/coin7.png"
        if "Orange" in res_str: return "assets/coin/coin6.png"
        if "Blue" in res_str: return "assets/coin/coin5.png"
        if "Red" in res_str: return "assets/coin/coin4.png"
        if "Yellow" in res_str: return "assets/coin/coin3.png"
        if "Tails" in res_str:
            return "assets/coin/coin1.png" if faction == "demon" else "assets/coin/coin2.png"
        return "assets/coin/coin10.png"

    # ฟังก์ชันซ่อนและทำลาย Pop-up
    def hide_piece_status(self):
        if self.status_popup:
            self.root_layout.remove_widget(self.status_popup)
            self.status_popup = None

    # ==========================================
    # ✨ ระบบ INVENTORY & ITEM UI
    # ==========================================
    def update_inventory_ui(self):
        """อัปเดตการแสดงผลไอเทมในกระเป๋าของคนที่กำลังเล่นอยู่"""
        self.inventory_layout.clear_widgets()
        
        # ป้ายบอกกระเป๋าของใคร
        inv_label = Label(text=f"INVENTORY\n({self.game.current_turn.upper()})", size_hint_x=0.2, bold=True, color=(0.8, 0.8, 0.8, 1), halign="center")
        self.inventory_layout.add_widget(inv_label)

        # ดึงลิสต์ไอเทมจาก Logic
        inv = getattr(self.game, f'inventory_{self.game.current_turn}', [])

        # สร้างช่องเก็บของ 5 ช่อง
        for i in range(5):
            if i < len(inv):
                item = inv[i]
                # ปุ่มไอเทม
                btn = Button(background_normal=item.image_path)
                # ใส่สีเขียวอ่อนเพื่อไฮไลท์เวลาถูกคลิกเลือก
                if self.selected_item == item:
                    btn.background_color = (0.5, 1, 0.5, 1) 
                
                btn.bind(on_release=lambda instance, it=item: self.on_item_click(it))
                self.inventory_layout.add_widget(btn)
            else:
                # ช่องว่าง
                empty_btn = Button(background_normal='', background_color=(0.2, 0.2, 0.2, 1), text="Empty slot", color=(0.5, 0.5, 0.5, 1))
                self.inventory_layout.add_widget(empty_btn)

    def on_item_click(self, item):
        """เมื่อกดที่ไอเทมในกระเป๋า"""
        # ถ้ากดซ้ำที่เดิม ให้ยกเลิกการเลือก
        if self.selected_item == item:
            self.selected_item = None
            self.hide_item_tooltip()
        else:
            self.selected_item = item
            self.show_item_tooltip(item)
            
        self.update_inventory_ui() # รีเฟรชสีกรอบไอเทม

    def show_item_tooltip(self, item):
        """แสดงคำอธิบายไอเทมเมื่อถูกคลิก"""
        self.hide_item_tooltip()
        
        # 🚨 [ส่วนที่แก้ไข] ขยายกรอบ 3 เท่า ย้ายไปขวา และเปลี่ยนเป็นแนวนอน
        self.item_tooltip = BoxLayout(
            orientation='horizontal', size_hint=(None, None), size=(800, 300),
            pos_hint={'right': 0.98, 'center_y': 0.5}, # ย้ายไปฝั่งขวา ตรงกลางหน้าจอ
            padding=20, spacing=20
        )
        with self.item_tooltip.canvas.before:
            Color(0.05, 0.05, 0.1, 0.98) # มืดทึบกว่าเดิม
            self.item_tooltip.bg_rect = Rectangle(pos=self.item_tooltip.pos, size=self.item_tooltip.size)
            
        self.item_tooltip.bind(pos=lambda inst, val: setattr(inst.bg_rect, 'pos', inst.pos) if hasattr(inst, 'bg_rect') else None)
        self.item_tooltip.bind(size=lambda inst, val: setattr(inst.bg_rect, 'size', inst.size) if hasattr(inst, 'bg_rect') else None)
        
        # 🚨 [ส่วนที่แก้ไข] เพิ่มรูปภาพขนาดใหญ่ด้านซ้าย
        large_img = Image(
            source=item.image_path,
            size_hint=(None, 1),
            width=200, # ล็อคความกว้างรูป
            keep_ratio=True,
            allow_stretch=True
        )
        self.item_tooltip.add_widget(large_img)
        
        # 🚨 [ส่วนที่แก้ไข] กรอบข้อความด้านขวา (ขยายฟอนต์ 3 เท่า)
        text_layout = BoxLayout(orientation='vertical', spacing=10)
        
        name_lbl = Label(
            text=f"[color=ffff00]{item.name}[/color]", 
            markup=True, bold=True, 
            font_size='48sp', # ขยายจาก 18sp เป็น 48sp
            size_hint_y=0.4, 
            halign='left'
        )
        name_lbl.bind(size=name_lbl.setter('text_size'))
        
        desc_lbl = Label(
            text=item.description, 
            font_size='36sp', # ขยายจาก 14sp เป็น 36sp
            color=(0.9, 0.9, 0.9, 1),
            halign="left", 
            valign="top"
        )
        desc_lbl.bind(size=desc_lbl.setter('text_size'))
        
        text_layout.add_widget(name_lbl)
        text_layout.add_widget(desc_lbl)
        
        self.item_tooltip.add_widget(text_layout)
        self.root_layout.add_widget(self.item_tooltip)

    def hide_item_tooltip(self):
        if self.item_tooltip:
            self.root_layout.remove_widget(self.item_tooltip)
            self.item_tooltip = None

    def check_ai_turn(self):
        if getattr(self, 'game_mode', 'PVP') == 'PVE' and self.game.current_turn == 'black' and not self.game.game_result:
            Clock.schedule_once(self.trigger_ai_move, 0.8)

    # ✨ ให้บอทสุ่มผล Crash ไปเลยโดยอัตโนมัติ
    def trigger_ai_move(self, dt):
        move = ChessAI.get_best_move(self.game, ai_color='black')
        if move:
            (sr, sc), (er, ec) = move
            res = self.game.move_piece(sr, sc, er, ec)
            
            if isinstance(res, tuple) and res[0] == "crash":
                _, attacker, defender = res
                a_base = getattr(attacker, 'base_points', 5)
                a_coins = getattr(attacker, 'coins', 3)
                d_base = getattr(defender, 'base_points', 5)
                d_coins = getattr(defender, 'coins', 3)
                
                from logic.crash_logic import calculate_total_points
                
                stagger_count = 0
                is_attacker_won = False
                attacker_died = False
                
                # ✨ ดึงค่า Faction สำหรับ AI (เหมือนกับจุดที่ 1)
                app = App.get_running_app()
                def get_faction_name(color):
                    theme = getattr(app, f'selected_unit_{color}', 'Medieval Knights')
                    if theme == "Ayothaya": return "ayothaya"
                    elif theme == "Demon": return "demon"
                    elif theme == "Heaven": return "heaven"
                    return "medieval"
                
                a_faction = get_faction_name(attacker.color)
                d_faction = get_faction_name(defender.color)

                # 🚨 FIX: ให้ AI รู้จักโดนเอฟเฟกต์ไอเทมก่อนทอยเหรียญเหมือนผู้เล่นด้วย!
                if getattr(defender, 'item', None) and defender.item.id == 4:
                    defender.item = None
                    attacker.has_moved = True # 🚨 FIX: ตั้งค่าว่า AI เดินแล้ว
                    self.game.history.save_state(self.game, "Mirage Shield Blocked!")
                    self.game.complete_turn()
                    self.init_board_ui()
                    return # จบเทิร์นบอททันทีเพราะโดนโล่ปัด
                    
                if getattr(defender, 'item', None) and defender.item.id == 8: a_coins = max(0, a_coins - 1)
                if getattr(attacker, 'item', None) and attacker.item.id == 8: d_coins = max(0, d_coins - 1)
                if getattr(defender, 'item', None) and defender.item.id == 2:
                    a_coins = 0
                    defender.item = None

                # ✨ ลูปวนหาผลลัพธ์ของ AI (จำลองการ Draw และ Stagger)
                while True:
                    a_tot, _ = calculate_total_points(a_base, a_coins, a_faction)
                    d_tot, _ = calculate_total_points(d_base, d_coins, d_faction)
                    
                    if a_tot > d_tot:
                        is_attacker_won = True
                        break
                    elif a_tot == d_tot:
                        continue # Draw: รันวงจรใหม่
                    else:
                        stagger_count += 1
                        if stagger_count >= 2:
                            attacker_died = True
                            break # Stagger ครบ 2 ครั้ง ตาย(Distortion)
                
                # ✨ ส่งผลลัพธ์ลงไป
                crash_status = "died" if attacker_died else is_attacker_won
                res = self.game.move_piece(sr, sc, er, ec, resolve_crash=True, crash_won=crash_status)
            
            if res == "promote":
                from logic.pieces import Queen
                self.game.promote_pawn(er, ec, Queen)
            
            self.init_board_ui()