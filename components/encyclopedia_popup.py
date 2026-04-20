# components/encyclopedia_popup.py
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp

from logic.pieces import King, Queen, Rook, Bishop, Knight, Pawn
from logic.item_logic import ITEM_DATABASE

class FactionCard(BoxLayout):
    def __init__(self, faction_name, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(10), **kwargs)
        self.faction_name = faction_name
        self.faction_id = faction_name.lower()
        
        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.bg = RoundedRectangle(radius=[dp(10)])
            Color(0.4, 0.4, 0.5, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(10)], width=1.2)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Faction Title
        self.add_widget(Label(text=f"[b]{faction_name}[/b]", markup=True, font_size='18sp', color=(1, 0.8, 0.2, 1), size_hint_y=None, height=dp(30)))
        
        # Dropdown for selecting piece
        self.spinner = Spinner(
            text='King',
            values=('King', 'Queen', 'Rook', 'Bishop', 'Knight', 'Pawn 1', 'Pawn 2', 'Pawn 3', 'Pawn 4'),
            size_hint_y=None, height=dp(40),
            background_color=(0.2, 0.2, 0.3, 1)
        )
        self.spinner.bind(text=self.on_piece_select)
        self.add_widget(self.spinner)
        
        # Piece Image
        self.img = Image(size_hint_y=None, height=dp(90), allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)
        
        # Stats Label
        self.stats_lbl = Label(text="", markup=True, font_size='14sp', size_hint_y=None, height=dp(40))
        self.add_widget(self.stats_lbl)
        
        # Load default
        self.on_piece_select(self.spinner, 'King')
        
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]
        
    def on_piece_select(self, instance, text):
        # Map selection to Class and filename
        pieces_map = {
            'King': (King, 'king'), 'Queen': (Queen, 'queen'), 'Rook': (Rook, 'rook'),
            'Knight': (Knight, 'knight'), 'Bishop': (Bishop, 'bishop'),
            'Pawn 1': (Pawn, 'pawn1'), 'Pawn 2': (Pawn, 'pawn2'), 'Pawn 3': (Pawn, 'pawn3'), 'Pawn 4': (Pawn, 'pawn4')
        }
        cls, filename = pieces_map[text]
        dummy = cls('white', self.faction_id) # Instantiate dummy piece to get exact stats
        
        # ✨ FIX: อัปเดต Path ให้ใช้ระบบใหม่ และชี้ไปที่ /1base/
        self.img.source = f"assets/pieces/{self.faction_id}/white/1base/{filename}.png"
        self.stats_lbl.text = f"Points: [b][color=ff5555]{dummy.base_points}[/color][/b] | Coins: [b][color=ffff55]{dummy.coins}[/color][/b]"

class CoinChanceBox(BoxLayout):
    def __init__(self, img_path, percentage, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=None, width=dp(80), **kwargs)
        self.add_widget(Image(source=img_path, size_hint_y=None, height=dp(40)))
        self.add_widget(Label(text=percentage, font_size='13sp', halign='center', markup=True))

class CrashLogicCard(BoxLayout):
    def __init__(self, faction, chances, special_rule=None, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter('height'))
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 0.8)
            self.bg = RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        title = Label(text=f"[b][color=d4af37]{faction}[/color][/b]", markup=True, font_size='18sp', size_hint_y=None, height=dp(30), halign='left')
        title.bind(size=title.setter('text_size'))
        self.add_widget(title)
        
        coin_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(60))
        for img, pct in chances:
            coin_layout.add_widget(CoinChanceBox(img, pct))
        coin_layout.add_widget(Label()) # spacer
        self.add_widget(coin_layout)
        
        if special_rule:
            rule_lbl = Label(text=f"[color=00ffaa]Special Rule:[/color] {special_rule}", markup=True, font_size='14sp', halign='left', size_hint_y=None, height=dp(30))
            rule_lbl.bind(size=rule_lbl.setter('text_size'))
            self.add_widget(rule_lbl)
            
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

class ItemCard(BoxLayout):
    def __init__(self, item, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None, height=dp(180), **kwargs)
        with self.canvas.before:
            Color(0.1, 0.15, 0.2, 0.8)
            self.bg = RoundedRectangle(radius=[dp(8)])
            Color(0.4, 0.4, 0.5, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)], width=1)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        self.add_widget(Image(source=item.image_path, size_hint_y=None, height=dp(60)))
        self.add_widget(Label(text=f"[b][color=ffdd55]{item.name}[/color][/b]", markup=True, font_size='15sp', size_hint_y=None, height=dp(25)))
        
        desc_lbl = Label(text=item.description, font_size='12sp', halign='center', valign='top', markup=True)
        desc_lbl.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        self.add_widget(desc_lbl)
        
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(8)]

