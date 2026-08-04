# components/encyclopedia_dnc_popup.py
import os
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

# นำเข้าคลาสที่เกี่ยวข้องทั้งหมด
from logic.pieces import King, Queen, Rook, Bishop, Knight, Pawn, Levies, Hastati, Menatarm, Praetorian, Royalguard, Prince, Princess
from logic.item_logic import ITEM_DATABASE
# ดึง UI Card เดิมจากหน้า Classic มาใช้ซ้ำเพื่อความสวยงาม
from components.encyclopedia_popup import CrashLogicCard, ItemCard

# ✨ ฟังก์ชันตรวจสอบไฟล์ภาพ ถ้าไม่มีรูปให้ใส่ กากบาท (X) สีแดงแทน
def update_safe_image(container, img_path, **kwargs):
    container.clear_widgets()
    if os.path.exists(img_path):
        container.add_widget(Image(source=img_path, allow_stretch=True, keep_ratio=True, **kwargs))
    else:
        # แสดง X พร้อมข้อความว่าไม่มีโมเดล
        lbl = Label(text="[b][color=ff4444]X[/color][/b]\n[size=11sp]No Model[/size]", markup=True, halign='center', **kwargs)
        container.add_widget(lbl)

class DNCFactionCard(BoxLayout):
    def __init__(self, faction_name, **kwargs):
        # ✨ FIX: เพิ่ม size_hint_y=None และ height=dp(300) เพื่อไม่ให้ Kivy ยุบการ์ดทิ้ง
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None, height=dp(300), **kwargs)
        self.faction_name = faction_name
        self.faction_id = faction_name.lower()
        
        with self.canvas.before:
            Color(0.1, 0.15, 0.15, 1)
            self.bg = RoundedRectangle(radius=[dp(10)])
            Color(0.2, 0.6, 0.4, 1)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(10)], width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Faction Title
        self.add_widget(Label(text=f"[b]{faction_name}[/b]", markup=True, font_size='16sp', color=(0.2, 0.8, 0.4, 1), size_hint_y=None, height=dp(30)))
        
        # 1. Dropdown for selecting piece
        self.piece_spinner = Spinner(
            text='Pawn',
            values=('King', 'Queen', 'Rook', 'Bishop', 'Knight', 'Pawn', 'Levies', 'Hastati', 'Menatarm', 'Praetorian', 'Royalguard', 'Prince', 'Princess'),
            size_hint_y=None, height=dp(35),
            background_color=(0.15, 0.3, 0.2, 1)
        )
        self.piece_spinner.bind(text=self.update_info)
        self.add_widget(self.piece_spinner)

        # 2. Dropdown for Upgrades (Filter)
        self.upg_spinner = Spinner(
            text='Normal (Base)',
            values=('Normal (Base)', 'Upgrade ATK', 'Upgrade DEF', 'Reroll Hidden Passive', 'Roll 2nd Passive'),
            size_hint_y=None, height=dp(35),
            background_color=(0.3, 0.2, 0.4, 1)
        )
        self.upg_spinner.bind(text=self.update_info)
        self.add_widget(self.upg_spinner)
        
        # คอนเทนเนอร์สำหรับใส่รูป (เพื่อรองรับระบบ Safe Image)
        self.img_container = BoxLayout(size_hint_y=None, height=dp(90))
        self.add_widget(self.img_container)
        
        # Stats Label (Coins, ATK, DEF)
        self.stats_lbl = Label(text="", markup=True, font_size='13sp', halign='center', size_hint_y=None, height=dp(50))
        self.add_widget(self.stats_lbl)
        
        self.update_info(None, None)
        
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]
        
    def update_info(self, instance, text):
        pieces_map = {
            'King': (King, 'king'), 'Queen': (Queen, 'queen'), 'Rook': (Rook, 'rook'),
            'Knight': (Knight, 'knight'), 'Bishop': (Bishop, 'bishop'), 'Pawn': (Pawn, 'pawn'),
            'Levies': (Levies, 'levies'), 'Hastati': (Hastati, 'hastati'), 'Menatarm': (Menatarm, 'menatarm'),
            'Praetorian': (Praetorian, 'praetorian'), 'Royalguard': (Royalguard, 'royalguard'),
            'Prince': (Prince, 'prince'), 'Princess': (Princess, 'princess')
        }
        
        p_name = self.piece_spinner.text
        upg = self.upg_spinner.text
        
        cls, filename = pieces_map[p_name]
        dummy = cls('white', self.faction_id) 
        
        # Base Stats
        atk = dummy.base_atk
        def_ = dummy.base_def
        coins = dummy.coins
        
        # Upgrade Logic & Folder mapping
        folder = "1base"
        if upg == 'Upgrade ATK':
            atk += 2
            folder = "2upATK"
        elif upg == 'Upgrade DEF':
            def_ += 2
            folder = "3upDEF"
        elif upg == 'Reroll Hidden Passive':
            folder = "4up_rehidden"
        elif upg == 'Roll 2nd Passive':
            folder = "5up_reroll_ATK_DEF"
            
        # Handle variants for specific pieces
        if filename in ['pawn', 'hastati', 'levies']:
            filename += '1'
            
        img_path = f"assets/pieces/{self.faction_id}/white/{folder}/{filename}.png"
        
        # ✨ ใช้ฟังก์ชัน Safe Image (จะแสดง ❌ ถ้าไม่มีไฟล์รูปรหัสนี้)
        update_safe_image(self.img_container, img_path, size_hint_y=None, height=dp(90))
        
        self.stats_lbl.text = f"[color=ffff00]Coins: {coins}[/color]\n[color=ff5555]ATK: {atk}[/color] | [color=5555ff]DEF: {def_}[/color]"

