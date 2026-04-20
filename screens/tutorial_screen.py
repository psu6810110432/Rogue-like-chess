# screens/tutorial_screen.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.graphics import Rectangle, Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.app import App

from screens.gameplay_screen import GameplayScreen
from logic.pieces import Pawn, Knight, Bishop, Rook, Queen, King
from logic.item_logic import ITEM_DATABASE, Item

# ✨ Tutorial Popup Window
class TutPopup(ModalView):
    def __init__(self, title, text, on_next, show_pieces=False, show_kings=False, item_img=None, show_droppers=False, btn_align='right', **kwargs):
        super().__init__(size_hint=(0.7, 0.6), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.6, 0.2, 1)
            self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=1.5)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='22sp', color=(1, 0.8, 0.2, 1), size_hint_y=0.2))
        
        content_box = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=dp(10))
        
        # แสดงหมากจำลอง (Step 1) พร้อมชื่อ
        if show_pieces:
            board_sim = GridLayout(cols=3, spacing=2, size_hint_y=None, height=dp(150))
            for i, p in enumerate(['pawn1', 'rook', 'knight', 'bishop', 'queen', 'king']):
                display_name = 'pawn' if 'pawn' in p else p
                bg_color = (0.7, 0.6, 0.5, 1) if i % 2 == 0 else (0.4, 0.3, 0.2, 1)
                
                cell = BoxLayout(orientation='vertical', padding=5)
                with cell.canvas.before:
                    Color(*bg_color)
                    self.rect = Rectangle(pos=cell.pos, size=cell.size)
                def update_rect(instance, value, rect=self.rect):
                    rect.pos = instance.pos
                    rect.size = instance.size
                cell.bind(pos=update_rect, size=update_rect)
                
                # ✨ แก้ไข Path ของหมาก
                cell.add_widget(Image(source=f"assets/pieces/the knight company/white/1base/{p}.png", allow_stretch=True, keep_ratio=True, size_hint_y=0.75))
                cell.add_widget(Label(text=f"[b]{display_name.upper()}[/b]", markup=True, font_size='11sp', color=(1, 1, 1, 1), size_hint_y=0.25))
                board_sim.add_widget(cell)
            content_box.add_widget(board_sim)
            
        if show_kings:
            grid = GridLayout(cols=4, spacing=5, size_hint_y=None, height=dp(100))
            # ✨ แก้ไขรายชื่อเผ่า
            for f in ['the knight company', 'the chaos mankind', 'the deep anomaly', 'the ancient runes']:
                grid.add_widget(Image(source=f"assets/pieces/{f}/white/1base/king.png", allow_stretch=True, keep_ratio=True))
            content_box.add_widget(grid)

        # โชว์ภาพ Knight, Bishop, Rook พร้อมชื่อ (Step 5)
        if show_droppers:
            grid = GridLayout(cols=3, spacing=10, size_hint_y=None, height=dp(100))
            droppers = [('knight', 'KNIGHT'), ('bishop', 'BISHOP'), ('rook', 'ROOK')]
            for filename, name in droppers: 
                box = BoxLayout(orientation='vertical')
                # ✨ แก้ไข Path
                box.add_widget(Image(source=f"assets/pieces/the knight company/white/1base/{filename}.png", allow_stretch=True, keep_ratio=True, size_hint_y=0.75))
                box.add_widget(Label(text=f"[b]{name}[/b]", markup=True, font_size='13sp', color=(0.8, 0.8, 0.8, 1), size_hint_y=0.25))
                grid.add_widget(box)
            content_box.add_widget(grid)
            
        # แสดงรูปไอเทมถ้ามีส่งเข้ามา
        if item_img:
            content_box.add_widget(Image(source=item_img, size_hint_y=None, height=dp(80), allow_stretch=True, keep_ratio=True))

        lbl = Label(text=text, markup=True, font_size='15sp', halign='center', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        content_box.add_widget(lbl)
        root.add_widget(content_box)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        next_btn = Button(text="[b]NEXT[/b]", markup=True, size_hint_x=0.4, background_color=(0.2, 0.6, 0.2, 1))
        
        def _on_next(*args):
            App.get_running_app().play_click_sound()
            self.dismiss()
            if on_next: on_next()
        next_btn.bind(on_release=_on_next)

        if btn_align == 'right':
            btn_box.add_widget(Label(size_hint_x=0.6))
            btn_box.add_widget(next_btn)
        else:
            btn_box.add_widget(next_btn)
            btn_box.add_widget(Label(size_hint_x=0.6))
            
        root.add_widget(btn_box)
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]


