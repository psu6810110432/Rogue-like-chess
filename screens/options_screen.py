# screens/options_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider # ✨ Import Slider
from kivy.app import App
from kivy.metrics import dp

class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(20))
        
        # หัวข้อหน้า Options
        title = Label(text="[b][color=ff4400]OPTIONS[/color][/b]", markup=True, font_size='48sp', size_hint_y=0.2)
        layout.add_widget(title)
        
        # --- ส่วนที่ 1: AI Difficulty ---
        diff_label = Label(text="AI Difficulty", font_size='24sp', size_hint_y=0.1)
        layout.add_widget(diff_label)
        
        self.diff_box = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.2)
        self.btn_easy = Button(text="Easy", font_size='20sp')
        self.btn_easy.bind(on_release=lambda x: self.set_difficulty('easy'))
        self.btn_normal = Button(text="Normal", font_size='20sp')
        self.btn_normal.bind(on_release=lambda x: self.set_difficulty('normal'))
        self.btn_hard = Button(text="Hard", font_size='20sp')
        self.btn_hard.bind(on_release=lambda x: self.set_difficulty('hard'))
        
        self.diff_box.add_widget(self.btn_easy)
        self.diff_box.add_widget(self.btn_normal)
        self.diff_box.add_widget(self.btn_hard)
        layout.add_widget(self.diff_box)
        
        # --- ✨ ส่วนที่ 2: Audio Settings ✨ ---
        audio_label = Label(text="Music Volume", font_size='24sp', size_hint_y=0.1)
        layout.add_widget(audio_label)

        audio_box = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.2)
        
        # แถบปรับเสียง
        self.vol_slider = Slider(min=0, max=1, value=0.5, size_hint_x=0.7)
        self.vol_slider.bind(value=self.on_volume_change)
        audio_box.add_widget(self.vol_slider)

        # ปุ่มปิดเสียง (Mute)
        self.btn_mute = Button(text="Mute Music", font_size='18sp', size_hint_x=0.3, background_color=(0.3, 0.3, 0.3, 1))
        self.btn_mute.bind(on_release=self.toggle_mute)
        audio_box.add_widget(self.btn_mute)

        layout.add_widget(audio_box)
        # -----------------------------------

        # ช่องว่างผลักปุ่ม Back ให้อยู่ล่างสุด
        layout.add_widget(Label(size_hint_y=0.2))
        
        # ปุ่มย้อนกลับ
        btn_back = Button(text="Back to Menu", font_size='20sp', size_hint_y=0.2, background_color=(0.5, 0.1, 0.1, 1))
        btn_back.bind(on_release=self.go_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
        
    def on_pre_enter(self, *args):
        self.update_button_colors()
        # ซิงค์ค่า Slider กับความดังของแอปตอนเปิดหน้านี้
        app = App.get_running_app()
        if app.bgm:
            self.vol_slider.value = app.bgm.volume

    def set_difficulty(self, level):
        app = App.get_running_app()
        app.play_click_sound() # ✨ เล่นเสียงตอนกด
        app.ai_difficulty = level  
        self.update_button_colors()
        
    def update_button_colors(self):
        app = App.get_running_app()
        current = getattr(app, 'ai_difficulty', 'normal')
        
        active_color = (0.8, 0.2, 0.0, 1)
        inactive_color = (0.2, 0.2, 0.2, 1)
        
        self.btn_easy.background_color = active_color if current == 'easy' else inactive_color
        self.btn_normal.background_color = active_color if current == 'normal' else inactive_color
        self.btn_hard.background_color = active_color if current == 'hard' else inactive_color

    # ✨ ฟังก์ชันจัดการเสียงเวลาเลื่อน Slider
    def on_volume_change(self, instance, value):
        app = App.get_running_app()
        app.set_bgm_volume(value)
        if value > 0:
            self.btn_mute.text = "Mute Music"
            self.btn_mute.background_color = (0.3, 0.3, 0.3, 1)
        else:
            self.btn_mute.text = "Unmute Music"
            self.btn_mute.background_color = (0.8, 0.2, 0.0, 1)

    # ✨ ฟังก์ชันปุ่ม Mute
    def toggle_mute(self, instance):
        app = App.get_running_app()
        app.play_click_sound()
        if self.vol_slider.value > 0:
            self.last_volume = self.vol_slider.value # จำค่าเก่าไว้
            self.vol_slider.value = 0
        else:
            self.vol_slider.value = getattr(self, 'last_volume', 0.5)

    def go_back(self, instance):
        App.get_running_app().play_click_sound() # ✨ เล่นเสียงตอนกดกลับ
        self.manager.current = 'main_menu' # ✨ FIX: จาก 'menu' เป็น 'main_menu' ให้ตรงกับ main.py