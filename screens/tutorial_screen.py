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
from screens.tutorials.classic_tutorial import ClassicTutorial
from screens.tutorials.dnc_tutorial import DNCTutorial

# ----------------- Tutorial Selection Popup -----------------
class TutSelectionPopup(ModalView):
    def __init__(self, on_classic, on_dnc, **kwargs):
        super().__init__(size_hint=(0.6, 0.4), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with root.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
        root.bind(pos=self._update_bg, size=self._update_bg)
        
        root.add_widget(Label(text="[b]SELECT TUTORIAL[/b]", markup=True, font_size='24sp', color=(1, 0.8, 0.2, 1)))
        
        btn_classic = Button(text="[b]TUTORIAL: CLASSIC CHESS[/b]", markup=True, font_size='18sp', background_color=(0.2, 0.5, 0.8, 1))
        btn_classic.bind(on_release=lambda x: (self.dismiss(), on_classic()))
        root.add_widget(btn_classic)
        
        btn_dnc = Button(text="[b]TUTORIAL: DIVIDE & CONQUER[/b]", markup=True, font_size='18sp', background_color=(0.8, 0.3, 0.2, 1))
        btn_dnc.bind(on_release=lambda x: (self.dismiss(), on_dnc()))
        root.add_widget(btn_dnc)
        
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

# ----------------- General Tutorial Popup Window -----------------
class TutPopup(ModalView):
    def __init__(self, title, text, on_next, show_pieces=False, show_kings=False, item_img=None, show_droppers=False, btn_align='right', custom_widget=None, on_prev=None, **kwargs):
        super().__init__(size_hint=(0.75, 0.75), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.6, 0.2, 1)
            self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=1.5)
        root.bind(pos=self._update_bg, size=self._update_bg)
        root.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='22sp', color=(1, 0.8, 0.2, 1), size_hint_y=0.15))
        
        content_box = BoxLayout(orientation='vertical', size_hint_y=0.7, spacing=dp(10))
        
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
                
                cell.add_widget(Image(source=f"assets/pieces/the knight company/white/1base/{p}.png", allow_stretch=True, keep_ratio=True, size_hint_y=0.75))
                cell.add_widget(Label(text=f"[b]{display_name.upper()}[/b]", markup=True, font_size='11sp', color=(1, 1, 1, 1), size_hint_y=0.25))
                board_sim.add_widget(cell)
            content_box.add_widget(board_sim)
            
        if show_kings:
            grid = GridLayout(cols=4, spacing=5, size_hint_y=None, height=dp(100))
            for f in ['the knight company', 'the chaos mankind', 'the deep anomaly', 'the ancient runes']:
                grid.add_widget(Image(source=f"assets/pieces/{f}/white/1base/king.png", allow_stretch=True, keep_ratio=True))
            content_box.add_widget(grid)

        if show_droppers:
            grid = GridLayout(cols=3, spacing=10, size_hint_y=None, height=dp(100))
            droppers = [('knight', 'KNIGHT'), ('bishop', 'BISHOP'), ('rook', 'ROOK')]
            for filename, name in droppers: 
                box = BoxLayout(orientation='vertical')
                box.add_widget(Image(source=f"assets/pieces/the knight company/white/1base/{filename}.png", allow_stretch=True, keep_ratio=True, size_hint_y=0.75))
                box.add_widget(Label(text=f"[b]{name}[/b]", markup=True, font_size='13sp', color=(0.8, 0.8, 0.8, 1), size_hint_y=0.25))
                grid.add_widget(box)
            content_box.add_widget(grid)
            
        if item_img:
            content_box.add_widget(Image(source=item_img, size_hint_y=None, height=dp(80), allow_stretch=True, keep_ratio=True))
            
        if custom_widget:
            content_box.add_widget(custom_widget)

        lbl = Label(text=text, markup=True, font_size='15sp', halign='center', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        content_box.add_widget(lbl)
        root.add_widget(content_box)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=dp(15))
        
        from kivy.uix.anchorlayout import AnchorLayout
        
        if on_prev:
            is_exit = isinstance(on_prev, dict) and on_prev.get('is_exit', False)
            prev_cb = on_prev.get('callback') if isinstance(on_prev, dict) else on_prev
            prev_text = "[b]QUIT TUTORIAL[/b]" if is_exit else "[b]<< PREV[/b]"
            prev_color = (0.8, 0.2, 0.2, 1) if is_exit else (0.6, 0.3, 0.1, 1)
            prev_btn = Button(text=prev_text, markup=True, size_hint=(None, None), size=(dp(200), dp(50)), background_color=prev_color)
            def _on_prev(*args, cb=prev_cb):
                App.get_running_app().play_click_sound()
                self.dismiss()
                if cb: cb()
            prev_btn.bind(on_release=_on_prev)
            prev_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
            prev_anchor.add_widget(prev_btn)
            btn_box.add_widget(prev_anchor)
        
        next_btn = Button(text="[b]NEXT[/b]", markup=True, size_hint=(None, None), size=(dp(200), dp(50)), background_color=(0.2, 0.6, 0.2, 1))
        
        def _on_next(*args):
            App.get_running_app().play_click_sound()
            self.dismiss()
            if on_next: on_next()
        next_btn.bind(on_release=_on_next)

        btn_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        btn_anchor.add_widget(next_btn)
        btn_box.add_widget(btn_anchor)
            
        root.add_widget(btn_box)
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