# ✨ MOCK CRASH POPUP 
class MockCrashPopup(ModalView):
    def __init__(self, atk_img, def_img, atk_b, atk_c_list, atk_s, def_b, def_c_list, def_s, res_text, res_color, on_next, **kwargs):
        super().__init__(size_hint=(0.7, 0.6), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.15, 0.15, 0.2, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(*res_color)
            self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=2.5)
        root.bind(pos=self._update_bg, size=self._update_bg)
        
        root.add_widget(Label(text="[b]CRASH PHASE[/b]", markup=True, font_size='22sp', size_hint_y=0.15, color=(1,1,1,1)))
        
        vs_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.55)
        
        # --- Helper Function for Coin UI ---
        def create_coin_row(coin_type):
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(5))
            if coin_type == 'heads':
                # ใช้ coin8.png สำหรับเหรียญหัวสีฟ้า
                box.add_widget(Image(source='assets/coin/coin8.png', size_hint_x=0.4))
                lbl = Label(text="[color=00ffff]+10[/color]", markup=True, bold=True, size_hint_x=0.6)
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)
            else:
                # ใช้ coin2.png สำหรับเหรียญก้อย
                box.add_widget(Image(source='assets/coin/coin2.png', size_hint_x=0.4))
                lbl = Label(text="[color=aaaaaa]+0[/color]", markup=True, bold=True, size_hint_x=0.6)
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)
            return box

        # --- Attacker Box ---
        atk_box = BoxLayout(orientation='vertical', spacing=dp(5))
        atk_box.add_widget(Image(source=atk_img, allow_stretch=True, keep_ratio=True, size_hint_y=0.4))
        atk_box.add_widget(Label(text=f"[b]Base: {atk_b}[/b]", markup=True, font_size='16sp', size_hint_y=0.15))
        
        atk_coins_box = BoxLayout(orientation='vertical', size_hint_y=0.25)
        for c in atk_c_list:
            atk_coins_box.add_widget(create_coin_row(c))
        atk_box.add_widget(atk_coins_box)
        atk_box.add_widget(Label(text=f"Total: {atk_s}", font_size='20sp', bold=True, color=(0.4, 0.8, 1, 1), size_hint_y=0.2))
        vs_box.add_widget(atk_box)
        
        # --- VS Center ---
        vs_box.add_widget(Label(text="VS", font_size='26sp', bold=True, size_hint_x=0.2, color=(1, 0.8, 0, 1)))
        
        # --- Defender Box ---
        def_box = BoxLayout(orientation='vertical', spacing=dp(5))
        def_box.add_widget(Image(source=def_img, allow_stretch=True, keep_ratio=True, size_hint_y=0.4))
        def_box.add_widget(Label(text=f"[b]Base: {def_b}[/b]", markup=True, font_size='16sp', size_hint_y=0.15))
        
        def_coins_box = BoxLayout(orientation='vertical', size_hint_y=0.25)
        for c in def_c_list:
            def_coins_box.add_widget(create_coin_row(c))
        def_box.add_widget(def_coins_box)
        def_box.add_widget(Label(text=f"Total: {def_s}", font_size='20sp', bold=True, color=(1, 0.4, 0.4, 1), size_hint_y=0.2))
        vs_box.add_widget(def_box)
        
        root.add_widget(vs_box)
        
        # --- Result Bottom ---
        root.add_widget(Label(text=f"[b]{res_text}[/b]", markup=True, font_size='26sp', color=res_color, size_hint_y=0.15))
        
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        btn_box.add_widget(Label(size_hint_x=0.6)) 
        btn = Button(text="[b]NEXT[/b]", markup=True, size_hint_x=0.4, background_color=(0.2, 0.6, 0.2, 1))
        def _on_next(*a):
            App.get_running_app().play_click_sound()
            self.dismiss()
            if on_next: on_next()
        btn.bind(on_release=_on_next)
        btn_box.add_widget(btn)
        
        root.add_widget(btn_box)
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]


