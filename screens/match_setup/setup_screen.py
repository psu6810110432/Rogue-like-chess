# screens/match_setup/setup_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.app import App 
from kivy.graphics import Rectangle, Color
from screens.match_setup.setup_section import SetupSection
from screens.main_menu import RoundedButton 

class MatchSetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_image = Rectangle(source='assets/ui/backgrounds/menu_bg.png', pos=self.pos, size=self.size)
            Color(0.02, 0.02, 0.04, 0.85) 
            self.bg_overlay = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', padding=[30, 20, 30, 20], spacing=15)
        
        top_bar = BoxLayout(size_hint_y=0.1, spacing=20)
        back_btn = RoundedButton(text="< Back", normal_color=(0.2, 0.2, 0.25, 0.9), size_hint_x=0.15, font_size='18sp')
        back_btn.bind(on_press=self.play_sound, on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        title_lbl = Label(text="BATTLE SETUP", font_size='32sp', bold=True, color=(1, 0.8, 0.4, 1))
        top_bar.add_widget(title_lbl)
        
        top_bar.add_widget(BoxLayout(size_hint_x=0.15))
        main_layout.add_widget(top_bar)
        
        self.setup_ui = SetupSection(size_hint_y=0.75)
        main_layout.add_widget(self.setup_ui)
        
        start_btn = RoundedButton(text="ENGAGE BATTLE", normal_color=(0.55, 0.15, 0.05, 1), size_hint_y=0.15, bold=True, font_size='28sp')
        start_btn.bind(on_press=self.play_sound, on_release=self.start_game)
        main_layout.add_widget(start_btn)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg_image.pos = self.pos
        self.bg_image.size = self.size
        self.bg_overlay.pos = self.pos
        self.bg_overlay.size = self.size

    def play_sound(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()

    def go_back(self, instance):
        self.manager.current = 'main_menu'

    def start_game(self, instance):
        app = self.setup_ui.app
        
        # ✨ เพิ่ม Fallback ป้องกัน Error หากผู้เล่นกดเริ่มเลยโดยไม่เลือก
        if not getattr(app, 'match_type', None): app.match_type = 'PVE'
        if not getattr(app, 'sub_mode', None): app.sub_mode = 'Classic'
        if not getattr(app, 'selected_board', None): app.selected_board = 'Classic Board'
        if not getattr(app, 'selected_unit_white', None): app.selected_unit_white = 'Medieval Knights'
        if not getattr(app, 'selected_unit_black', None): app.selected_unit_black = 'Demon'

        # แปลง match_type เป็น game_mode ให้ระบบเดิมใช้ได้
        app.game_mode = app.match_type 

        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(app.game_mode)
        self.manager.current = 'gameplay'