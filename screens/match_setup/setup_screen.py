# screens/match_setup/setup_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from screens.match_setup.setup_section import SetupSection

class MatchSetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.1)
        back_btn = Button(text="< Back", size_hint_x=0.15, background_color=(0.2, 0.2, 0.2, 1))
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        title_lbl = Label(text="Make Match", font_size='28sp', bold=True, size_hint_x=0.85)
        top_bar.add_widget(title_lbl)
        main_layout.add_widget(top_bar)
        
        self.setup_ui = SetupSection(size_hint_y=0.75)
        main_layout.add_widget(self.setup_ui)
        
        start_btn = Button(text="START BATTLE", size_hint_y=0.15, bold=True, font_size='24sp', background_color=(0.1, 0.5, 0.2, 1))
        start_btn.bind(on_release=self.start_game)
        main_layout.add_widget(start_btn)
        
        self.add_widget(main_layout)

    def go_back(self, instance):
        self.manager.current = 'main_menu'

    def start_game(self, instance):
        app = self.setup_ui.app
        
        # ✨ ดักคนใจร้อน! ถ้ากดปุ่มเริ่มก่อนที่จะเลือกครบ จะใส่ค่าเริ่มต้นให้ จะได้ไม่ค้าง
        if not app.game_mode: app.game_mode = 'PVE'
        if not app.selected_board: app.selected_board = 'Classic Board'
        if not app.selected_unit_white: app.selected_unit_white = 'Medieval Knights'
        if not app.selected_unit_black: app.selected_unit_black = 'Demon'

        # โหลดเกม
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(app.game_mode)
        self.manager.current = 'gameplay'