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
        # 1. ปรับเว้นขอบหน้าจอ (Padding) และช่องไฟ (Spacing) ให้ดูโปร่งสบายตา
        super().__init__(orientation='vertical', padding=[40, 10, 40, 10], spacing=20, **kwargs)
        
        self.app = App.get_running_app()
        # เช็คและตั้งค่า Default ป้องกันบัค
        if not hasattr(self.app, 'game_mode'): self.app.game_mode = 'PVE'
        if not hasattr(self.app, 'selected_board'): self.app.selected_board = 'Classic Board'
        if not hasattr(self.app, 'selected_unit_white'): self.app.selected_unit_white = 'Medieval Knights'
        if not hasattr(self.app, 'selected_unit_black'): self.app.selected_unit_black = 'Demon'

        self.anim_widgets = [] # เก็บรายชื่อปุ่มไว้ทำแอนิเมชันตอนเปิดหน้าจอ

        # ==========================================
        # 1. SELECT GAME MODE (เลือกโหมด)
        # ==========================================
        mode_box = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        lbl1 = Label(text="[color=f1c40f][b]1. SELECT GAME MODE[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl1.bind(size=lbl1.setter('text_size'))
        mode_box.add_widget(lbl1)
        
        mode_grid = GridLayout(cols=2, spacing=20)
        self.mode_cards = []
        for m in ['PVE', 'PVP']:
            desc = "Play against AI" if m == 'PVE' else "Local 2 Players"
            card = UnitCard(text=f"[b]{m} Mode[/b]\n[size=14sp][color=aaaaaa]{desc}[/color][/size]")
            card.val = m
            card.bind(on_release=self.on_mode_select)
            mode_grid.add_widget(card)
            self.mode_cards.append(card)
            self.anim_widgets.append(card)
        mode_box.add_widget(mode_grid)
        self.add_widget(mode_box)

        # ==========================================
        # 2. SELECT MAP (เลือกแมพ)
        # ==========================================
        map_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
        lbl2 = Label(text="[color=f1c40f][b]2. SELECT MAP[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl2.bind(size=lbl2.setter('text_size'))
        map_box.add_widget(lbl2)
        
        map_grid = GridLayout(cols=5, spacing=15)
        self.map_cards = []
        for mp in ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra', 'Random Board']:
            card = UnitCard(text=f"[b]{mp}[/b]")
            card.val = mp
            card.bind(on_release=self.on_map_select)
            map_grid.add_widget(card)
            self.map_cards.append(card)
            self.anim_widgets.append(card)
        map_box.add_widget(map_grid)
        self.add_widget(map_box)

        # ==========================================
        # 3. SELECT FACTIONS (เลือกเผ่า)
        # ==========================================
        fac_box = BoxLayout(orientation='vertical', size_hint_y=0.55, spacing=5)
        lbl3 = Label(text="[color=f1c40f][b]3. SELECT FACTIONS[/b][/color]", markup=True, font_size='20sp', halign='left', valign='middle')
        lbl3.bind(size=lbl3.setter('text_size'))
        fac_box.add_widget(lbl3)
        
        fac_split = BoxLayout(orientation='horizontal', spacing=40)
        
        # ฝั่งคนเล่น 1 (WHITE)
        w_box = BoxLayout(orientation='vertical', spacing=10)
        w_lbl = Label(text="WHITE FACTION", bold=True, color=(1,1,1,1), size_hint_y=0.15)
        w_box.add_widget(w_lbl)
        self.white_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b]{f}[/b]")
            card.val = f
            card.bind(on_release=self.on_white_select)
            w_box.add_widget(card)
            self.white_cards.append(card)
            self.anim_widgets.append(card)
        fac_split.add_widget(w_box)
        
        # ฝั่งคนเล่น 2 / บอท (BLACK)
        b_box = BoxLayout(orientation='vertical', spacing=10)
        b_lbl = Label(text="BLACK FACTION", bold=True, color=(0.7,0.7,0.7,1), size_hint_y=0.15)
        b_box.add_widget(b_lbl)
        self.black_cards = []
        for f in ['Medieval Knights', 'Ayothaya', 'Demon', 'Heaven']:
            card = UnitCard(text=f"[b]{f}[/b]")
            card.val = f
            card.bind(on_release=self.on_black_select)
            b_box.add_widget(card)
            self.black_cards.append(card)
            self.anim_widgets.append(card)
        fac_split.add_widget(b_box)
        
        fac_box.add_widget(fac_split)
        self.add_widget(fac_box)
        
        # ไฮไลท์การ์ดสีเขียวตามค่าที่เลือกไว้ตอนแรก
        self.update_selections()
        
        # ✨ ซ่อนปุ่มทั้งหมดเตรียมรันแอนิเมชัน
        for w in self.anim_widgets:
            w.opacity = 0
            w.y -= 20
            
        Clock.schedule_once(self.animate_in, 0.1)

    # ✨ แอนิเมชันโผล่ไล่ระดับ (Cascade Animation)
    def animate_in(self, dt):
        delay = 0
        for w in self.anim_widgets:
            anim = Animation(opacity=1, y=w.y + 20, duration=0.3, t='out_quad')
            Clock.schedule_once(lambda dt, a=anim, widget=w: a.start(widget), delay)
            delay += 0.03 # ค่อยๆ โผล่ไล่ไปทีละปุ่ม

    # ฟังก์ชันอัปเดตสีปุ่ม
    def update_selections(self):
        for c in self.mode_cards: c.set_selected(c.val == self.app.game_mode)
        for c in self.map_cards: c.set_selected(c.val == self.app.selected_board)
        for c in self.white_cards: c.set_selected(c.val == self.app.selected_unit_white)
        for c in self.black_cards: c.set_selected(c.val == self.app.selected_unit_black)

    # ฟังก์ชันรับค่าเมื่อปุ่มถูกกด
   # ฟังก์ชันรับค่าเมื่อปุ่มถูกกด
    def on_mode_select(self, instance):
        self.app.game_mode = instance.val
        self.update_selections()
        
    def on_map_select(self, instance):
        self.app.selected_board = instance.val
        self.update_selections()
        
    def on_white_select(self, instance):
        self.app.selected_unit_white = instance.val
        self.update_selections()
        
    def on_black_select(self, instance):
        self.app.selected_unit_black = instance.val
        self.update_selections()