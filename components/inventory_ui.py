# components/inventory_ui.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp

class InventorySlot(ButtonBehavior, BoxLayout):
    def __init__(self, img_path='', is_selected=False, **kwargs):
        super().__init__(padding=dp(5), **kwargs)
        with self.canvas.before:
            self.bg_color = Color(0.15, 0.2, 0.15, 0.85) if is_selected else Color(0.1, 0.1, 0.12, 0.7)
            self.bg_rect = RoundedRectangle(radius=[10])
            self.border_color = Color(0.83, 0.68, 0.21, 1) if is_selected else Color(0.3, 0.3, 0.35, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 10], width=2.0 if is_selected else 1.2)
            
        self.bind(pos=self._update_bg, size=self._update_bg)
        if img_path: 
            self.add_widget(Image(source=img_path, allow_stretch=True, keep_ratio=True))
            
    def _update_bg(self, instance, value):
        self.bg_rect.pos, self.bg_rect.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, 10]