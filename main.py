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
        self._sound_cache = {}
        self.bgm = None
        self._bgm_volume = 0.5

    def build(self):
        self.play_bgm('assets/audio/bgm/main_theme.mp3')

        self.sm = ScreenManager(transition=FadeTransition())
        
        self.sm.add_widget(MainMenuScreen(name='main_menu'))
        self.sm.add_widget(MatchSetupScreen(name='setup'))
        self.sm.add_widget(GameplayScreen(name='gameplay'))
        self.sm.add_widget(TutorialScreen(name='tutorial'))
        self.sm.add_widget(OptionsScreen(name='options'))
        self.sm.add_widget(CampaignMapScreen(name='campaign_map'))
        
        return self.sm

    def play_bgm(self, path):
        if self.bgm:
            self.bgm.stop()
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = self._bgm_volume
            self.bgm.loop = True
            self.bgm.play()

    def set_bgm_volume(self, volume):
        self._bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume

    def _play_sfx(self, path):
        if path not in self._sound_cache:
            sound = SoundLoader.load(path)
            if sound:
                self._sound_cache[path] = sound
        
        sound = self._sound_cache.get(path)
        if sound:
            if sound.state == 'play':
                sound.stop()
            sound.play()

    def play_click_sound(self): self._play_sfx('assets/audio/sfx/click.mp3')
    def play_coin_sound(self): self._play_sfx('assets/audio/sfx/coin.mp3')
    def play_victory_sound(self): self._play_sfx('assets/audio/sfx/victory.mp3')
    def play_lose_sound(self): self._play_sfx('assets/audio/sfx/lose.mp3')
    def play_draw_sound(self): self._play_sfx('assets/audio/sfx/draw.mp3')
    def play_crash_win_sound(self): self._play_sfx('assets/audio/sfx/stagger.mp3')
    def play_move_sound(self): self._play_sfx('assets/audio/sfx/chessmove.mp3')
    def play_distortion_sound(self): self._play_sfx('assets/audio/sfx/distorsion.mp3')

if __name__ == '__main__':
    RogueChessApp().run()