class TutorialScreen(GameplayScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tut_state = ''

    def on_enter(self):
        super().setup_game(mode='TUTORIAL')
        self.game.current_turn = 'white'
        self.tut_state = 'step1'
        Clock.schedule_once(lambda dt: self.run_step1(), 0.5)

    def show_popup(self, title, text, on_next=None, show_pieces=False, show_kings=False, item_img=None, show_droppers=False, btn_align='right'):
        TutPopup(title, text, on_next, show_pieces, show_kings, item_img, show_droppers, btn_align).open()
        
    def _create_dummy(self, cls, color, faction):
        p = cls(color, faction)
        p.base_points, p.coins = 5, 1
        p.hidden_passive.apply_passive = lambda d, c: (d, c)
        return p

    def set_board(self):
        self.game.board = [[None for _ in range(8)] for _ in range(8)]
        # ✨ อัปเดตเผ่าเริ่มต้นให้ King
        self.game.board[0][0] = self._create_dummy(King, 'white', 'the knight company')
        self.game.board[7][7] = self._create_dummy(King, 'black', 'the chaos mankind')
        
        if hasattr(self, 'board_anchor'): self._keep_grid_square(self.board_anchor, self.board_anchor.size)
        self.refresh_ui()

    def check_winner(self): pass
    def check_game_over(self): pass
    def end_game(self, *args, **kwargs): pass

    def run_step1(self):
        txt = ("All pieces move exactly like traditional chess.\n"
               "(Pawns move 2 squares on their first move, then 1 square forward).")
        self.show_popup("STEP 1: MOVEMENT", txt, self.run_step2_intro, show_pieces=True)

    def run_step2_intro(self):
        txt = ("[b]Base Points + Coin Tosses[/b] decide the winner!\n\n"
               "[color=00ff00]Breaking[/color]: You Win.\n"
               "[color=ffff00]Draw[/color]: Tie, reroll.\n"
               "[color=ffaa00]Stagger[/color]: Warning for ATK, reroll.\n"
               "[color=ff0000]Distortion[/color]: ATK loses & dies.")
        self.show_popup("STEP 2: CRASH COMBAT", txt, self.setup_pair1, btn_align='right')

    def setup_pair1(self):
        self.tut_state = 'pair1'
        self.set_board()
        # ✨ อัปเดตชื่อเผ่า
        self.game.board[5][4] = self._create_dummy(Pawn, 'white', 'the knight company')
        self.game.board[4][3] = self._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.game.current_turn = 'white'
        self.refresh_ui()

    def setup_pair2(self):
        self.tut_state = 'pair2_draw'
        self.set_board()
        # ✨ อัปเดตชื่อเผ่า
        self.game.board[5][4] = self._create_dummy(Pawn, 'white', 'the knight company')
        self.game.board[4][3] = self._create_dummy(Pawn, 'black', 'the knight company')
        self.game.current_turn = 'white'
        self.refresh_ui()

    def run_step3(self):
        txt = "ROGuelike Chess features 4 unique Legions:"
        self.show_popup("STEP 3: LEGIONS", txt, self.run_step4, show_kings=True)

    def run_step4(self):
        txt = ("Every Legion has its own unique Passive skills, and each piece has a chance to get a 'Hidden Passive' (bonus or penalty in points/coins).\n\n"
               "You can read more in the 'Making Match' screen by clicking '?' behind 'Choose your Legion'.")
        self.show_popup("STEP 4: PASSIVES", txt, self.run_step5_intro)

    def run_step5_intro(self):
        txt = ("Items drop when you Win a Crash as an Attacker using a Knight, Bishop, or Rook. (No items if you win as Defender).\n\n"
               "There are 4 types: Universal, Specific, Permanent, and Consumable.")
        self.show_popup("STEP 5: ITEMS", txt, self.setup_step5_attack1, show_droppers=True)

    def setup_step5_attack1(self):
        self.tut_state = 'step5_attack1'
        self.set_board()
        # ✨ อัปเดตชื่อเผ่า
        self.game.board[5][4] = self._create_dummy(Knight, 'white', 'the knight company')
        self.game.board[3][5] = self._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.game.current_turn = 'white'
        self.refresh_ui()

    def setup_step5_equip(self):
        self.tut_state = 'step5_equip'
        txt = ("You obtained a [color=ff0000]Bloodlust Emblem[/color]!\n"
               "Effect: Gain +5 Base Points upon winning a Crash. (Consumable)\n\n"
               "Please equip it to your Knight by clicking the item in your inventory, then clicking the Knight.")
        self.show_popup("ITEM DROP", txt, item_img="assets/item/item3.png")

    def setup_step5_attack2(self):
        self.tut_state = 'step5_attack2'
        # ✨ อัปเดตชื่อเผ่า
        self.game.board[3][5] = self._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.refresh_ui()

    def run_step6(self):
        txt = ("[color=ffcc00]Classic:[/color] Standard chess board.\n"
               "[color=00ff44]Enchanted Forest:[/color] Thorny vines may block squares (3 turns).\n"
               "[color=ffaa00]Desert Ruins:[/color] Empty rows/cols may spawn Sandstorms (3 turns).\n"
               "[color=00ccff]Frozen Tundra:[/color] Every 3 turns, 2 random pieces freeze. Ice blocks may also appear.")
        self.show_popup("STEP 6: BATTLEFIELDS", txt, self.run_step7)

    def run_step7(self):
        txt = ("There are 2 ways to win:\n"
               "1. Standard Checkmate.\n"
               "2. Corner the enemy King so it's forced to Crash with your pieces and lose!")
        def finish():
            self.manager.current = 'main_menu'
        
        self.show_popup("STEP 7: VICTORY & DEFEAT", txt, finish)

    def show_crash_overlay(self, attacker, defender, start, end):
        App.get_running_app().play_coin_sound()
        atk_img = self.get_piece_image_path(attacker)
        def_img = self.get_piece_image_path(defender)

        if self.tut_state == 'pair1':
            ab, ac, a_s = 5, ['heads'], 15
            db, dc, d_s = 5, ['tails'], 5
            res, color, real_status = "BREAKING", (0,1,0,1), 'won'
        elif self.tut_state == 'pair2_draw':
            ab, ac, a_s = 5, ['heads'], 15
            db, dc, d_s = 5, ['heads'], 15
            res, color, real_status = "DRAW", (1,1,0,1), 'draw'
        elif self.tut_state == 'pair2_stagger':
            ab, ac, a_s = 5, ['tails'], 5
            db, dc, d_s = 5, ['heads'], 15
            res, color, real_status = "STAGGER", (1,0.5,0,1), 'stagger'
        elif self.tut_state == 'pair2_distortion':
            ab, ac, a_s = 5, ['tails'], 5
            db, dc, d_s = 5, ['heads'], 15
            res, color, real_status = "DISTORTION", (1,0,0,1), 'died'
        elif self.tut_state == 'step5_attack1':
            ab, ac, a_s = 5, ['heads'], 15
            db, dc, d_s = 5, ['tails'], 5
            res, color, real_status = "BREAKING", (0,1,0,1), 'won'
        elif self.tut_state == 'step5_attack2':
            ab, ac, a_s = 10, ['heads'], 20
            db, dc, d_s = 5, ['tails'], 5
            res, color, real_status = "BREAKING", (0,1,0,1), 'won'
        else:
            ab, ac, a_s = 5, ['tails'], 5
            db, dc, d_s = 5, ['tails'], 5
            res, color, real_status = "DRAW", (1,1,0,1), 'draw'

        def on_close():
            self.selected = None
            self.valid_moves = []
            self.game.current_turn = 'white' 
            self.refresh_ui()

            if real_status in ['won', 'died']:
                if self.tut_state == 'pair1':
                    self.show_popup("BREAKING!", "When your total is higher, you WIN and capture the piece!", self.setup_pair2)
                elif self.tut_state == 'pair2_distortion':
                    self.show_popup("DISTORTION!", "If you lose again after a Stagger, you suffer DISTORTION. Your piece is destroyed!", self.run_step3)
                elif self.tut_state == 'step5_attack1':
                    template = ITEM_DATABASE[3]
                    self.game.inventory_white.append(Item(template.id, template.name, template.description, template.image_path))
                    self.update_inventory_ui()
                    self.setup_step5_equip()
                elif self.tut_state == 'step5_attack2':
                    self.show_popup("GREAT JOB!", "You've mastered items and combat.", self.run_step6)

            elif real_status == 'draw':
                self.show_popup("DRAW!", "When totals are equal, it's a DRAW.\nThe system will reroll until there's a winner.", self.trigger_stagger)
            elif real_status == 'stagger':
                self.show_popup("STAGGER!", "If your total is lower on the first try, you get a STAGGER.\nIt's a warning before death. The system will reroll.", self.trigger_distortion)

        MockCrashPopup(atk_img, def_img, ab, ac, a_s, db, dc, d_s, res, color, on_close).open()

    def trigger_stagger(self):
        self.tut_state = 'pair2_stagger'
        self.show_crash_overlay(self.game.board[5][4], self.game.board[4][3], (5,4), (4,3))

    def trigger_distortion(self):
        self.tut_state = 'pair2_distortion'
        self.show_crash_overlay(self.game.board[5][4], self.game.board[4][3], (5,4), (4,3))

    def on_square_tap(self, instance):
        r, c = instance.row, instance.col
        
        if self.tut_state == 'pair1':
            if not ((r==5 and c==4) or (self.selected==(5,4) and r==4 and c==3)): return
        elif self.tut_state in ['pair2_draw', 'pair2_stagger', 'pair2_distortion']:
            if not ((r==5 and c==4) or (self.selected==(5,4) and r==4 and c==3)): return
        elif self.tut_state == 'step5_attack1':
            if not ((r==5 and c==4) or (self.selected==(5,4) and r==3 and c==5)): return
        elif self.tut_state == 'step5_equip':
            if not self.selected_item and not (r==5 and c==4): return
        elif self.tut_state == 'step5_attack2':
            if not ((r==5 and c==4) or (self.selected==(5,4) and r==3 and c==5)): return
            
        super().on_square_tap(instance)
        
        if self.tut_state == 'step5_equip' and self.selected_item is None:
            piece = self.game.board[5][4]
            if piece and getattr(piece, 'item', None) is not None:
                self.setup_step5_attack2()