class EncyclopediaPopup(ModalView):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.95, 0.95), background_color=(0, 0, 0, 0.85), auto_dismiss=True, **kwargs)
        
        root_box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with root_box.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.83, 0.68, 0.21, 1)
            self.border_line = Line(rounded_rectangle=[root_box.x, root_box.y, root_box.width, root_box.height, dp(15)], width=2)
        root_box.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header (Title + Close Button)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        header.add_widget(Label(text="[b]GAME ENCYCLOPEDIA[/b]", markup=True, font_size='24sp', color=(1, 0.8, 0.2, 1), halign='left'))
        close_btn = Button(text="[b]X[/b]", markup=True, size_hint_x=None, width=dp(40), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        root_box.add_widget(header)
        
        # Scrollable Content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(30), padding=[0, 0, dp(10), 0])
        content.bind(minimum_height=content.setter('height'))
        
        # ------------------ SECTION 1: LEGION ------------------
        content.add_widget(self._make_title("1. LEGION FACTIONS"))
        legion_grid = GridLayout(cols=5, spacing=dp(10), size_hint_y=None, height=dp(240))
        
        # ✨ FIX: อัปเดตรายชื่อเผ่าให้ตรงกับระบบใหม่ (เพิ่ม Bandit เข้ามาด้วย)
        for f in ['The Knight Company', 'The Chaos Mankind', 'The Deep Anomaly', 'The Ancient Runes']:
            legion_grid.add_widget(FactionCard(f))
        content.add_widget(legion_grid)
        
        hidden_passive_text = "[i][color=aaaaaa]Hidden Passive: Bonus Coins (+1) | Bonus Points (+2/+3) | Reduce Coins (-1) | Reduce Points (-1/-2)[/color][/i]"
        content.add_widget(Label(text=hidden_passive_text, markup=True, font_size='14sp', size_hint_y=None, height=dp(20)))
        
        # ------------------ SECTION 2: CRASH LOGIC ------------------
        content.add_widget(self._make_title("2. CRASH LOGIC"))
        crash_box = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        crash_box.bind(minimum_height=crash_box.setter('height'))
        
        # ✨ FIX: อัปเดตชื่อเผ่าในส่วนนี้
        crash_box.add_widget(CrashLogicCard("The Knight Company", [("assets/coin/coin2.png", "50%"), ("assets/coin/coin8.png", "49.995%"), ("assets/coin/coin9.png", "0.005%")]))
        crash_box.add_widget(CrashLogicCard("The Chaos Mankind", [("assets/coin/coin2.png", "30%"), ("assets/coin/coin3.png", "57.2%"), ("assets/coin/coin4.png", "11.76%"), ("assets/coin/coin5.png", "1.04%")]))
        crash_box.add_widget(CrashLogicCard("The Deep Anomaly", [("assets/coin/coin1.png", "40%"), ("assets/coin/coin6.png", "57.6%"), ("assets/coin/coin7.png", "2.4%")], special_rule="If Tails (-3) > 1 coin, convert -3 to +3 points."))
        crash_box.add_widget(CrashLogicCard("The Ancient Runes", [("assets/coin/coin2.png", "50%"), ("assets/coin/coin3.png", "50%")], special_rule="If 3 Heads: +3 | 6 Heads: +3 | 9 Heads: +3 points."))
        content.add_widget(crash_box)
        
        # ------------------ SECTION 3: ITEMS ------------------
        content.add_widget(self._make_title("3. ARTIFACTS & ITEMS"))
        items_grid = GridLayout(cols=3, spacing=dp(10), size_hint_y=None)
        items_grid.bind(minimum_height=items_grid.setter('height'))
        for item in ITEM_DATABASE.values():
            items_grid.add_widget(ItemCard(item))
        content.add_widget(items_grid)
        
        scroll.add_widget(content)
        root_box.add_widget(scroll)
        self.add_widget(root_box)
        
    def _make_title(self, text):
        lbl = Label(text=f"[b][color=ffffff]{text}[/color][/b]", markup=True, font_size='20sp', size_hint_y=None, height=dp(40), halign='left')
        lbl.bind(size=lbl.setter('text_size'))
        return lbl
        
    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(15)]