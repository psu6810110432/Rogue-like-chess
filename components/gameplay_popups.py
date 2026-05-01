# components/gameplay_popups.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.app import App
from logic.pieces import Queen, Princess, Rook, Bishop, Knight

class _PromotionOption(ButtonBehavior, BoxLayout):
    def __init__(self, img_path, **kwargs):
        super().__init__(orientation='vertical', padding=dp(4), **kwargs)
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 0.8)
            self._bg_rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=lambda i, v: setattr(self._bg_rr, 'pos', v), size=lambda i, v: setattr(self._bg_rr, 'size', v))
        self.add_widget(Image(source=img_path, fit_mode='contain'))

class PromotionPopup(ModalView):
    def __init__(self, color, tribe, callback, is_prince=False, **kwargs):
        super().__init__(size_hint=(0.45, 0.3), auto_dismiss=False, background='', background_color=(0, 0, 0, 0), **kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        with root.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(12)])
        root.bind(pos=lambda i, v: setattr(self._bg, 'pos', v), size=lambda i, v: setattr(self._bg, 'size', v))
        root.add_widget(Label(text='Choose Your Piece', font_size='16sp', bold=True, color=(1, 0.25, 0.25, 1), size_hint_y=0.18))
        layout = GridLayout(cols=4, padding=dp(5), spacing=dp(10), size_hint_y=0.82)
        
        if is_prince:
            ops = [Princess, Knight, Bishop, Rook]; names = ['princess', 'knight', 'bishop', 'rook']
            display_names = {'princess': 'Princess', 'knight': 'Knight', 'bishop': 'Bishop', 'rook': 'Rook'}
        else:
            ops = [Queen, Knight, Bishop, Rook]; names = ['queen', 'knight', 'bishop', 'rook']
            display_names = {'queen': 'Queen', 'knight': 'Knight', 'bishop': 'Bishop', 'rook': 'Rook'}
            
        for cls, n in zip(ops, names):
            col = BoxLayout(orientation='vertical', spacing=dp(2))
            opt = _PromotionOption(img_path=f"assets/pieces/{tribe}/{color}/1base/{n}.png")
            opt.bind(on_release=lambda b, c=cls: (App.get_running_app().play_click_sound(), callback(c)))
            col.add_widget(opt)
            col.add_widget(Label(text=display_names[n], font_size='13sp', size_hint_y=0.18, color=(0.9, 0.9, 0.9, 1)))
            layout.add_widget(col)
        root.add_widget(layout)
        self.add_widget(root)

class RetreatPopup(ModalView):
    def __init__(self, dead_count, on_close, **kwargs):
        super().__init__(size_hint=(0.45, 0.35), auto_dismiss=False, background='', background_color=(0, 0, 0, 0.8), **kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.12, 0.12, 0.15, 0.95)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(12)])
            Color(0.8, 0.3, 0.2, 1)
            self._border = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=2)
        root.bind(pos=self._update_bg, size=self._update_bg)
        
        title = Label(text="[b]TACTICAL RETREAT[/b]", markup=True, font_size='22sp', color=(1, 0.4, 0.4, 1), size_hint_y=0.2)
        root.add_widget(title)
        
        msg = "Your army is falling back..."
        if dead_count > 0:
            msg += f"\n\n[color=ff4444]Casualties: {dead_count} Light Infantry lost during the escape![/color]"
        else:
            msg += "\n\n[color=44ff44]A clean escape! No casualties.[/color]"
            
        lbl = Label(text=msg, markup=True, font_size='16sp', halign='center', size_hint_y=0.5)
        root.add_widget(lbl)
        
        btn = Button(text="[b]CONTINUE[/b]", markup=True, size_hint_y=0.3, background_color=(0.6, 0.2, 0.2, 1))
        btn.bind(on_release=lambda x: (self.dismiss(), on_close()))
        root.add_widget(btn)
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self._bg.pos, self._bg.size = instance.pos, instance.size
        self._border.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]