# ----------------- MOCK CRASH POPUP -----------------
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
        
        def create_coin_row(coin_type):
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(5))
            if coin_type == 'heads':
                box.add_widget(Image(source='assets/coin/coin8.png', size_hint_x=0.4))
                lbl = Label(text="[color=00ffff]+10[/color]", markup=True, bold=True, size_hint_x=0.6)
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)
            else:
                box.add_widget(Image(source='assets/coin/coin2.png', size_hint_x=0.4))
                lbl = Label(text="[color=aaaaaa]+0[/color]", markup=True, bold=True, size_hint_x=0.6)
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)
            return box

        atk_box = BoxLayout(orientation='vertical', spacing=dp(5))
        atk_box.add_widget(Image(source=atk_img, allow_stretch=True, keep_ratio=True, size_hint_y=0.4))
        atk_box.add_widget(Label(text=f"[b]Base: {atk_b}[/b]", markup=True, font_size='16sp', size_hint_y=0.15))
        
        atk_coins_box = BoxLayout(orientation='vertical', size_hint_y=0.25)
        for c in atk_c_list:
            atk_coins_box.add_widget(create_coin_row(c))
        atk_box.add_widget(atk_coins_box)
        atk_box.add_widget(Label(text=f"Total: {atk_s}", font_size='20sp', bold=True, color=(0.4, 0.8, 1, 1), size_hint_y=0.2))
        vs_box.add_widget(atk_box)
        
        vs_box.add_widget(Label(text="VS", font_size='26sp', bold=True, size_hint_x=0.2, color=(1, 0.8, 0, 1)))
        
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

