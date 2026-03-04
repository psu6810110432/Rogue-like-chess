# screens/options_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.app import App
from kivy.graphics import Rectangle, Color
# ✨ ดึงคลาสที่เราทำไว้มาใช้เพื่อความคุมโทน
from screens.main_menu import RoundedButton
from screens.match_setup.setup_section import SelectionCard

class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # ✨ 1. เพิ่มพื้นหลังคุมโทน
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_image = Rectangle(source='assets/ui/backgrounds/menu_bg.png', pos=self.pos, size=self.size)
            Color(0.02, 0.02, 0.04, 0.8) 
            self.bg_overlay = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', padding=[50, 40, 50, 40], spacing=30)
        
        # ✨ 2. ส่วนหัว OPTIONS (มี Drop Shadow)
        header_container = FloatLayout(size_hint_y=0.2)
        header_shadow = Label(
            text="[b]OPTIONS[/b]", markup=True, font_size='54sp',
            color=(0, 0, 0, 0.9), pos_hint={'center_x': 0.503, 'center_y': 0.5}
        )
        header_main = Label(
            text="[b][color=ff5500]OPTIONS[/color][/b]", markup=True, font_size='54sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.52}
        )
        header_container.add_widget(header_shadow)
        header_container.add_widget(header_main)
        main_layout.add_widget(header_container)

        # ✨ 3. AI DIFFICULTY (ใช้ SelectionCard ขอบทอง)
        diff_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.25)
        self.add_gold_label(diff_box, "AI DIFFICULTY")
        
        self.diff_layout = BoxLayout(orientation='horizontal', spacing=20)
        self.diff_btns = {}
        for level in ['Easy', 'Normal', 'Hard']:
            btn = SelectionCard(text=f"[b]{level}[/b]")
            btn.val = level
            btn.bind(on_release=self.set_difficulty)
            self.diff_btns[level] = btn
            self.diff_layout.add_widget(btn)
        
        diff_box.add_widget(self.diff_layout)
        main_layout.add_widget(diff_box)

        # ✨ 4. MUSIC VOLUME
        vol_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.25)
        self.add_gold_label(vol_box, "MUSIC VOLUME")
        
        vol_controls = BoxLayout(orientation='horizontal', spacing=20)
        # ปรับแต่ง Slider
        self.vol_slider = Slider(min=0, max=1, value=0.5, step=0.05, size_hint_x=0.7)
        self.vol_slider.bind(value=self.on_volume_change)
        
        self.mute_btn = RoundedButton(text="Mute", normal_color=(0.2, 0.2, 0.25, 1), size_hint_x=0.3)
        self.mute_btn.bind(on_release=self.toggle_mute)
        
        vol_controls.add_widget(self.vol_slider)
        vol_controls.add_widget(self.mute_btn)
        vol_box.add_widget(vol_controls)
        main_layout.add_widget(vol_box)

        # ✨ 5. ปุ่มกลับหน้าเมนู (3D สีเลือดหมูเข้ม)
        self.back_btn = RoundedButton(
            text="BACK TO MENU", normal_color=(0.4, 0.1, 0.1, 1),
            size_hint=(0.4, 0.15), pos_hint={'center_x': 0.5}, bold=True
        )
        self.back_btn.bind(on_release=self.go_back)
        main_layout.add_widget(self.back_btn)
        
        self.add_widget(main_layout)
        
        # ตั้งค่าเริ่มต้นให้ Normal ถูกเลือก
        Clock_once = lambda dt: self.refresh_difficulty_ui("Normal")
        from kivy.clock import Clock
        Clock.schedule_once(Clock_once)

    def add_gold_label(self, parent, text):
        lbl = Label(text=f"[color=d4af37][b]{text}[/b][/color]", markup=True, 
                    font_size='20sp', halign='left', size_hint_y=None, height=30)
        lbl.bind(size=lbl.setter('text_size'))
        parent.add_widget(lbl)

    def update_bg(self, *args):
        self.bg_image.pos = self.pos
        self.bg_image.size = self.size
        self.bg_overlay.pos = self.pos
        self.bg_overlay.size = self.size

    def set_difficulty(self, instance):
        App.get_running_app().play_click_sound()
        self.refresh_difficulty_ui(instance.val)

    def refresh_difficulty_ui(self, selected_val):
        for val, btn in self.diff_btns.items():
            btn.set_selected(val == selected_val)

    def on_volume_change(self, instance, value):
        # ใส่ Logic ปรับเสียงเพลงของแอปคุณตรงนี้
        pass

    def toggle_mute(self, instance):
        App.get_running_app().play_click_sound()
        self.vol_slider.value = 0

    def go_back(self, instance):
        App.get_running_app().play_click_sound()
        self.manager.current = 'main_menu'