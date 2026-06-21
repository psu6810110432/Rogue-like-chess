# screens/match_setup/setup_screen.py
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.app import App 
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock

from screens.match_setup.setup_section import SetupSection
from screens.main_menu import RoundedButton 

# Import ฉากพื้นหลัง 3 ฉากที่ต้องการ
from screens.parallax_screen import MenuScreen, Stage1Screen, Stage2Screen

class MatchSetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # ==========================================
        # 1. ชั้นล่างสุด: ภาพพื้นหลังแบบเปลี่ยนอัตโนมัติ
        # ==========================================
        self.bg_manager = ScreenManager(transition=FadeTransition())
        self.bg_manager.add_widget(MenuScreen(name='menu'))
        self.bg_manager.add_widget(Stage1Screen(name='stage1'))
        self.bg_manager.add_widget(Stage2Screen(name='stage2'))
        self.add_widget(self.bg_manager)


        # ==========================================
        # 2. ชั้นบนสุด: UI เมนูเดิมของคุณ
        # ==========================================
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

    def update_rect(self, *args):
        self.overlay.pos = self.pos
        self.overlay.size = self.size

    def on_enter(self, *args):
        super().on_enter(*args)
        # ตั้งเวลาเปลี่ยนหน้าจอทุก 15 วินาที
        self.bg_clock = Clock.schedule_interval(self.auto_change_bg, 15.0)

    def on_leave(self, *args):
        super().on_leave(*args)
        # ปิดการทำงานของ Clock เมื่อออกจากหน้านี้
        if hasattr(self, 'bg_clock'):
            self.bg_clock.cancel()

    def auto_change_bg(self, dt):
        # รายชื่อฉากแค่ 3 อันตามที่คุณต้องการ
        scene_order = ['menu', 'stage1', 'stage2']
        current_scene = self.bg_manager.current
        if current_scene in scene_order:
            current_index = scene_order.index(current_scene)
            next_index = (current_index + 1) % len(scene_order)
            self.bg_manager.current = scene_order[next_index]

    def play_sound(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()

    def go_back(self, instance):
        self.manager.current = 'main_menu'

    def start_game(self, instance):
        app = self.setup_ui.app
        
        if not getattr(app, 'match_type', None): app.match_type = 'PVE'
        if not getattr(app, 'sub_mode', None): app.sub_mode = 'Classic'
        if not getattr(app, 'selected_board', None): app.selected_board = 'Classic Board'
        if not getattr(app, 'selected_unit_white', None): app.selected_unit_white = 'Medieval Knights'
        if not getattr(app, 'selected_unit_black', None): app.selected_unit_black = 'Demon'
        if getattr(app, 'selected_time_limit', None) is None: app.selected_time_limit = 0

        if app.match_type == 'ONLINE_PVP':
            app.game_mode = 'ONLINE_PVP'
            app.sub_mode = 'Classic'  
        elif app.match_type == 'LOCAL_PVP':
            app.game_mode = 'PVP'
        else:
            app.game_mode = app.match_type  

        if app.sub_mode == 'Divide_Conquer':
            self.manager.current = 'campaign_map'
        else:
            gameplay_screen = self.manager.get_screen('gameplay')
            gameplay_screen.setup_game(app.game_mode)
            self.manager.current = 'gameplay'