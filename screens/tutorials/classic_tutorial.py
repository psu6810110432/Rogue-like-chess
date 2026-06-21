# screens/tutorials/classic_tutorial.py
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

class ClassicTutorial:
    def __init__(self, screen):
        self.screen = screen
        self.current_step = 0
        self.steps = [
            self.run_step1,        # 0
            self.run_step2_intro,  # 1
            self.run_step3,        # 2
            self.run_step4,        # 3
            self.run_step5_intro,  # 4
            self.run_step6,        # 5
            self.run_step7,        # 6
        ]

    def start(self):
        app = App.get_running_app()
        app.selected_unit_white = 'Medieval Knights'
        app.selected_unit_black = 'Demon'

        self.current_step = 0
        self.screen.tut_state = 'step1'
        Clock.schedule_once(lambda dt: self.run_step1(), 0.5)

    def cleanup(self):
        """Reset transient state before replaying a step."""
        self.screen.selected = None
        self.screen.valid_moves = []
        self.screen.set_board()

    def go_back(self):
        """Go to the previous step."""
        if self.current_step <= 0:
            return
        self.current_step -= 1
        self.cleanup()
        self.steps[self.current_step]()

    def run_step1(self):
        self.current_step = 0
        self.screen.tut_state = 'step1'
        self.screen.show_retreat_button(self.current_step)
        txt = ("All pieces move exactly like traditional chess.\n"
               "(Pawns move 2 squares on their first move, then 1 square forward).")
        self.screen.show_popup("STEP 1: MOVEMENT", txt, self.run_step2_intro, show_pieces=True)

    def run_step2_intro(self):
        self.current_step = 1
        self.screen.show_retreat_button(self.current_step)
        txt = ("[b]Base Points + Coin Tosses[/b] decide the winner!\n\n"
               "[color=00ff00]Breaking[/color]: You Win.\n"
               "[color=ffff00]Draw[/color]: Tie, reroll.\n"
               "[color=ffaa00]Stagger[/color]: Warning for ATK, reroll.\n"
               "[color=ff0000]Distortion[/color]: ATK loses & dies.")
        self.screen.show_popup("STEP 2: CRASH COMBAT", txt, self.setup_pair1, btn_align='right')

    def setup_pair1(self):
        self.screen.tut_state = 'pair1'
        self.screen.set_board()
        self.screen.game.board[5][4] = self.screen._create_dummy(Pawn, 'white', 'the knight company')
        self.screen.game.board[4][3] = self.screen._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.screen.game.current_turn = 'white'
        self.screen.refresh_ui()

    def setup_pair2(self):
        self.screen.tut_state = 'pair2_draw'
        self.screen.set_board()
        self.screen.game.board[5][4] = self.screen._create_dummy(Pawn, 'white', 'the knight company')
        self.screen.game.board[4][3] = self.screen._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.screen.game.current_turn = 'white'
        self.screen.refresh_ui()

    def run_step3(self):
        self.current_step = 2
        self.screen.show_retreat_button(self.current_step)
        txt = "ROGuelike Chess features 4 unique Legions:"
        self.screen.show_popup("STEP 3: LEGIONS", txt, self.run_step4, show_kings=True)

    def run_step4(self):
        self.current_step = 3
        self.screen.show_retreat_button(self.current_step)
        txt = ("Every Legion has its own unique Passive skills, and each piece has a chance to get a 'Hidden Passive' (bonus or penalty in points/coins).\n\n"
               "You can read more in the 'Making Match' screen by clicking '?' behind 'Choose your Legion'.")
        self.screen.show_popup("STEP 4: PASSIVES", txt, self.run_step5_intro)

    def run_step5_intro(self):
        self.current_step = 4
        self.screen.show_retreat_button(self.current_step)
        txt = ("Items drop when you Win a Crash as an Attacker using a Knight, Bishop, or Rook. (No items if you win as Defender).\n\n"
               "There are 4 types: Universal, Specific, Permanent, and Consumable.")
        self.screen.show_popup("STEP 5: ITEMS", txt, self.setup_step5_attack1, show_droppers=True)

    def setup_step5_attack1(self):
        self.screen.tut_state = 'step5_attack1'
        self.screen.set_board()
        self.screen.game.board[5][4] = self.screen._create_dummy(Knight, 'white', 'the knight company')
        self.screen.game.board[3][5] = self.screen._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.screen.game.current_turn = 'white'
        self.screen.refresh_ui()

    def setup_step5_equip(self):
        self.screen.tut_state = 'step5_equip'
        
        # ✨ รีเซ็ตกระดานกลับมาจุดเริ่มต้นของ Step 5 
        self.screen.set_board()
        self.screen.game.board[5][4] = self.screen._create_dummy(Knight, 'white', 'the knight company')
        self.screen.game.board[3][5] = self.screen._create_dummy(Pawn, 'black', 'the chaos mankind')
        self.screen.game.current_turn = 'white'
        self.screen.refresh_ui()

        txt = ("You obtained a [color=ff0000]Bloodlust Emblem[/color]!\n"
               "Effect: Gain +5 Base Points upon winning a Crash. (Consumable)\n\n"
               "Please equip it to your Knight by clicking the item in your inventory, then clicking the Knight.")
        self.screen.show_popup("ITEM DROP", txt, item_img="assets/item/item3.png")

    def setup_step5_attack2(self):
        self.screen.tut_state = 'step5_attack2'
        # ✨ ไม่ต้องเสกศัตรูใหม่แล้ว ปล่อยให้ผู้เล่นโจมตีตัวที่รีเซ็ตกลับมาได้เลย
        self.screen.refresh_ui()

    def run_step6(self):
        self.current_step = 5
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=ffcc00]Classic:[/color] Standard chess board.\n"
               "[color=00ff44]Enchanted Forest:[/color] Thorny vines may block squares (3 turns).\n"
               "[color=ffaa00]Desert Ruins:[/color] Empty rows/cols may spawn Sandstorms (3 turns).\n"
               "[color=00ccff]Frozen Tundra:[/color] Every 3 turns, 2 random pieces freeze. Ice blocks may also appear.")
        self.screen.show_popup("STEP 6: BATTLEFIELDS", txt, self.run_step7)

    def run_step7(self):
        self.current_step = 6
        self.screen.show_retreat_button(self.current_step)
        txt = ("There are 2 ways to win:\n"
               "1. Standard Checkmate.\n"
               "2. Corner the enemy King so it's forced to Crash with your pieces and lose!")
        def finish():
            self.screen.hide_retreat_button()
            self.screen.manager.current = 'main_menu'
        self.screen.show_popup("STEP 7: VICTORY & DEFEAT", txt, finish)

    def handle_crash_result(self, real_status):
        if real_status in ['won', 'died']:
            if self.screen.tut_state == 'pair1':
                self.screen.show_popup("BREAKING!", "When your total is higher, you WIN and capture the piece!", self.setup_pair2)
            elif self.screen.tut_state == 'pair2_distortion':
                self.screen.show_popup("DISTORTION!", "If you lose again after a Stagger, you suffer DISTORTION. Your piece is destroyed!", self.run_step3)
            elif self.screen.tut_state == 'step5_attack1':
                template = ITEM_DATABASE[3]
                self.screen.game.inventory_white.append(Item(template.id, template.name, template.description, template.image_path))
                self.screen.update_inventory_ui()
                self.setup_step5_equip()
            elif self.screen.tut_state == 'step5_attack2':
                self.screen.show_popup("GREAT JOB!", "You've mastered items and combat.", self.run_step6)
        elif real_status == 'draw':
            self.screen.show_popup("DRAW!", "When totals are equal, it's a DRAW.\nThe system will reroll until there's a winner.", self.trigger_stagger)
        elif real_status == 'stagger':
            self.screen.show_popup("STAGGER!", "If your total is lower on the first try, you get a STAGGER.\nIt's a warning before death. The system will reroll.", self.trigger_distortion)

    def trigger_stagger(self):
        self.screen.tut_state = 'pair2_stagger'
        self.screen.show_crash_overlay(self.screen.game.board[5][4], self.screen.game.board[4][3], (5,4), (4,3))

    def trigger_distortion(self):
        self.screen.tut_state = 'pair2_distortion'
        self.screen.show_crash_overlay(self.screen.game.board[5][4], self.screen.game.board[4][3], (5,4), (4,3))