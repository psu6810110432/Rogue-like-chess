# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from screens.main_menu import MainMenuScreen
from screens.match_setup.setup_screen import MatchSetupScreen
from screens.gameplay_screen import GameplayScreen
from screens.options_screen import OptionsScreen
from screens.tutorial_screen import TutorialScreen
from kivy.properties import StringProperty
from kivy.core.audio import SoundLoader # ✨ Import ระบบเสียง

class RogueChessApp(App):
    ai_difficulty = 'normal'  # ตั้งค่าความยากเริ่มต้นของ AI

    # ตัวแปร StringProperty สำหรับเก็บค่าการตั้งค่าต่างๆ
    selected_board = StringProperty('Classic Board') 
    selected_unit_white = StringProperty('Medieval Knights') 
    selected_unit_black = StringProperty('Demon')
    
    def build(self):
        # ✨ โหลดไฟล์เสียง BGM และ SFX
        self.bgm = SoundLoader.load('assets/audio/bgm/main_theme.mp3')
        self.sfx_click = SoundLoader.load('assets/audio/sfx/click.wav')
        self.sfx_capture = SoundLoader.load('assets/audio/sfx/capture.wav')

        # เริ่มเล่น BGM ทันทีเมื่อเปิดเกม
        if self.bgm:
            self.bgm.loop = True
            self.bgm.volume = 0.5 # ระดับเสียงเริ่มต้น 50%
            self.bgm.play()

        # สร้าง ScreenManager พร้อมเอฟเฟกต์เฟดตอนเปลี่ยนหน้า
        sm = ScreenManager(transition=FadeTransition())
        
        # เพิ่มหน้าจอต่างๆ เข้าไปในระบบ
        sm.add_widget(MainMenuScreen(name='main_menu')) 
        sm.add_widget(MatchSetupScreen(name='setup'))
        sm.add_widget(GameplayScreen(name='gameplay')) 
        sm.add_widget(TutorialScreen(name='tutorial'))
        sm.add_widget(OptionsScreen(name='options'))
        
        return sm

    # ✨ ฟังก์ชันสำหรับปรับเสียงให้เรียกใช้จากที่อื่นได้
    def set_bgm_volume(self, volume):
        if self.bgm:
            self.bgm.volume = volume

    def play_click_sound(self):
        if self.sfx_click:
            self.sfx_click.play()

    def play_capture_sound(self):
        if self.sfx_capture:
            self.sfx_capture.play()

if __name__ == "__main__":
    RogueChessApp().run()