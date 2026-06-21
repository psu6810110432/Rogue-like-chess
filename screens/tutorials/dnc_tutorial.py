# screens/tutorials/dnc_tutorial.py
import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Rectangle, Color
from kivy.metrics import dp
from kivy.app import App
from kivy.uix.widget import Widget

from logic.pieces import Pawn, Praetorian, Royalguard, Menatarm, Hastati, Levies, Prince, Princess, King
from components.map_node import MapNode
from components.campaign_cards import RecruitCard
from components.campaign_popups import TechCard, BuildCard

class DNCTutorial:
    def __init__(self, screen):
        self.screen = screen
        self.current_step = 0
        self.steps = [
            self.run_dnc_step1,  # 0
            self.run_dnc_step2,  # 1
            self.run_dnc_step3,  # 2
            self.run_dnc_step4,  # 3
            self.run_dnc_step5,  # 4
            self.run_dnc_step6,  # 5
            self.run_dnc_step7,  # 6
            self.run_dnc_step8,  # 7
            self.run_dnc_step9,  # 8
        ]

    def start(self):
        app = App.get_running_app()
        app.selected_unit_white = 'Medieval Knights'
        app.selected_unit_black = 'Demon'
        
        self.current_step = 0
        self.screen.tut_state = 'dnc_step1'
        self.run_dnc_step1()

    def cleanup(self):
        """Remove all transient tutorial widgets before replaying a step."""
        screen = self.screen
        # Remove mock map layer
        if hasattr(screen, 'mock_map_layer') and screen.mock_map_layer and screen.mock_map_layer.parent:
            screen.root_layout.remove_widget(screen.mock_map_layer)
            screen.mock_map_layer = None
        screen.mock_castles = []
        screen.mock_villages = []
        # Remove tutorial action button from sidebar (covers board-phase buttons)
        if hasattr(screen, 'sidebar') and screen.sidebar:
            screen.sidebar.hide_tutorial_action_btn()
        # Remove floating next_step_btn (for map steps)
        if hasattr(screen, 'next_step_btn') and screen.next_step_btn and screen.next_step_btn.parent:
            screen.next_step_btn.parent.remove_widget(screen.next_step_btn)
            screen.next_step_btn = None
        # Remove black mask
        if hasattr(self, 'black_mask') and self.black_mask and self.black_mask.parent:
            screen.root_layout.remove_widget(self.black_mask)
            self.black_mask = None
        # Restore play area
        if hasattr(screen, 'play_area'):
            screen.play_area.opacity = 1
        # Reset board
        screen.is_input_locked = False
        screen.game.board = [[None for _ in range(8)] for _ in range(8)]
        if hasattr(screen, 'board_anchor'):
            screen._keep_grid_square(screen.board_anchor, screen.board_anchor.size)
        screen.refresh_ui()

    def go_back(self):
        """Go to the previous step."""
        if self.current_step <= 0:
            return
        self.current_step -= 1
        self.cleanup()
        self.steps[self.current_step]()

    def _ensure_mock_map(self):
        """Ensure the mock map layer and base nodes exist (recreate after cleanup)."""
        screen = self.screen
        if hasattr(screen, 'play_area'):
            screen.play_area.opacity = 0
        if not hasattr(screen, 'mock_map_layer') or not screen.mock_map_layer or not screen.mock_map_layer.parent:
            screen.mock_map_layer = FloatLayout()
            with screen.mock_map_layer.canvas.before:
                Color(0.12, 0.18, 0.12, 1)
                Rectangle(pos=(0, 0), size=(9600, 5400))
            screen.root_layout.add_widget(screen.mock_map_layer)
        if not hasattr(screen, 'mock_castles') or not screen.mock_castles:
            cx = screen.width / 2
            cy = screen.height / 2
            screen.mock_castles = []
            for i in range(3):
                c = MapNode('castle', 'white', f'C{i+1}', app=None)
                c.on_release = lambda: None
                c.pos = (cx - dp(400) + (i * dp(400)) - dp(35), cy + dp(100))
                c.addons = {}
                c.sub_villages = []
                c.update_graphics()
                screen.mock_map_layer.add_widget(c)
                screen.mock_castles.append(c)
            screen.mock_villages = []
            for i in range(6):
                v = MapNode('village', 'white', f'V{i+1}', app=None)
                v.on_release = lambda: None
                v.pos = (cx - dp(500) + (i * dp(200)) - dp(35), cy - dp(150))
                v.addons = {}
                v.update_graphics()
                screen.mock_map_layer.add_widget(v)
                screen.mock_villages.append(v)

    def run_dnc_step1(self):
        self.current_step = 0
        self.screen.tut_state = 'dnc_step1'
        self.screen.show_retreat_button(self.current_step)
        
        if hasattr(self.screen, 'play_area'):
            self.screen.play_area.opacity = 0
            
        self.screen.mock_map_layer = FloatLayout()
        with self.screen.mock_map_layer.canvas.before:
            Color(0.12, 0.18, 0.12, 1)
            Rectangle(pos=(0, 0), size=(9600, 5400))
        self.screen.root_layout.add_widget(self.screen.mock_map_layer)
        
        txt = ("Welcome to [b]Divide and Conquer[/b]!\n\n"
               "The world is generated with bases you must capture to earn [color=00ff00]Tax[/color] points.\n"
               "There are 2 main types of bases:\n"
               "1. Villages\n"
               "2. Castles")
        
        self.screen.show_popup("STEP 1: WORLD GENERATION", txt, self.draw_step2_and_wait)

    def draw_step2_and_wait(self):
        self._ensure_mock_map()
        self.screen.show_next_step_button(self.run_dnc_step2)

    def run_dnc_step2(self):
        self.current_step = 1
        self.screen.tut_state = 'dnc_step2'
        self.screen.show_retreat_button(self.current_step)
        txt = ("Villages have 3 building paths. 2 are guaranteed (Farm, Tavern), and 1 is a random Special building.\n\n"
               "[b]Farm[/b]: Generates Tax income.\n"
               "[b]Tavern[/b]: Recruits units (Row 1-2: Militia like Pawn, Levies. Row 3: Regular like Hastati).\n\n"
               "[b]Special Building (Random)[/b]:\n"
               "- [color=ffaa00]Mine (20%)[/color]: +3 Tax\n"
               "- [color=aaaaff]Blacksmith (15%)[/color]: +1 Base DEF to recruits\n"
               "- [color=ff5555]Weaponsmith (15%)[/color]: +1 Base ATK to recruits\n"
               "- [color=55ff55]Guard (15%)[/color]: Spawns defensive units during attacks\n"
               "- [color=ffff55]Statue (15%)[/color]: Reduces recruit costs (Max 50%)\n"
               "- None (50%)")
        self.screen.show_popup("STEP 2: VILLAGES", txt, self.draw_step3_and_wait)
        
    def draw_step3_and_wait(self):
        self._ensure_mock_map()
        specials = ['mine', 'blacksmith', 'weaponsmith', 'guard', 'statue', None]
        for i, v in enumerate(self.screen.mock_villages):
            v.addons = {
                'farm': 1,
                'tavern': 1,
                'special': specials[i],
                'special_lvl': 1
            }
            v.update_graphics()
            
        self.screen.show_next_step_button(self.run_dnc_step3)

    def run_dnc_step3(self):
        self.current_step = 2
        self.screen.tut_state = 'dnc_step3'
        self.screen.show_retreat_button(self.current_step)
        txt = ("Castles are massive fortresses containing 1 to 3 [color=ffaa00]Sub-Villages[/color].\n"
               "Sub-villages cannot be attacked directly; they are part of the Castle.\n\n"
               "A Castle's Tavern is superior, offering 5 rows of units:\n"
               "Row 1: Militia\n"
               "Row 2-3: Regulars\n"
               "Row 4-5: Veterans & Elites (Praetorian, Royalguard)\n\n"
               "You can view sub-village recruits from the Castle's menu.")
        self.screen.show_popup("STEP 3: CASTLES", txt, self.draw_step4_and_wait)

    def draw_step4_and_wait(self):
        self._ensure_mock_map()
        for i, c in enumerate(self.screen.mock_castles):
            num_subs = i + 1 
            c.sub_villages = []
            angles = [30, 150, 270]
            for j in range(num_subs):
                angle = math.radians(angles[j])
                dist = dp(110)
                c.sub_villages.append({
                    'id': f"V{j+1}",
                    'rel_pos': (math.cos(angle) * dist, math.sin(angle) * dist),
                    'addons': {'farm': 1, 'tavern': 1, 'special': None, 'special_lvl': 1}
                })
            c.update_graphics()
            
        self.screen.show_next_step_button(self.run_dnc_step4)

    def run_dnc_step4(self):
        self.current_step = 3
        self.screen.tut_state = 'dnc_step4'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=00ff00]Tax and Upgrades[/color]\n\n"
               "[b]Tax[/b] is earned on Next Turn. A Level 1 Farm gives 2 Tax, and adds +2 per level. You can read more about reducing costs and increasing tax in the '?' menu during Match Setup.\n\n"
               "[b]Upgrades[/b] are split into 2 main types:\n"
               "1. [color=00ffff]Unit Upgrade[/color]: Increases Base ATK/DEF. Some units have special upgrade paths.\n"
               "2. [color=ffaa00]Building Upgrade[/color]: Increases stats and benefits of structures.")
        
        main_box = BoxLayout(orientation='horizontal', spacing=dp(20), size_hint_y=None, height=dp(250))
        
        unit_box = BoxLayout(orientation='vertical', spacing=dp(5))
        unit_box.add_widget(Label(text="[b]1. Unit Upgrade[/b]", markup=True, size_hint_y=None, height=dp(30)))
        tc = TechCard("Rank I", "+2 Base ATK", 4, 2, 1, "assets/pieces/the knight company/white/2upATK/pawn1.png", True, False, None)
        unit_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        unit_anchor.add_widget(tc)
        unit_box.add_widget(unit_anchor)
        
        build_box = BoxLayout(orientation='vertical', spacing=dp(5))
        build_box.add_widget(Label(text="[b]2. Building Upgrade[/b]", markup=True, size_hint_y=None, height=dp(30)))
        bc = BuildCard("Farm", "Lvl 1 -> 2\n(+2 Tax)", 5, "assets/structure/addon/base1/farm.png", lambda: None)
        build_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        build_anchor.add_widget(bc)
        build_box.add_widget(build_anchor)
        
        main_box.add_widget(unit_box)
        main_box.add_widget(build_box)

        self.screen.show_popup("STEP 4: TAX & UPGRADES", txt, self.run_dnc_step5, custom_widget=main_box)

    def run_dnc_step5(self):
        self.current_step = 4
        self.screen.tut_state = 'dnc_step5'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=00ffff]New Units & Exclusives[/color]\n\n"
               "- [b]Praetorian[/b]: Attacking crash wins grant +1 ATK/DEF (Max 5). Buffs last 6 turns.\n"
               "- [b]Royalguard[/b]: ANY crash win grants a permanent +1 ATK or DEF (Max 8).\n"
               "- [b]Menatarm[/b]: Standing still builds Charge Stacks (Max 3). At 3 stacks, next attack grants bonus coins (+50% of current coins).\n"
               "- [b]Hastati[/b]: Standing still builds Defense Stacks (+1 DEF/turn, Max 5). Moving resets it.\n"
               "- [b]Levies[/b]: If a Prince leads the army, Levies promote to Princess, Knight, Bishop, or Rook. If led by King, they promote to Pawn, and Princess becomes Queen.\n"
               "[color=ff5555]*Note: These special units CANNOT obtain items from Crash Wins.*[/color]\n\n"
               "[b]Prince & Princess[/b]: Cannot be recruited in the Tavern. Prince is earned by capturing Castles. Princess is obtained via Levies promotion (when led by Prince).")
        
        pieces_to_show = [Praetorian, Royalguard, Menatarm, Hastati, Levies, Prince, Princess]
        self.step5_grid = GridLayout(cols=4, spacing=10, size_hint_y=None, height=dp(150))
        for cls in pieces_to_show:
            p = self.screen._create_dummy(cls, 'white', 'the knight company')
            box = BoxLayout(orientation='vertical')
            img_path = self.screen.get_piece_image_path(p)
            box.add_widget(Image(source=img_path, allow_stretch=True, keep_ratio=True))
            box.add_widget(Label(text=f"[b]{p.__class__.__name__}[/b]", markup=True, font_size='11sp'))
            self.step5_grid.add_widget(box)

        self.screen.show_popup("STEP 5: NEW UNITS", txt, self.draw_step5_and_wait, custom_widget=self.step5_grid)

    def draw_step5_and_wait(self):
        if hasattr(self.screen, 'mock_map_layer'):
            self.screen.root_layout.remove_widget(self.screen.mock_map_layer)
        if hasattr(self.screen, 'play_area'):
            self.screen.play_area.opacity = 1
            
        self.screen.is_input_locked = True
            
        self.screen.game.board = [[None for _ in range(8)] for _ in range(8)]
        pieces_to_show = [Praetorian, Royalguard, Menatarm, Hastati, Levies, Prince, Princess]
        
        for cls in pieces_to_show:
            p = self.screen._create_dummy(cls, 'white', 'the knight company')
            self.screen.game.board[0][pieces_to_show.index(cls)] = p
            
        self.screen.refresh_ui()
        self.screen.show_next_step_button(self.run_dnc_step6, pos_hint={'right': 0.98, 'y': 0.22})

    def run_dnc_step6(self):
        self.current_step = 5
        self.screen.tut_state = 'dnc_step6'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=ffaa00]Combat Phases[/color]\n\n"
               "When engaging an enemy base, combat is split into 2 phases:\n\n"
               "[b]Phase 1 (Deployment)[/b]: You arrange your units on the bottom 3 rows. The top rows are hidden (Blind Phase). You can safely [color=ff5555]Retreat[/color] here without losing any units.\n\n"
               "[b]Phase 2 (Reveal)[/b]: The enemy Commander's position is revealed. You must click [color=55ff55]Ready to Battle[/color] to begin.\n\n"
               "[color=00ffff]*PVP Exception*[/color]: If you attack another Player (White vs Black), Phase 2 will flip the board for the Defender, allowing them to arrange their units before battle begins.")
        self.screen.show_popup("STEP 6: COMBAT PHASES", txt, self.start_mock_phase_1)

    def start_mock_phase_1(self):
        # Allow clicks so players can inspect pieces during deployment
        self.screen.is_input_locked = False
        self.screen.tut_state = 'dnc_phase1'
        self.screen.game.board = [[None for _ in range(8)] for _ in range(8)]
        # Place exactly 3 Pawns matching the mockup (Max 3/3 units)
        self.screen.game.board[7][3] = self.screen._create_dummy(Pawn, 'white', 'the knight company')  # d1
        self.screen.game.board[7][4] = self.screen._create_dummy(Pawn, 'white', 'the knight company')  # e1
        self.screen.game.board[6][4] = self.screen._create_dummy(Pawn, 'white', 'the knight company')  # e2
        self.screen.init_board_ui()
        
        self.screen.info_label.text = "[color=00ffff]PHASE 1: Arrange your units (Bottom 3 rows)[/color]"
        for r in range(5, 8):
            for c in range(8):
                self.screen.squares[(r,c)].update_square_style(is_legal='move')
                
        self.black_mask = Widget()
        with self.black_mask.canvas.before:
            Color(0, 0, 0, 1)
            self.mask_rect = Rectangle()
            
        def update_mask(*args):
            if hasattr(self.screen, 'grid') and self.screen.grid:
                self.mask_rect.pos = (self.screen.grid.x, self.screen.grid.y + self.screen.grid.height * 3 / 8)
                self.mask_rect.size = (self.screen.grid.width, self.screen.grid.height * 5 / 8)
                
        if hasattr(self.screen, 'grid'):
            self.screen.grid.bind(pos=update_mask, size=update_mask)
            update_mask()
        self.screen.root_layout.add_widget(self.black_mask)
        
        self.screen.show_tutorial_phase_button(
            "CONFIRM SETUP",
            self.start_mock_phase_2,
            color=(0.15, 0.45, 0.65, 0.95)
        )

    def start_mock_phase_2(self):
        # Button callback fires via show_tutorial_phase_button which already hides itself
        if hasattr(self, 'black_mask') and self.black_mask and self.black_mask.parent:
            self.black_mask.parent.remove_widget(self.black_mask)
        
        self.screen.info_label.text = "[color=ffaa00]PHASE 2: Enemy Revealed! Observe their position.[/color]"
        for r in range(8):
            for c in range(8):
                self.screen.squares[(r,c)].update_square_style(is_legal=False, is_check=(r==0 and c==4))
        
        self.screen.show_tutorial_phase_button(
            "READY TO BATTLE",
            self.finish_mock_phases,
            color=(0.15, 0.55, 0.2, 0.95)
        )

    def finish_mock_phases(self):
        # Button already removed by show_tutorial_phase_button callback wrapper
        self.screen.info_label.text = "BATTLE COMMENCED!"
        for r in range(8):
            for c in range(8):
                self.screen.squares[(r,c)].update_square_style(is_legal=False, is_check=False)
        self.screen.show_next_step_button(self.run_dnc_step7)

    def run_dnc_step7(self):
        self.current_step = 6
        self.screen.tut_state = 'dnc_step7'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=00ffff]Army Mechanics[/color]\n\n"
               "[b]Fatigue[/b]: Marching and fighting causes Fatigue.\n"
               "Attacking a Village adds +1 Fatigue. Attacking a Castle adds +2.\n"
               "Fatigue is tracked per army stack. Max Fatigue is 6/6, forcing the army to rest.\n\n"
               "[b]Loyalty[/b]: Captured bases must be garrisoned with at least 3 units, otherwise Loyalty decreases. At 0%, a Rebellion occurs! (Main bases are immune to rebellions).\n\n"
               "[b]Capacity[/b]: An army stack is limited to 16 units maximum.")
        self.screen.show_popup("STEP 7: FATIGUE & LOYALTY", txt, self.run_dnc_step8)

    def run_dnc_step8(self):
        self.current_step = 7
        self.screen.tut_state = 'dnc_step8'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=ffff00]Tavern Recruitment[/color]\n\n"
               "You can buy new units from the Tavern menu inside a base.\n"
               "Each row offers 5 unit slots. Once a unit is purchased, its slot becomes empty [X].\n\n"
               "Try recruiting the Hastati (Cost: 6). You have 10 Tax.\n"
               "After buying, click NEXT.")
        
        layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(200))
        self.mock_tax_lbl = Label(text="Tax: [color=00ff00]10[/color]", markup=True, size_hint_y=None, height=dp(30))
        layout.add_widget(self.mock_tax_lbl)
        
        self.row_grid = GridLayout(cols=5, spacing=dp(10), size_hint_y=None, height=dp(140))
        app = App.get_running_app()
        
        def mock_buy_piece(p_name, cost):
            if not getattr(self, 'mock_bought', False):
                self.mock_bought = True
                self.mock_tax_lbl.text = f"Tax: [color=00ff00]{10 - cost}[/color]"
                self.row_grid.clear_widgets()
                self.row_grid.add_widget(RecruitCard(None, 0, 'white', app, None))
                self.row_grid.add_widget(RecruitCard('menatarm', 6, 'white', app, mock_buy_piece))
                for _ in range(3): self.row_grid.add_widget(RecruitCard(None, 0, 'white', app, None))
                app.play_click_sound()

        self.mock_bought = False
        self.row_grid.add_widget(RecruitCard('hastati', 6, 'white', app, mock_buy_piece))
        self.row_grid.add_widget(RecruitCard('menatarm', 6, 'white', app, mock_buy_piece))
        for _ in range(3): self.row_grid.add_widget(RecruitCard(None, 0, 'white', app, None))
        
        layout.add_widget(self.row_grid)
        self.screen.show_popup("STEP 8: RECRUITMENT", txt, self.run_dnc_step9, custom_widget=layout)

    def run_dnc_step9(self):
        self.current_step = 8
        self.screen.tut_state = 'dnc_step9'
        self.screen.show_retreat_button(self.current_step)
        txt = ("[color=00ff00]Victory & Defeat[/color]\n\n"
               "There are 2 ways to eliminate an enemy faction in Divide & Conquer:\n"
               "1. Kill their [b]King[/b] in combat. (Killing a Prince does NOT end the game).\n"
               "2. Successfully capture their [b]Main Base[/b] on the world map.\n\n"
               "[color=ff5555]*Critical Rule*[/color]: When defending your Main Base, you CANNOT press Retreat. It's a fight to the death!")
        
        def finish():
            self.screen.hide_retreat_button()
            self.screen.manager.current = 'main_menu'
            
        self.screen.show_popup("STEP 9: VICTORY CONDITIONS", txt, finish)