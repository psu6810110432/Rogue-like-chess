from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.app import App
from kivy.graphics import Rectangle, Color, RoundedRectangle 
from kivy.animation import Animation 
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from screens.parallax_screen import MenuScreen, Stage1Screen, Stage2Screen
from screens.parallax_screen import Fight1Screen, Fight2Screen, Fight3Screen, Fight4Screen, Fight5Screen, Fight6Screen, Fight7Screen

class RoundedButton(Button):
    def __init__(self, normal_color, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  
        self.background_normal = ''
        self.background_down = ''
        
        self.normal_color = normal_color
        self.shadow_color = [max(0, c * 0.4) for c in normal_color[:3]] + [normal_color[3]] 
        self.pressed_color = [max(0, c * 0.8) for c in normal_color[:3]] + [normal_color[3]] 
        
        with self.canvas.before:
            self.shadow_inst = Color(*self.shadow_color)
            self.shadow_rect = RoundedRectangle(radius=[15])
            
            self.color_inst = Color(*self.normal_color)
            self.main_rect = RoundedRectangle(radius=[15])
            
        self.bind(pos=self.update_rect, size=self.update_rect, state=self.on_state_change)

    def update_rect(self, *args):
        self.main_rect.pos = self.pos
        self.main_rect.size = self.size
        self.shadow_rect.pos = (self.pos[0], self.pos[1] - dp(4))
        self.shadow_rect.size = self.size

    def on_state_change(self, instance, value):
        if value == 'down':
            self.color_inst.rgba = self.pressed_color
            self.main_rect.pos = (self.pos[0], self.pos[1] - dp(2))
        else:
            self.color_inst.rgba = self.normal_color
            self.main_rect.pos = self.pos

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bg_manager = ScreenManager(transition=FadeTransition())
        self.bg_manager.add_widget(MenuScreen(name='menu'))
        self.bg_manager.add_widget(Stage1Screen(name='stage1'))
        self.bg_manager.add_widget(Stage2Screen(name='stage2'))
        self.bg_manager.add_widget(Fight1Screen(name='fight1'))
        self.bg_manager.add_widget(Fight2Screen(name='fight2'))
        self.bg_manager.add_widget(Fight3Screen(name='fight3'))
        self.bg_manager.add_widget(Fight4Screen(name='fight4'))
        self.bg_manager.add_widget(Fight5Screen(name='fight5'))
        self.bg_manager.add_widget(Fight6Screen(name='fight6'))
        self.bg_manager.add_widget(Fight7Screen(name='fight7'))
        
        self.add_widget(self.bg_manager) 


        root_layout = FloatLayout()

        # Layout หลักของเมนู (อยู่ตรงกลางเหมือนเดิม)
        layout = BoxLayout(orientation='vertical', padding=[50, 60, 50, 40], spacing=20, size_hint=(1, 1))
        
        title_container = FloatLayout(size_hint_y=0.4)
        
        title_shadow = Label(
            text="[b]ROGUELIKE CHESS[/b]",
            markup=True, font_size='70sp', color=(0, 0, 0, 0.9),
            pos_hint={'center_x': 0.505, 'center_y': 0.55}
        )
        title_main = Label(
            text="[b][color=ff5500]ROGUELIKE CHESS[/color][/b]",
            markup=True, font_size='70sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.57}
        )
        subtitle = Label(
            text="Enter the Dark Battlefield   Face Your Destiny",
            font_size='20sp', color=(0.6, 0.6, 0.7, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )
        
        title_container.add_widget(title_shadow)
        title_container.add_widget(title_main)
        title_container.add_widget(subtitle)
        layout.add_widget(title_container)
        
        btn_box = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.35, 0.55), pos_hint={'center_x': 0.5})
        
        play_btn = RoundedButton(text="PLAY", normal_color=(0.55, 0.15, 0.05, 0.95), bold=True, font_size='26sp')
        play_btn.bind(on_press=self.play_btn_sound, on_release=self.go_play)

        # --- 🟢 1. เพิ่มปุ่ม LOAD GAME ตรงนี้ ---
        load_btn = RoundedButton(text="LOAD GAME", normal_color=(0.15, 0.45, 0.15, 0.95), bold=True, font_size='24sp')
        load_btn.bind(on_press=self.play_btn_sound, on_release=self.open_load_menu)
        # ------------------------------------
        
        tutorial_btn = RoundedButton(text="TUTORIAL", normal_color=(0.1, 0.25, 0.35, 0.95), bold=True, font_size='22sp')
        tutorial_btn.bind(on_press=self.play_btn_sound, on_release=self.go_tutorial)
        
        opt_btn = RoundedButton(text="Options", normal_color=(0.15, 0.15, 0.15, 0.95), font_size='20sp')
        opt_btn.bind(on_press=self.play_btn_sound, on_release=self.go_options) 
        
        exit_btn = RoundedButton(text="Exit", normal_color=(0.35, 0.05, 0.05, 0.95), font_size='20sp')
        exit_btn.bind(on_press=self.play_btn_sound, on_release=self.do_exit)
        
        btn_box.add_widget(play_btn)
        btn_box.add_widget(load_btn)  # <--- เติมบรรทัดนี้เข้าไปครับ
        btn_box.add_widget(tutorial_btn)
        btn_box.add_widget(opt_btn)
        btn_box.add_widget(exit_btn)
        
        layout.add_widget(btn_box)
        
        self.prep_label = Label(text=">> PREPARE FOR BATTLE <<", size_hint_y=0.15, color=(0.8, 0.4, 0.1, 1), font_size='18sp')
        layout.add_widget(self.prep_label)
        
        root_layout.add_widget(layout)

        # ---------------------------------------------------------
        # เพิ่ม Label แสดงเวอร์ชันเกมที่มุมซ้ายล่าง
        # ---------------------------------------------------------
        game_version = "v2.7.17" # กำหนดเลขเวอร์ชันตรงนี้
        version_label = Label(
            text=f"[color=888888]{game_version}[/color]", 
            markup=True, 
            font_size='14sp',
            size_hint=(None, None),
            size=(dp(100), dp(30)),
            pos_hint={'x': 0.02, 'y': 0.02}, # วางไว้มุมซ้ายล่าง
            halign='left',
            valign='bottom'
        )
        version_label.bind(size=version_label.setter('text_size'))
        root_layout.add_widget(version_label)
        # ---------------------------------------------------------

        self.add_widget(root_layout)

    def update_rect(self, *args):
        self.overlay.pos = self.pos
        self.overlay.size = self.size

    def on_enter(self, *args):
        super().on_enter(*args) 
        self.bg_clock = Clock.schedule_interval(self.auto_change_bg, 10.0)

        anim = Animation(opacity=0.3, duration=1.2) + Animation(opacity=1, duration=1.2)
        anim.repeat = True 
        anim.start(self.prep_label) 

        # --- 🟢 2. เช็ค Suspended Save ทันทีที่เข้าหน้าจอ ---
        try:
            from logic.save_manager import get_suspended_save
            suspended_save = get_suspended_save()
            # เช็คว่ามีเซฟค้าง และยังไม่เคยโชว์ popup นึ้ตอนเปิดเกม
            if suspended_save and not getattr(self, '_suspend_checked', False):
                self._suspend_checked = True
                self.show_suspended_popup(suspended_save[0], suspended_save[1])
        except ImportError:
            pass # กันเหนียวเผื่อไฟล์ save_manager ยังไม่มี
        # ----------------------------------------------

    # --- 🟢 3. สร้างฟังก์ชันโชว์ Popup เกมค้าง ---
    def show_suspended_popup(self, world_id, save_name):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        lbl = Label(text=f"[b]CRASH RECOVERY[/b]\n\nพบการเล่นที่ค้างอยู่:\n[color=00ff00]{save_name}[/color]\n\nคุณต้องการดำเนินการต่อหรือไม่?", markup=True, halign='center', font_size='18sp')
        content.add_widget(lbl)
        
        btn_box = BoxLayout(spacing=dp(15), size_hint_y=0.4)
        
        btn_yes = RoundedButton(text="YES (โหลดทันที)", normal_color=(0.2, 0.6, 0.2, 1))
        btn_no = RoundedButton(text="NO (ลบทิ้ง/ยกเลิก)", normal_color=(0.8, 0.2, 0.2, 1))
        
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        content.add_widget(btn_box)
        
        pop = Popup(title="Session Suspended", content=content, size_hint=(0.6, 0.4), auto_dismiss=False, separator_color=(0.8, 0.2, 0.2, 1))
        
        def on_yes(instance):
            self.play_btn_sound()
            pop.dismiss()
            self.load_world_and_play(world_id) # ฟังก์ชันไปหน้าโหลดเกม
            
        def on_no(instance):
            self.play_btn_sound()
            from logic.save_manager import clear_suspended_status
            clear_suspended_status(world_id) # ปลดสถานะ suspended ออก
            pop.dismiss()
            
        btn_yes.bind(on_release=on_yes)
        btn_no.bind(on_release=on_no)
        pop.open()

    def load_world_and_play(self, world_id):
        """เมื่อกดโหลด จะส่ง ID เข้าไปเก็บที่ App และตัดเข้าหน้าแผนที่"""
        print(f"Loading World ID: {world_id}...")
        
        # เก็บ world_id ไว้ในตัวแปรของ App เพื่อให้หน้าแผนที่ดึงไปใช้ต่อ
        app = App.get_running_app()
        app.loaded_world_id = world_id 
        
        # ตัดเข้าหน้าจอ Campaign Map
        self.manager.current = 'campaign_map'

    def open_load_menu(self, instance):
        """เมื่อกดปุ่ม Load Game"""
        self.play_btn_sound()
        try:
            from components.load_menu_popup import LoadMenuPopup
            LoadMenuPopup(main_menu_ref=self).open()
        except ImportError as e:
            print(f"Error opening Load Menu: {e}")

    def on_leave(self, *args):
        super().on_leave(*args) 
        if hasattr(self, 'bg_clock'):
            self.bg_clock.cancel()
        Animation.cancel_all(self.prep_label)

    def play_btn_sound(self, instance=None):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()

    def go_play(self, instance):
        self.manager.current = 'setup'

    def go_tutorial(self, instance):
        self.manager.current = 'tutorial'

    def go_options(self, instance):
        self.manager.current = 'options'

    def do_exit(self, instance):
        App.get_running_app().stop()
    
    def auto_change_bg(self, dt):
        scene_order = [
            'menu', 'stage1', 'stage2',
            'fight1', 'fight2', 'fight3', 'fight4', 'fight5', 'fight6', 'fight7'
        ]
        current_scene = self.bg_manager.current
        if current_scene in scene_order:
            current_index = scene_order.index(current_scene)
            next_index = (current_index + 1) % len(scene_order)
            self.bg_manager.current = scene_order[next_index]