class DNCBuildingCard(BoxLayout):
    def __init__(self, build_id, build_name, base_desc, is_special=False, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None, height=dp(250), **kwargs)
        self.build_id = build_id
        self.base_desc = base_desc
        
        with self.canvas.before:
            Color(0.15, 0.1, 0.1, 1)
            self.bg = RoundedRectangle(radius=[dp(10)])
            border_c = (0.8, 0.5, 0.2, 1) if not is_special else (0.8, 0.2, 0.8, 1)
            Color(*border_c)
            self.border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(10)], width=1.5)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Title
        self.add_widget(Label(text=f"[b]{build_name}[/b]", markup=True, font_size='16sp', size_hint_y=None, height=dp(30)))
        
        # Dropdown for Upgrades
        self.lvl_spinner = Spinner(
            text='Level 1',
            values=('Level 1', 'Level 2', 'Level 3'),
            size_hint_y=None, height=dp(35),
            background_color=(0.5, 0.3, 0.2, 1)
        )
        self.lvl_spinner.bind(text=self.update_info)
        self.add_widget(self.lvl_spinner)
        
        # คอนเทนเนอร์สำหรับรูปสิ่งก่อสร้าง (รองรับ Safe Image)
        self.img_container = BoxLayout(size_hint_y=None, height=dp(80))
        self.add_widget(self.img_container)
        
        # Description
        self.desc_lbl = Label(text="", markup=True, font_size='13sp', halign='center', valign='top')
        self.desc_lbl.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        self.add_widget(self.desc_lbl)
        
        self.update_info(None, 'Level 1')
        
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]
        
    def update_info(self, instance, text):
        lvl_map = {'Level 1': 1, 'Level 2': 2, 'Level 3': 3}
        lvl = lvl_map[text]
        
        # Image logic
        folder = "base1" if lvl == 1 else ("up1" if lvl == 2 else "up2")
        img_path = f"assets/structure/addon/{folder}/{self.build_id}.png"
        
        # ✨ ใช้ฟังก์ชัน Safe Image ตรวจสอบก่อนโหลดรูป
        update_safe_image(self.img_container, img_path, size_hint_y=None, height=dp(80))
        
        # Dynamic Description Logic
        desc = f"[color=dddddd]{self.base_desc}[/color]\n"
        
        if self.build_id == 'farm':
            desc += f"[b][color=00ff00]Income: +{lvl * 2} Tax / Turn[/color][/b]"
        elif self.build_id == 'tavern':
            ranks = ["Militia", "Militia & Regulars", "Militia, Regs, & Elites"]
            desc += f"[b][color=00ffff]Unlocks: {ranks[lvl-1]}[/color][/b]"
        elif self.build_id == 'mine':
            desc += f"[b][color=00ff00]Income: +{lvl * 3} Tax / Turn[/color][/b]"
        elif self.build_id == 'blacksmith':
            desc += f"[b][color=5555ff]Effect: +{lvl} Base DEF to Recruits[/color][/b]"
        elif self.build_id == 'weaponsmith':
            desc += f"[b][color=ff5555]Effect: +{lvl} Base ATK to Recruits[/color][/b]"
        elif self.build_id == 'guard':
            guard_tier = ["Militia Guards", "Regular Guards", "Elite Guards"]
            desc += f"[b][color=ffaa00]Spawns: {guard_tier[lvl-1]} on Defense[/color][/b]"
        elif self.build_id == 'statue': 
            reductions = ["-1 Cost", "-2 Cost", "-50% Cost (Max)"]
            desc += f"[b][color=ffff00]Discount: {reductions[lvl-1]}[/color][/b]"
            
        self.desc_lbl.text = desc

