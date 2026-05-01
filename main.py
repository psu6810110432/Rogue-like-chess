# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from screens.main_menu import MainMenuScreen
from screens.match_setup.setup_screen import MatchSetupScreen
from screens.gameplay_screen import GameplayScreen
from screens.options_screen import OptionsScreen
from screens.tutorial_screen import TutorialScreen
from kivy.properties import StringProperty
from kivy.core.audio import SoundLoader
from screens.campaign_map_screen import CampaignMapScreen

class RogueChessApp(App):
    ai_difficulty = 'normal'
    selected_board = StringProperty('Classic Board')
    selected_unit_white = StringProperty('Medieval Knights')
    selected_unit_black = StringProperty('Demon')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ระบบ Cache สำหรับเก็บไฟล์เสียงที่ถูกโหลดแล้ว
        self._sound_cache = {}
        self.bgm = None
        self._bgm_volume = 0.5

    def build(self):
        # โหลดเฉพาะ BGM เพื่อเล่นตอนเริ่มเกม
        self.play_bgm('assets/audio/bgm/main_theme.mp3')

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(MatchSetupScreen(name='setup'))
        sm.add_widget(GameplayScreen(name='gameplay'))
        sm.add_widget(TutorialScreen(name='tutorial'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(CampaignMapScreen(name='campaign_map'))
        
        return sm

    def get_sound(self, path):
        """โหลดเสียงแบบ Lazy Load ประหยัด RAM"""
        if path not in self._sound_cache:
            self._sound_cache[path] = SoundLoader.load(path)
        return self._sound_cache[path]

    def play_bgm(self, path):
        sound = self.get_sound(path)
        if sound:
            self.bgm = sound
            self.bgm.loop = True
            self.bgm.volume = self._bgm_volume
            self.bgm.play()

    def set_bgm_volume(self, volume):
        self._bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume

    def _play_sfx(self, path):
        """Helper เล่น SFX ทั่วไป"""
        sfx = self.get_sound(path)
        if sfx:
            sfx.play()

    def play_click_sound(self): self._play_sfx('assets/audio/sfx/click.mp3')
    def play_coin_sound(self): self._play_sfx('assets/audio/sfx/coin.mp3')
    def play_victory_sound(self): self._play_sfx('assets/audio/sfx/victory.mp3')
    def play_lose_sound(self): self._play_sfx('assets/audio/sfx/lose.mp3')
    def play_draw_sound(self): self._play_sfx('assets/audio/sfx/draw.mp3')
    def play_crash_win_sound(self): self._play_sfx('assets/audio/sfx/stagger.mp3')
    def play_move_sound(self): self._play_sfx('assets/audio/sfx/chessmove.mp3')
    def play_distortion_sound(self): self._play_sfx('assets/audio/sfx/distorsion.mp3')

if __name__ == "__main__":
    RogueChessApp().run()