# ----------------- MAIN TUTORIAL SCREEN -----------------
class TutorialScreen(GameplayScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tut_state = ''
        self.classic_tut = ClassicTutorial(self)
        self.dnc_tut = DNCTutorial(self)
        self.retreat_btn = None

    def on_enter(self):
        super().setup_game(mode='TUTORIAL')
        self.game.current_turn = 'white'
        self.tut_state = 'select_mode'
        
        # Create singleton retreat button once (hidden by default)
        if self.retreat_btn and self.retreat_btn.parent:
            self.retreat_btn.parent.remove_widget(self.retreat_btn)
        self.retreat_btn = Button(
            text="[b]<< PREV[/b]", markup=True, font_size='16sp',
            size_hint=(None, None), size=(dp(180), dp(50)),
            pos_hint={'x': 0.02, 'top': 0.98},
            background_color=(0.6, 0.3, 0.1, 1),
            opacity=0, disabled=True
        )
        self.retreat_btn.bind(on_release=self.go_to_previous_step)
        self.root_layout.add_widget(self.retreat_btn)
        
        Clock.schedule_once(lambda dt: TutSelectionPopup(
            on_classic=self.classic_tut.start,
            on_dnc=self.dnc_tut.start
        ).open(), 0.5)

    def show_retreat_button(self, step_index):
        """Toggle retreat button visibility and text based on step index."""
        if not self.retreat_btn:
            return
        self.retreat_btn.opacity = 1
        self.retreat_btn.disabled = False
        if step_index <= 0:
            self.retreat_btn.text = "[b]QUIT TUTORIAL[/b]"
            self.retreat_btn.background_color = (0.8, 0.2, 0.2, 1)
        else:
            self.retreat_btn.text = "[b]<< PREV[/b]"
            self.retreat_btn.background_color = (0.6, 0.3, 0.1, 1)

    def hide_retreat_button(self):
        """Hide the retreat button."""
        if self.retreat_btn:
            self.retreat_btn.opacity = 0
            self.retreat_btn.disabled = True

    def exit_tutorial(self):
        """Cleanly exit the tutorial and return to main menu."""
        # Cleanup DNC state if active
        if self.tut_state.startswith('dnc'):
            self.dnc_tut.cleanup()
        self.hide_retreat_button()
        self.manager.current = 'main_menu'

    def go_to_previous_step(self, instance):
        """Delegate retreat to the active tutorial, or exit at step 0."""
        App.get_running_app().play_click_sound()
        if self.tut_state.startswith('dnc'):
            if self.dnc_tut.current_step <= 0:
                self.exit_tutorial()
            else:
                self.dnc_tut.go_back()
        else:
            if self.classic_tut.current_step <= 0:
                self.exit_tutorial()
            else:
                self.classic_tut.go_back()

    def show_popup(self, title, text, on_next=None, show_pieces=False, show_kings=False, item_img=None, show_droppers=False, btn_align='right', custom_widget=None):
        # Auto-wire on_prev: EXIT at step 0, go_back at step 1+
        on_prev = None
        if self.tut_state.startswith('dnc'):
            if self.dnc_tut.current_step <= 0:
                on_prev = {'callback': self.exit_tutorial, 'is_exit': True}
            else:
                on_prev = self.dnc_tut.go_back
        elif self.tut_state != 'select_mode':
            if self.classic_tut.current_step <= 0:
                on_prev = {'callback': self.exit_tutorial, 'is_exit': True}
            else:
                on_prev = self.classic_tut.go_back
        TutPopup(title, text, on_next, show_pieces, show_kings, item_img, show_droppers, btn_align, custom_widget, on_prev=on_prev).open()
        
    def _create_dummy(self, cls, color, faction):
        p = cls(color, faction)
        p.base_points, p.coins = 5, 1
        p.hidden_passive.apply_passive = lambda d, c: (d, c)
        return p

    def set_board(self):
        self.game.board = [[None for _ in range(8)] for _ in range(8)]
        self.game.board[0][0] = self._create_dummy(King, 'white', 'the knight company')
        self.game.board[7][7] = self._create_dummy(King, 'black', 'the chaos mankind')
        
        if hasattr(self, 'board_anchor'): self._keep_grid_square(self.board_anchor, self.board_anchor.size)
        self.refresh_ui()

    def on_square_tap(self, instance):
        """Override: intercept taps during D&C Phase 1 to show piece status only."""
        if self.tut_state == 'dnc_phase1':
            App.get_running_app().play_click_sound()
            r, c = instance.row, instance.col
            piece = self.game.board[r][c]
            # Toggle: clicking the already-selected square deselects
            if self.selected == (r, c):
                self.selected = None
                self.hide_piece_status()
                self.refresh_ui()
                return
            if piece and piece.color == 'white':
                self.selected = (r, c)
                # Highlight the selected square; clear all others
                for (pr, pc), sq in self.squares.items():
                    sq.update_square_style(
                        highlight=((pr, pc) == (r, c)),
                        is_legal=False, is_check=False, is_last=False
                    )
                    p = self.game.board[pr][pc]
                    sq.set_piece_icon(self.get_piece_image_path(p) if p else None, piece=p)
                self.show_piece_status(piece)
            else:
                # Clicked empty square — deselect
                self.selected = None
                self.hide_piece_status()
                self.refresh_ui()
            return
        # All other tutorial states: delegate to parent GameplayScreen
        super().on_square_tap(instance)

    def check_winner(self): pass
    def check_game_over(self): pass
    def end_game(self, *args, **kwargs): pass

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
            if real_status == 'won':
                atk_piece = self.game.board[start[0]][start[1]]
                self.game.board[end[0]][end[1]] = atk_piece
                self.game.board[start[0]][start[1]] = None
            elif real_status == 'died':
                self.game.board[start[0]][start[1]] = None

            self.selected = None
            self.valid_moves = []
            self.game.current_turn = 'white' 
            self.refresh_ui()
            self.classic_tut.handle_crash_result(real_status)
            
        MockCrashPopup(atk_img, def_img, ab, ac, a_s, db, dc, d_s, res, color, on_close).open()

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
        elif self.tut_state == 'step5_attack2_wait':
            # ✨ บล็อคการกดกระดานระหว่างรอ 0.5 วิ
            return 
            
        super().on_square_tap(instance)
        
        if self.tut_state == 'step5_equip' and self.selected_item is None:
            piece = self.game.board[5][4]
            if piece and getattr(piece, 'item', None) is not None:
                # ✨ เปลี่ยน State ทันทีเพื่อป้องกันบั๊กกดรัวๆ (Race Condition)
                self.tut_state = 'step5_attack2_wait'
                Clock.schedule_once(lambda dt: self.classic_tut.setup_step5_attack2(), 0.5)

    def show_next_step_button(self, on_click, pos_hint=None, use_sidebar=None):
        """Show a tutorial NEXT STEP button. Auto-detects sidebar vs floating mode."""
        # Remove any existing floating next_step_btn
        if hasattr(self, 'next_step_btn') and self.next_step_btn and self.next_step_btn.parent:
            self.next_step_btn.parent.remove_widget(self.next_step_btn)
            self.next_step_btn = None
        # Also remove any sidebar version
        if hasattr(self, 'sidebar') and self.sidebar:
            self.sidebar.hide_tutorial_action_btn()

        # Auto-detect: if play_area is hidden (map mode), use floating button
        if use_sidebar is None:
            use_sidebar = hasattr(self, 'play_area') and self.play_area.opacity > 0

        if use_sidebar:
            def _cb():
                App.get_running_app().play_click_sound()
                self.sidebar.hide_tutorial_action_btn()
                if on_click: on_click()
            self.sidebar.show_tutorial_action_btn("NEXT STEP >>", _cb, color=(0.15, 0.55, 0.2, 0.95))
        else:
            # Floating button for full-screen / map steps
            if pos_hint is None:
                pos_hint = {'center_x': 0.5, 'y': 0.05}
            from kivy.uix.button import Button
            self.next_step_btn = Button(
                text="[b]NEXT STEP >>[/b]", markup=True, font_size='18sp',
                size_hint=(None, None), size=(dp(200), dp(50)),
                pos_hint=pos_hint,
                background_color=(0.2, 0.8, 0.2, 1)
            )
            def _cb_float(instance):
                App.get_running_app().play_click_sound()
                if self.next_step_btn and self.next_step_btn.parent:
                    self.next_step_btn.parent.remove_widget(self.next_step_btn)
                    self.next_step_btn = None
                if on_click: on_click()
            self.next_step_btn.bind(on_release=_cb_float)
            self.root_layout.add_widget(self.next_step_btn)

    def show_tutorial_phase_button(self, text, on_click, color=(0.15, 0.45, 0.6, 0.95)):
        """Show a phase-specific action button (e.g. CONFIRM SETUP) in the sidebar."""
        def _cb():
            App.get_running_app().play_click_sound()
            self.sidebar.hide_tutorial_action_btn()
            if on_click: on_click()

        self.sidebar.show_tutorial_action_btn(text, _cb, color=color)

    def hide_tutorial_phase_button(self):
        """Remove the tutorial phase button from the sidebar."""
        self.sidebar.hide_tutorial_action_btn()
