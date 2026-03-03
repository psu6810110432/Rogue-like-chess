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
        super().__init__(orientation='vertical', padding=[40, 10, 40, 10], spacing=20, **kwargs)
        
        self.app = App.get_running_app()
        
        # 🚨 FIX: เปลี่ยนจาก None เป็น '' (ข้อความว่างเปล่า) เพื่อไม่ให้ Kivy StringProperty Error
        self.app.game_mode = ''
        self.app.selected_board = ''
        self.app.selected_unit_white = ''
        self.app.selected_unit_black = ''

        # ==========================================
        # 1. SELECT GAME MODE (โชว์เป็นอันดับแรกเสมอ)
        # ==========================================
        self.mode_box = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        lbl1 = Label(text="[color=f1c40f][b]1. SELECT GAME MODE[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl1.bind(size=lbl1.setter('text_size'))
        self.mode_box.add_widget(lbl1)
        
        mode_grid = GridLayout(cols=2, spacing=20)
        self.mode_cards = []
        for m in ['PVE', 'PVP']:
            desc = "Play against AI" if m == 'PVE' else "Local 2 Players"
            card = UnitCard(text=f"[b]{m} Mode[/b]\n[size=14sp][color=aaaaaa]{desc}[/color][/size]")
            card.val = m
            card.bind(on_release=self.on_mode_select)
            mode_grid.add_widget(card)
            self.mode_cards.append(card)
        self.mode_box.add_widget(mode_grid)
        self.add_widget(self.mode_box)

        # ==========================================
        # 2. SELECT MAP (ซ่อนไว้รอโหมดถูกกด)
        # ==========================================
        self.map_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
        lbl2 = Label(text="[color=f1c40f][b]2. SELECT MAP[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl2.bind(size=lbl2.setter('text_size'))
        self.map_box.add_widget(lbl2)
        
        map_grid = GridLayout(cols=5, spacing=15)
        self.map_cards = []
        for mp in ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra', 'Random Board']:
            card = UnitCard(text=f"[b][size=16sp]{mp}[/size][/b]")
            card.val = mp
            card.bind(on_release=self.on_map_select)
            map_grid.add_widget(card)
            self.map_cards.append(card)
        self.map_box.add_widget(map_grid)
        self.add_widget(self.map_box)

        # ==========================================
        # 3. SELECT FACTIONS (ซ่อนไว้รอแมพถูกกด)
        # ==========================================
        self.fac_box = BoxLayout(orientation='vertical', size_hint_y=0.55, spacing=5)
        lbl3 = Label(text="[color=f1c40f][b]3. SELECT FACTIONS[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl3.bind(size=lbl3.setter('text_size'))
        self.fac_box.add_widget(lbl3)
        
        self.fac_split = BoxLayout(orientation='horizontal', spacing=40)
        
        # === ฝั่งขาว (รอแมพถูกกด) ===
        self.w_box = BoxLayout(orientation='vertical', spacing=10)
        w_lbl = Label(text="WHITE FACTION", bold=True, color=(1,1,1,1), size_hint_y=0.15)
        self.w_box.add_widget(w_lbl)
        self.white_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b]{f}[/b]")
            card.val = f
            card.bind(on_release=self.on_white_select)
            self.w_box.add_widget(card)
            self.white_cards.append(card)
        self.fac_split.add_widget(self.w_box)
        
        # === ฝั่งดำ (รอฝั่งขาวถูกกด) ===
        self.b_box = BoxLayout(orientation='vertical', spacing=10)
        b_lbl = Label(text="BLACK FACTION", bold=True, color=(0.7,0.7,0.7,1), size_hint_y=0.15)
        self.b_box.add_widget(b_lbl)
        self.black_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b]{f}[/b]")
            card.val = f
            card.bind(on_release=self.on_black_select)
            self.b_box.add_widget(card)
            self.black_cards.append(card)
        self.fac_split.add_widget(self.b_box)
        
        self.fac_box.add_widget(self.fac_split)
        self.add_widget(self.fac_box)

        # ==========================================
        # การตั้งค่าแอนิเมชันเริ่มต้น (ซ่อนทุกอย่างยกเว้นโหมด)
        # ==========================================
        self.map_box.opacity = 0
        self.map_box.disabled = True
        
        self.fac_box.opacity = 0
        self.fac_box.disabled = True
        
        self.w_box.opacity = 0
        self.b_box.opacity = 0
        
        self.update_selections()
        
        Clock.schedule_once(lambda dt: self.animate_cards(self.mode_cards), 0.1)

    def animate_cards(self, cards):
        delay = 0
        for w in cards:
            w.opacity = 0
            anim = Animation(opacity=1, duration=0.4, t='out_quad')
            Clock.schedule_once(lambda dt, a=anim, widget=w: a.start(widget), delay)
            delay += 0.08 

    def update_selections(self):
        for c in self.mode_cards: c.set_selected(c.val == self.app.game_mode)
        for c in self.map_cards: c.set_selected(c.val == self.app.selected_board)
        for c in self.white_cards: c.set_selected(c.val == self.app.selected_unit_white)
        for c in self.black_cards: c.set_selected(c.val == self.app.selected_unit_black)

    # ==========================================
    # Logic การกดแล้วให้โผล่ทีละขั้น (Cascade Reveal)
    # ==========================================
    def on_mode_select(self, instance):
        self.app.game_mode = instance.val
        self.update_selections()
        
        if self.map_box.opacity == 0:
            self.map_box.disabled = False
            Animation(opacity=1, duration=0.3).start(self.map_box)
            self.animate_cards(self.map_cards)
            
    def on_map_select(self, instance):
        self.app.selected_board = instance.val
        self.update_selections()
        
        if self.fac_box.opacity == 0:
            self.fac_box.disabled = False
            Animation(opacity=1, duration=0.3).start(self.fac_box)
            
        if self.w_box.opacity == 0:
            Animation(opacity=1, duration=0.3).start(self.w_box)
            self.animate_cards(self.white_cards)
            
    def on_white_select(self, instance):
        self.app.selected_unit_white = instance.val
        self.update_selections()
        
        if self.b_box.opacity == 0:
            Animation(opacity=1, duration=0.3).start(self.b_box)
            self.animate_cards(self.black_cards)
            
    def on_black_select(self, instance):
        self.app.selected_unit_black = instance.val
        self.update_selections()