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
    
    def build(self):
        # โหลดไฟล์ BGM และ SFX เดิม
        self.bgm = SoundLoader.load('assets/audio/bgm/main_theme.mp3')
        self.sfx_click = SoundLoader.load('assets/audio/sfx/click.mp3')
        self.sfx_coin = SoundLoader.load('assets/audio/sfx/coin.mp3')
        self.sfx_victory = SoundLoader.load('assets/audio/sfx/victory.mp3')
        
        # โหลดไฟล์ SFX ชุดใหม่ตามชื่อไฟล์ในโฟลเดอร์
        self.sfx_lose = SoundLoader.load('assets/audio/sfx/lose.mp3')
        self.sfx_draw = SoundLoader.load('assets/audio/sfx/draw.mp3')
        self.sfx_crash_win = SoundLoader.load('assets/audio/sfx/stagger.mp3') # ใช้ไฟล์ stagger.mp3
        self.sfx_move = SoundLoader.load('assets/audio/sfx/chessmove.mp3') # ใช้ไฟล์ chessmove.mp3
        self.sfx_distortion = SoundLoader.load('assets/audio/sfx/distorsion.mp3') # ใช้ไฟล์ distorsion.mp3

        if self.bgm:
            self.bgm.loop = True
            self.bgm.volume = 0.5 
            self.bgm.play()

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenuScreen(name='main_menu')) 
        sm.add_widget(MatchSetupScreen(name='setup'))
        sm.add_widget(GameplayScreen(name='gameplay')) 
        sm.add_widget(TutorialScreen(name='tutorial'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(CampaignMapScreen(name='campaign_map'))
        
        return sm

    def set_bgm_volume(self, volume):
        if self.bgm: self.bgm.volume = volume

    # ฟังก์ชันสั่งเล่นเสียงต่างๆ
    def play_click_sound(self):
        if getattr(self, 'sfx_click', None): self.sfx_click.play()
    def play_coin_sound(self):
        if getattr(self, 'sfx_coin', None): self.sfx_coin.play()
    def play_victory_sound(self):
        if getattr(self, 'sfx_victory', None): self.sfx_victory.play()
    
    # โหลดไฟล์ SFX ชุดใหม่ตามชื่อไฟล์ในโฟลเดอร์
    def play_lose_sound(self):
        if getattr(self, 'sfx_lose', None): self.sfx_lose.play()
    def play_draw_sound(self):
        if getattr(self, 'sfx_draw', None): self.sfx_draw.play()
    def play_crash_win_sound(self):
        if getattr(self, 'sfx_crash_win', None): self.sfx_crash_win.play()
    def play_move_sound(self):
        if getattr(self, 'sfx_move', None): self.sfx_move.play()
    def play_distortion_sound(self):
        if getattr(self, 'sfx_distortion', None): self.sfx_distortion.play()

if __name__ == "__main__":
    RogueChessApp().run()