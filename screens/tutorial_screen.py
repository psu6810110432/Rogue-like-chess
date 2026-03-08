# screens/tutorial_screen.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color, Line
from kivy.metrics import dp
from kivy.clock import Clock
from screens.gameplay_screen import GameplayScreen
from logic.pieces import Pawn, King

class TutorialScreen(GameplayScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tutorial_step = 0
        self.instr_box = None

    def on_enter(self):
        super().setup_game(mode='TUTORIAL')
        Clock.schedule_once(self.inject_scenario, 0.25)

    def inject_scenario(self, dt):
        self.tutorial_step = 1
        self.game.board = [[None for _ in range(8)] for _ in range(8)]
        # วางหมากสำหรับ Tutorial
        white_p = Pawn('white', 'medieval'); white_p.setup_stats('pawn', 'medieval')
        # ✨ บังคับให้ Pawn ขาวมีพลัง 99 เพื่อให้ Crash ชนะแน่นอน
        white_p.base_points = 99 
        self.game.board[6][4] = white_p
        
        white_k = King('white', 'medieval'); white_k.setup_stats('king', 'medieval')
        self.game.board[7][4] = white_k
        
        black_p = Pawn('black', 'demon'); black_p.setup_stats('pawn', 'demon')
        # ✨ ลดพลัง Pawn ดำให้เหลือ 0 ทั้งหมดเพื่อให้แพ้แน่นอน
        black_p.base_points = 0
        black_p.coins = 0
        self.game.board[5][5] = black_p
        
        black_k = King('black', 'demon'); black_k.setup_stats('king', 'demon')
        self.game.board[4][4] = black_k
        
        from logic.item_logic import ITEM_DATABASE, Item
        template_item = ITEM_DATABASE[3]
        self.game.inventory_white = [Item(template_item.id, template_item.name, template_item.description, template_item.image_path)]
        self.game.current_turn = 'white'
        
        if hasattr(self, 'board_anchor'): self._keep_grid_square(self.board_anchor, self.board_anchor.size)
        self.refresh_ui()
        self.add_tutorial_overlay()
        self.update_instruction()

    def add_tutorial_overlay(self):
        if self.instr_box: self.root_layout.remove_widget(self.instr_box)
        
        # ปรับพิกัดและขนาด
        self.instr_box = BoxLayout(
            orientation='vertical', 
            size_hint=(0.55, None), 
            height=dp(85), 
            pos_hint={'center_x': 0.375, 'top': 0.95}, 
            padding=dp(10)
        )
        
        with self.instr_box.canvas.before:
            Color(0.05, 0.05, 0.1, 0.9) 
            self.overlay_bg = Rectangle(pos=self.instr_box.pos, size=self.instr_box.size)
            Color(1, 0.5, 0, 1) 
            self.overlay_border = Line(
                rectangle=(self.instr_box.x, self.instr_box.y, self.instr_box.width, self.instr_box.height), 
                width=dp(1.2)
            )
            
        self.instr_box.bind(pos=self._update_ui, size=self._update_ui)
        self.lbl = Label(text="", markup=True, font_size='16sp', halign='center', valign='middle')
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.instr_box.add_widget(self.lbl)
        self.root_layout.add_widget(self.instr_box)

    def _update_ui(self, instance, value):
        self.overlay_bg.pos, self.overlay_bg.size = instance.pos, instance.size
        self.overlay_border.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def update_instruction(self):
        steps = {
            1: "[color=ffaa00][b]STEP 1: CAPTURING[/b][/color]\nPawns capture [b]diagonally[/b]. Select your Pawn and capture the enemy at (5, 5).",
            2: "[color=ffaa00][b]STEP 2: CRASH COMBAT[/b][/color]\nWin the [b]CRASH[/b] battle to take control of the square!",
            3: "[color=ffaa00][b]STEP 3: SKILLS & ITEMS[/b][/color]\nRead unit skills in the Sidebar. Now, click the [b]Emblem[/b] in your Inventory.",
            4: "[color=ffaa00][b]STEP 4: EQUIPPING[/b][/color]\nClick on your [b]White Pawn[/b] at (5, 5) to equip the item!",
            5: "[color=ffaa00][b]STEP 5: VICTORY[/b][/color]\nFinal Task: Capture the [b]Black King[/b] at (4, 4) to win the game!", # ✨ FIX: เปลี่ยนเป็นภาษาอังกฤษเพื่อแก้บั๊กฟอนต์
            6: "[color=00ff00][b]TUTORIAL COMPLETE![/b][/color]\nYou win! Press [b]QUIT MATCH[/b] to return."
        }
        if hasattr(self, 'lbl'): self.lbl.text = steps.get(self.tutorial_step, "")

    def on_square_tap(self, instance):
        self.game.current_turn = 'white'
        r, c = instance.row, instance.col
        if self.tutorial_step == 4:
            if self.selected_item and (r, c) == (5, 5):
                super().on_square_tap(instance)
                if self.selected_item is None:
                    self.tutorial_step = 5; self.update_instruction(); self.refresh_ui()
            return
        if self.tutorial_step in [1, 2]:
            if self.selected is None:
                if (r, c) == (6, 4): super().on_square_tap(instance)
            else:
                if (r, c) == (5, 5): super().on_square_tap(instance)
                else: self.selected = None; self.refresh_ui()
            return
        if self.tutorial_step == 5:
            if self.selected is None:
                if (r, c) == (5, 5): super().on_square_tap(instance)
            else:
                if (r, c) == (4, 4): super().on_square_tap(instance)
                else: self.selected = None; self.refresh_ui()
            return
        super().on_square_tap(instance)

    def on_item_click(self, item):
        self.game.current_turn = 'white'
        super().on_item_click(item)
        if self.tutorial_step == 3 and self.selected_item:
            self.tutorial_step = 4; self.update_instruction()

    def execute_board_move(self, start, end, status):
        super().execute_board_move(start, end, status)
        self.game.current_turn = 'white'
        if self.tutorial_step == 2 and status in ["won", "died"]:
            self.tutorial_step = 3; self.update_instruction()
            p = self.game.board[end[0]][end[1]]
            if p: self.show_piece_status(p)
        if self.game.game_result and "WHITE WINS" in self.game.game_result.upper():
            self.tutorial_step = 6; self.update_instruction()
        self.refresh_ui()

    def show_crash_overlay(self, attacker, defender, start, end):
        if self.tutorial_step == 1: self.tutorial_step = 2; self.update_instruction()
        super().show_crash_overlay(attacker, defender, start, end)

    def on_quit(self):
        if self.instr_box: self.root_layout.remove_widget(self.instr_box); self.instr_box = None
        super().on_quit()