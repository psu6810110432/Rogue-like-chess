# screens/main_menu.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.app import App 

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = (0.02, 0.02, 0.05, 1) # พื้นหลังมืดสนิท
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=30)
        
        # Title & Subtitle
        title_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
        title_box.add_widget(Label(
            text="[b][color=ff4400]⚔ ROGUELIKE CHESS ⚔[/color][/b]",
            markup=True, font_size='64sp'
        ))
        title_box.add_widget(Label(
            text="Enter the Dark Battlefield • Face Your Destiny",
            font_size='18sp', color=(0.7, 0.7, 0.8, 1)
        ))
        layout.add_widget(title_box)
        
        # Buttons
        btn_box = BoxLayout(orientation='vertical', spacing=15, size_hint=(0.4, 0.5), pos_hint={'center_x': 0.5})
        
        play_btn = Button(text="PLAY", background_color=(1, 0.3, 0, 1), bold=True, font_size='24sp')
        play_btn.bind(on_release=self.go_play)
        
        tutorial_btn = Button(text="TUTORIAL", background_color=(0.1, 0.6, 0.8, 1), bold=True, font_size='24sp')
        tutorial_btn.bind(on_release=self.go_tutorial)
        
        opt_btn = Button(text="Options", background_color=(0.2, 0.2, 0.3, 1))
        # ✨ FIX: เพิ่มคำสั่ง bind ให้ปุ่ม Options ทำงานแล้วครับ
        opt_btn.bind(on_release=self.go_options) 
        
        exit_btn = Button(text="Exit", background_color=(0.5, 0.1, 0.1, 1))
        exit_btn.bind(on_release=self.do_exit)
        
        btn_box.add_widget(play_btn)
        btn_box.add_widget(tutorial_btn)
        btn_box.add_widget(opt_btn)
        btn_box.add_widget(exit_btn)
        
        layout.add_widget(btn_box)
        layout.add_widget(Label(text="⚡ PREPARE FOR BATTLE ⚡", size_hint_y=0.1, color=(1, 0.5, 0, 1)))
        
        self.add_widget(layout)

    # ✨ สร้างฟังก์ชันแยกสำหรับแต่ละปุ่ม เพื่อให้เล่นเสียง Click ก่อนเปลี่ยนหน้าได้
    def play_btn_sound(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()

    def go_play(self, instance):
        self.play_btn_sound()
        self.manager.current = 'setup'

    def go_tutorial(self, instance):
        self.play_btn_sound()
        self.manager.current = 'tutorial'

    def go_options(self, instance):
        self.play_btn_sound()
        self.manager.current = 'options'

    def do_exit(self, instance):
        self.play_btn_sound()
        App.get_running_app().stop()