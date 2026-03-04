# screens/main_menu.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.app import App
from kivy.graphics import Rectangle, Color, RoundedRectangle 
from kivy.animation import Animation 
from kivy.metrics import dp

class RoundedButton(Button):
    def __init__(self, normal_color, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  
        self.background_normal = ''
        self.background_down = ''
        
        self.normal_color = normal_color
        # ปรับเงาให้มืดลงอีกเป็น 0.4 (เพื่อให้ดูมีมิติลึกขึ้นในพื้นหลังมืด)
        self.shadow_color = [max(0, c * 0.4) for c in normal_color[:3]] + [normal_color[3]] 
        self.pressed_color = [max(0, c * 0.8) for c in normal_color[:3]] + [normal_color[3]] 
        
        with self.canvas.before:
            self.shadow_inst = Color(*self.shadow_color)
            self.shadow_rect = RoundedRectangle(radius=[15])
            
            self.color_inst = Color(*self.normal_color)
            self.main_rect = RoundedRectangle(radius=[15])
            
        self.bind(pos=self.update_rect, size=self.update_rect, state=self.update_state)
        
    def update_rect(self, *args):
        self.shadow_rect.pos = self.pos
        self.shadow_rect.size = self.size
        
        if self.state == 'normal':
            self.main_rect.pos = (self.pos[0], self.pos[1] + dp(6))
            self.main_rect.size = (self.size[0], self.size[1] - dp(6))
        else:
            self.main_rect.pos = self.pos
            self.main_rect.size = self.size
            
    def update_state(self, *args):
        if self.state == 'down':
            self.color_inst.rgba = self.pressed_color
            self.main_rect.pos = self.pos
            self.main_rect.size = self.size
        else:
            self.color_inst.rgba = self.normal_color
            self.main_rect.pos = (self.pos[0], self.pos[1] + dp(6))
            self.main_rect.size = (self.size[0], self.size[1] - dp(6))

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(1, 1, 1, 1) 
            self.bg_image = Rectangle(source='assets/ui/backgrounds/menu_bg.png', pos=self.pos, size=self.size)
            # เพิ่มความทึบของฟิลเตอร์ดำอีกนิด (0.75) เพื่อเบลนขอบปุ่มให้เข้ากับฉากหลัง
            Color(0.02, 0.02, 0.05, 0.75) 
            self.bg_overlay = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)
        
        layout = BoxLayout(orientation='vertical', padding=[50, 60, 50, 40], spacing=20)
        
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
            text="Enter the Dark Battlefield • Face Your Destiny",
            font_size='20sp', color=(0.6, 0.6, 0.7, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )
        
        title_container.add_widget(title_shadow)
        title_container.add_widget(title_main)
        title_container.add_widget(subtitle)
        layout.add_widget(title_container)
        
        btn_box = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.35, 0.45), pos_hint={'center_x': 0.5})
        
        # ✨ ปรับโทนสีใหม่ให้ "ดาร์ก และ คุมโทน" (ตัวเลขสุดท้าย 0.95 คือโปร่งแสงเบาๆ ให้กลืนกับรูป)
        play_btn = RoundedButton(text="PLAY", normal_color=(0.55, 0.15, 0.05, 0.95), bold=True, font_size='26sp')
        play_btn.bind(on_press=self.play_btn_sound, on_release=self.go_play)
        
        tutorial_btn = RoundedButton(text="TUTORIAL", normal_color=(0.1, 0.25, 0.35, 0.95), bold=True, font_size='22sp')
        tutorial_btn.bind(on_press=self.play_btn_sound, on_release=self.go_tutorial)
        
        opt_btn = RoundedButton(text="Options", normal_color=(0.15, 0.15, 0.15, 0.95), font_size='20sp')
        opt_btn.bind(on_press=self.play_btn_sound, on_release=self.go_options) 
        
        exit_btn = RoundedButton(text="Exit", normal_color=(0.35, 0.05, 0.05, 0.95), font_size='20sp')
        exit_btn.bind(on_press=self.play_btn_sound, on_release=self.do_exit)
        
        btn_box.add_widget(play_btn)
        btn_box.add_widget(tutorial_btn)
        btn_box.add_widget(opt_btn)
        btn_box.add_widget(exit_btn)
        
        layout.add_widget(btn_box)
        
        self.prep_label = Label(text=">> PREPARE FOR BATTLE <<", size_hint_y=0.15, color=(0.8, 0.4, 0.1, 1), font_size='18sp')
        layout.add_widget(self.prep_label)
        
        self.add_widget(layout)

    def update_bg(self, *args):
        self.bg_image.pos = self.pos
        self.bg_image.size = self.size
        self.bg_overlay.pos = self.pos
        self.bg_overlay.size = self.size

    def on_enter(self, *args):
        anim = Animation(opacity=0.3, duration=1.2) + Animation(opacity=1, duration=1.2)
        anim.repeat = True 
        anim.start(self.prep_label) 

    def on_leave(self, *args):
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