class EncyclopediaDNCPopup(ModalView):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.95, 0.95), background_color=(0, 0, 0, 0.85), auto_dismiss=True, **kwargs)
        
        root_box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with root_box.canvas.before:
            Color(0.05, 0.08, 0.05, 1)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.2, 0.8, 0.4, 1)
            self.border_line = Line(rounded_rectangle=[root_box.x, root_box.y, root_box.width, root_box.height, dp(15)], width=2.5)
        root_box.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        header.add_widget(Label(text="[b]DNC ENCYCLOPEDIA[/b]", markup=True, font_size='24sp', color=(0.2, 1, 0.4, 1), halign='left'))
        close_btn = Button(text="[b]X[/b]", markup=True, size_hint_x=None, width=dp(40), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        root_box.add_widget(header)
        
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(30), padding=[0, 0, dp(10), 0])
        content.bind(minimum_height=content.setter('height'))
        
        # ------------------ SECTION 1: DNC UNITS ------------------
        content.add_widget(self._make_title("1. FACTION UNITS & UPGRADES"))
        
        # ปล่อยความสูงยืดหยุ่นด้วย minimum_height
        legion_grid = GridLayout(cols=4, spacing=dp(10), size_hint_y=None)
        legion_grid.bind(minimum_height=legion_grid.setter('height'))
        
        for f in ['The Knight Company', 'The Chaos Mankind', 'The Deep Anomaly', 'The Ancient Runes']:
            legion_grid.add_widget(DNCFactionCard(f))
        content.add_widget(legion_grid)
        
        # ------------------ SECTION 2: BUILDINGS & ADDONS ------------------
        content.add_widget(self._make_title("2. BUILDINGS & INFRASTRUCTURE"))
        
        # 2.1 Guaranteed Buildings
        content.add_widget(Label(text="[b]Standard Base Buildings[/b]", markup=True, font_size='16sp', size_hint_y=None, height=dp(20)))
        
        std_build_grid = GridLayout(cols=4, spacing=dp(10), size_hint_y=None)
        std_build_grid.bind(minimum_height=std_build_grid.setter('height'))
        
        std_build_grid.add_widget(DNCBuildingCard('farm', 'Farm', 'Essential agricultural structure for base income.'))
        std_build_grid.add_widget(DNCBuildingCard('tavern', 'Tavern', 'Gathering place to hire new recruits and mercenaries.'))
        content.add_widget(std_build_grid)
        
        # 2.2 Special Buildings
        content.add_widget(Label(text="[b]Special Random Buildings (1 Per Village)[/b]", markup=True, font_size='16sp', size_hint_y=None, height=dp(20), color=(0.8, 0.6, 1, 1)))
        
        spc_build_grid = GridLayout(cols=4, spacing=dp(10), size_hint_y=None)
        spc_build_grid.bind(minimum_height=spc_build_grid.setter('height'))
        
        spc_build_grid.add_widget(DNCBuildingCard('mine', 'Mine', 'Extracts precious resources from the earth.', is_special=True))
        spc_build_grid.add_widget(DNCBuildingCard('blacksmith', 'Blacksmith', 'Forges sturdy armors for new recruits.', is_special=True))
        spc_build_grid.add_widget(DNCBuildingCard('weaponsmith', 'Weaponsmith', 'Crafts deadly weapons for new recruits.', is_special=True))
        spc_build_grid.add_widget(DNCBuildingCard('guard', 'Guard Post', 'Militia outpost to defend against incoming raids.', is_special=True))
        spc_build_grid.add_widget(DNCBuildingCard('statue', 'Hero Statue', 'Inspires locals, making recruitment cheaper.', is_special=True))
        content.add_widget(spc_build_grid)

        # ------------------ SECTION 3: CRASH LOGIC ------------------
        content.add_widget(self._make_title("3. CRASH LOGIC"))
        crash_box = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        crash_box.bind(minimum_height=crash_box.setter('height'))
        
        crash_box.add_widget(CrashLogicCard("The Knight Company", [("assets/coin/coin2.png", "50%"), ("assets/coin/coin8.png", "49.995%"), ("assets/coin/coin9.png", "0.005%")]))
        crash_box.add_widget(CrashLogicCard("The Chaos Mankind", [("assets/coin/coin2.png", "30%"), ("assets/coin/coin3.png", "57.2%"), ("assets/coin/coin4.png", "11.76%"), ("assets/coin/coin5.png", "1.04%")]))
        crash_box.add_widget(CrashLogicCard("The Deep Anomaly", [("assets/coin/coin1.png", "40%"), ("assets/coin/coin6.png", "57.6%"), ("assets/coin/coin7.png", "2.4%")], special_rule="If the number of Tails is even, convert negative points to positive (+3). If odd, keep them negative (-3)."))
        crash_box.add_widget(CrashLogicCard("The Ancient Runes", [("assets/coin/coin2.png", "50%"), ("assets/coin/coin3.png", "50%")], special_rule="If 3 Heads: +3 | 6 Heads: +3 | 9 Heads: +3 points."))
        content.add_widget(crash_box)
        
        # ------------------ SECTION 4: ITEMS ------------------
        content.add_widget(self._make_title("4. ARTIFACTS & ITEMS"))
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