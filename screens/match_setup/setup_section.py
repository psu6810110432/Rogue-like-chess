# screens/match_setup/setup_section.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from components.unit_card import UnitCard

class SetupSection(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=[60, 20, 60, 20], spacing=20, **kwargs)
        self.app = App.get_running_app()
        # รีเซ็ตค่าเริ่มต้นในแอป
        self.app.game_mode = ''
        self.app.selected_board = ''
        self.app.selected_unit_white = ''
        self.app.selected_unit_black = ''

        # 1. SELECT GAME MODE
        self.mode_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=10)
        lbl1 = Label(text="[color=f1c40f][b]1. SELECT GAME MODE[/b][/color]", markup=True, font_size='22sp', halign='left', size_hint_y=None, height=35)
        lbl1.bind(size=lbl1.setter('text_size'))
        self.mode_box.add_widget(lbl1)
        
        mode_grid = GridLayout(cols=2, spacing=20)
        self.mode_cards = []
        for m in ['PVE', 'PVP']:
            card = UnitCard(text=f"[b]{m} Mode[/b]\n[size=14sp]{'Play vs AI' if m=='PVE' else '2 Players'}[/size]")
            card.val = m
            card.bind(on_release=self.on_mode_select)
            self.mode_cards.append(card)
            mode_grid.add_widget(card)
        self.mode_box.add_widget(mode_grid)
        self.add_widget(self.mode_box)

        # 2. SELECT MAP (ซ่อนไว้ก่อน)
        self.map_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=10, opacity=0, disabled=True)
        lbl2 = Label(text="[color=f1c40f][b]2. SELECT MAP[/b][/color]", markup=True, font_size='22sp', halign='left', size_hint_y=None, height=35)
        lbl2.bind(size=lbl2.setter('text_size'))
        self.map_box.add_widget(lbl2)
        
        map_grid = GridLayout(cols=5, spacing=15)
        self.map_cards = []
        for mp in ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra', 'Random Board']:
            card = UnitCard(text=f"[b][size=16sp]{mp}[/size][/b]")
            card.val = mp
            card.bind(on_release=self.on_map_select)
            self.map_cards.append(card)
            map_grid.add_widget(card)
        self.map_box.add_widget(map_grid)
        self.add_widget(self.map_box)

        # 3. SELECT FACTIONS (ซ่อนไว้ก่อน)
        self.fac_box = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=10, opacity=0, disabled=True)
        lbl3 = Label(text="[color=f1c40f][b]3. SELECT FACTIONS[/b][/color]", markup=True, font_size='22sp', halign='left', size_hint_y=None, height=35)
        lbl3.bind(size=lbl3.setter('text_size'))
        self.fac_box.add_widget(lbl3)
        
        self.fac_split = BoxLayout(orientation='horizontal', spacing=40)
        # ฝั่งขาว
        self.w_box = BoxLayout(orientation='vertical', spacing=10, opacity=0)
        self.w_box.add_widget(Label(text="WHITE", bold=True, size_hint_y=None, height=30))
        self.white_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b][size=18sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_release=self.on_white_select)
            self.white_cards.append(card)
            self.w_box.add_widget(card)
        # ฝั่งดำ
        self.b_box = BoxLayout(orientation='vertical', spacing=10, opacity=0)
        self.b_box.add_widget(Label(text="BLACK", bold=True, size_hint_y=None, height=30))
        self.black_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b][size=18sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_release=self.on_black_select)
            self.black_cards.append(card)
            self.b_box.add_widget(card)
            
        self.fac_split.add_widget(self.w_box)
        self.fac_split.add_widget(self.b_box)
        self.fac_box.add_widget(self.fac_split)
        self.add_widget(self.fac_box)

        self.update_selections()

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