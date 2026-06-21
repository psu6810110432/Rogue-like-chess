from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty
from kivy.animation import Animation

class ParallaxScreen(Screen):
    layer_1_src = StringProperty('')
    layer_2_src = StringProperty('')
    layer_3_src = StringProperty('')
    layer_4_src = StringProperty('')
    layer_5_src = StringProperty('')
    overlay_color = ListProperty([0, 0, 0, 0]) 

    def on_enter(self, *args):
        super().on_enter(*args)
        self.set_texture_filters()
        self.start_pan_effect()

    def on_leave(self, *args):
        super().on_leave(*args)
        for i in range(1, 6):
            img = self.ids.get(f'layer_{i}')
            if img:
                Animation.stop_all(img)

    def set_texture_filters(self):
        for i in range(1, 6):
            img = self.ids.get(f'layer_{i}')
            if img and img.texture:
                img.texture.mag_filter = 'nearest'
                img.texture.min_filter = 'nearest'

    def start_pan_effect(self):
        t_half = 5  
        t_full = 10 
        speeds = {1: 0.01, 2: 0.03, 3: 0.05, 4: 0.08, 5: 0.12}

        for i in range(1, 6):
            img = self.ids.get(f'layer_{i}')
            if img:
                Animation.stop_all(img)
                img.pos_hint = {'center_x': 0.5, 'y': 0}
                
                d_x = speeds[i]
                anim = Animation(pos_hint={'center_x': 0.5 - d_x, 'y': 0}, duration=t_half) + \
                       Animation(pos_hint={'center_x': 0.5 + d_x, 'y': 0}, duration=t_full) + \
                       Animation(pos_hint={'center_x': 0.5, 'y': 0}, duration=t_half)
                anim.repeat = True
                anim.start(img)

class FightScreen(Screen):
    layer_1_src = StringProperty('')
    layer_2_src = StringProperty('')
    layer_3_src = StringProperty('')

    def on_enter(self, *args):
        super().on_enter(*args)
        self.set_texture_filters()
        self.start_pan_effect()

    def on_leave(self, *args):
        super().on_leave(*args)
        for i in range(1, 4):  
            img = self.ids.get(f'layer_{i}')
            if img:
                Animation.stop_all(img)

    def set_texture_filters(self):
        for i in range(1, 4):
            img = self.ids.get(f'layer_{i}')
            if img and img.texture:
                img.texture.mag_filter = 'nearest'
                img.texture.min_filter = 'nearest'

    def start_pan_effect(self):
        t_half = 5  
        t_full = 10 
        speeds = {1: 0.01, 2: 0.03, 3: 0.05}

        for i in range(1, 4):
            img = self.ids.get(f'layer_{i}')
            if img:
                Animation.stop_all(img)
                img.pos_hint = {'center_x': 0.5, 'y': 0}
                
                d_x = speeds[i]
                anim = Animation(pos_hint={'center_x': 0.5 - d_x, 'y': 0}, duration=t_half) + \
                       Animation(pos_hint={'center_x': 0.5 + d_x, 'y': 0}, duration=t_full) + \
                       Animation(pos_hint={'center_x': 0.5, 'y': 0}, duration=t_half)
                anim.repeat = True
                anim.start(img)

class MenuScreen(ParallaxScreen): pass
class Stage1Screen(ParallaxScreen): pass
class Stage2Screen(ParallaxScreen): pass

class Fight1Screen(FightScreen): pass
class Fight2Screen(FightScreen): pass
class Fight3Screen(FightScreen): pass
class Fight4Screen(FightScreen): pass
class Fight5Screen(FightScreen): pass
class Fight6Screen(FightScreen): pass
class Fight7Screen(FightScreen): pass