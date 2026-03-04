# screens/match_setup/setup_section.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp

class SelectionCard(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.markup = True
        self.val = ''
        self.is_selected = False
        
        with self.canvas.before:
            # ✨ เปลี่ยนชื่อตัวแปรให้มีคำว่า card_ นำหน้าทั้งหมด หนีตัวแปรระบบ Kivy
            self.card_bg_color = Color(0.1, 0.1, 0.12, 0.7) 
            self.card_rect = RoundedRectangle(radius=[12])
            
            self.card_border_color = Color(0.3, 0.3, 0.35, 1) 
            self.card_border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 12], width=1.2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics, state=self.update_state)

    def update_graphics(self, *args):
        self.card_rect.pos = self.pos
        self.card_rect.size = self.size
        self.card_border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 12]

    def update_state(self, *args):
        if not self.is_selected:
            if self.state == 'down':
                self.card_bg_color.rgba = (0.2, 0.2, 0.25, 0.8)
            else:
                self.card_bg_color.rgba = (0.1, 0.1, 0.12, 0.7)

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.card_bg_color.rgba = (0.15, 0.2, 0.15, 0.85) 
            self.card_border_color.rgba = (0.83, 0.68, 0.21, 1) 
            self.card_border_line.width = 2.0
        else:
            self.card_bg_color.rgba = (0.1, 0.1, 0.12, 0.7)
            self.card_border_color.rgba = (0.3, 0.3, 0.35, 1)
            self.card_border_line.width = 1.2


class SetupSection(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=[20, 10, 20, 10], spacing=15, **kwargs)
        self.app = App.get_running_app()
        self.app.game_mode = ''
        self.app.selected_board = ''
        self.app.selected_unit_white = ''
        self.app.selected_unit_black = ''

        # 1. SELECT GAME MODE
        self.mode_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
        self.add_header(self.mode_box, "1. SELECT GAME MODE")
        
        mode_grid = GridLayout(cols=2, spacing=20)
        self.mode_cards = []
        for m in ['PVE', 'PVP']:
            desc = "COMMANDER vs AI" if m=='PVE' else "DUEL BETWEEN LORDS"
            card = SelectionCard(text=f"[b]{m} MODE[/b]\n[size=14sp][color=a0a0a0]{desc}[/color][/size]")
            card.val = m
            card.bind(on_press=self.play_sound, on_release=self.on_mode_select)
            self.mode_cards.append(card)
            mode_grid.add_widget(card)
        self.mode_box.add_widget(mode_grid)
        self.add_widget(self.mode_box)

        # 2. SELECT MAP
        self.map_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5, opacity=0, disabled=True)
        self.add_header(self.map_box, "2. STRATEGIC BATTLEFIELD")
        
        map_grid = GridLayout(cols=5, spacing=12)
        self.map_cards = []
        for mp in ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra', 'Random Board']:
            display_name = mp.replace(" Board", "")
            card = SelectionCard(text=f"[b][size=15sp]{display_name}[/size][/b]")
            card.val = mp
            card.bind(on_press=self.play_sound, on_release=self.on_map_select)
            self.map_cards.append(card)
            map_grid.add_widget(card)
        self.map_box.add_widget(map_grid)
        self.add_widget(self.map_box)

        # 3. SELECT FACTIONS
        self.fac_box = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=5, opacity=0, disabled=True)
        self.add_header(self.fac_box, "3. CHOOSE YOUR LEGION")
        
        self.fac_split = BoxLayout(orientation='horizontal', spacing=30)
        
        # WHITE
        self.w_box = BoxLayout(orientation='vertical', spacing=8, opacity=0)
        self.w_box.add_widget(Label(text="DIVINE ORDER (WHITE)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.white_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = SelectionCard(text=f"[b][size=16sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_press=self.play_sound, on_release=self.on_white_select)
            self.white_cards.append(card)
            self.w_box.add_widget(card)
            
        # BLACK
        self.b_box = BoxLayout(orientation='vertical', spacing=8, opacity=0)
        self.b_box.add_widget(Label(text="DARK ABYSS (BLACK)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.black_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = SelectionCard(text=f"[b][size=16sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_press=self.play_sound, on_release=self.on_black_select)
            self.black_cards.append(card)
            self.b_box.add_widget(card)
            
        self.fac_split.add_widget(self.w_box)
        self.fac_split.add_widget(self.b_box)
        self.fac_box.add_widget(self.fac_split)
        self.add_widget(self.fac_box)

        self.update_selections()

    def add_header(self, parent_box, text):
        lbl = Label(text=f"[color=d4af37][b]{text}[/b][/color]", markup=True, font_size='20sp', halign='left', size_hint_y=None, height=35)
        lbl.bind(size=lbl.setter('text_size'))
        parent_box.add_widget(lbl)

    def play_sound(self, instance):
        if hasattr(self.app, 'play_click_sound'):
            self.app.play_click_sound()

    def update_selections(self):
        for c in self.mode_cards: c.set_selected(c.val == self.app.game_mode)
        for c in self.map_cards: c.set_selected(c.val == self.app.selected_board)
        for c in self.white_cards: c.set_selected(c.val == self.app.selected_unit_white)
        for c in self.black_cards: c.set_selected(c.val == self.app.selected_unit_black)

    def on_mode_select(self, instance):
        self.app.game_mode = instance.val
        self.update_selections()
        self.map_box.disabled = False
        Animation(opacity=1, duration=0.3).start(self.map_box)

    def on_map_select(self, instance):
        self.app.selected_board = instance.val
        self.update_selections()
        self.fac_box.disabled = False
        Animation(opacity=1, duration=0.3).start(self.fac_box)
        Animation(opacity=1, duration=0.3).start(self.w_box)

    def on_white_select(self, instance):
        self.app.selected_unit_white = instance.val
        self.update_selections()
        Animation(opacity=1, duration=0.3).start(self.b_box)

    def on_black_select(self, instance):
        self.app.selected_unit_black = instance.val
        self.update_selections()