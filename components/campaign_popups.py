# components/campaign_popups.py
import math

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from components.campaign_cards import RecruitCard
from logic.image_utils import safe_piece_path
import os

def get_addon_img(addon, lvl):
    folder = "base1" if lvl <= 1 else ("up1" if lvl == 2 else "up2")
    return f"assets/structure/addon/{folder}/{addon}.png"

class BuildCard(ButtonBehavior, FloatLayout):
    def __init__(self, title, desc, cost, img_path, on_click_cb, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(160), dp(110)), **kwargs)
        self.bind(on_release=lambda x: on_click_cb())
        
        with self.canvas.before:
            Color(0.15, 0.25, 0.15, 1)
            self.bg = RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        self.add_widget(Image(source=img_path, size_hint=(0.35, 0.8), pos_hint={'x': 0.05, 'center_y': 0.5}, allow_stretch=True, keep_ratio=True))
        
        lbl_box = BoxLayout(orientation='vertical', size_hint=(0.55, 0.9), pos_hint={'right': 0.95, 'center_y': 0.5})
        lbl_box.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='14sp', halign='center'))
        lbl_box.add_widget(Label(text=f"[size=11sp]{desc}[/size]", markup=True, halign='center'))
        
        # Cost with Tax icon using BoxLayout
        cost_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20), spacing=dp(3))
        tax_img = Image(source='assets/icon_effect/tax.png', size_hint_x=None, width=16)
        tax_img.texture.mag_filter = 'nearest' if tax_img.texture else 'linear'
        cost_box.add_widget(tax_img)
        cost_box.add_widget(Label(text=f"{cost}", font_size='12sp', halign='center', color=(1, 1, 0, 1)))
        lbl_box.add_widget(cost_box)
        
        self.add_widget(lbl_box)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size

def create_subvillage_nav(panel, popup_instance):
    nav_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(5))
    if panel.current_node.node_type != 'castle': 
        return nav_box
        
    btn_main = Button(text="Main Castle", font_size='13sp', background_color=(0.5, 0.5, 0.2, 1) if panel.active_sub_village is None else (0.2, 0.2, 0.2, 1))
    btn_main.bind(on_release=lambda x: popup_instance.change_sv(None))
    nav_box.add_widget(btn_main)
    
    for sv in panel.current_node.sub_villages:
        btn_v = Button(text=f"Village {sv['id']}", font_size='13sp', background_color=(0.5, 0.5, 0.2, 1) if panel.active_sub_village == sv else (0.2, 0.2, 0.2, 1))
        btn_v.bind(on_release=lambda x, v=sv: popup_instance.change_sv(v))
        nav_box.add_widget(btn_v)
        
    return nav_box

# ----------------- Recruit Popup -----------------
class RecruitPopup(ModalView):
    def __init__(self, panel, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(0,0,0,0.8), auto_dismiss=True, **kwargs)
        self.panel = panel
        self.app = panel.app
        self.node = panel.current_node
        self.active_sv = panel.active_sub_village
        
        self.root_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with self.root_box.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.3, 0.8, 0.3, 1)
            self.border_line = Line(rounded_rectangle=[self.root_box.x, self.root_box.y, self.root_box.width, self.root_box.height, dp(12)], width=2)
        self.root_box.bind(pos=self._update_bg, size=self._update_bg)
        
        self.header = BoxLayout(size_hint_y=None, height=dp(40))
        self.title = Label(text="[b]RECRUITMENT CAMP[/b]", markup=True, font_size='22sp', halign='left', color=(0.3, 0.8, 0.3, 1), size_hint_x=0.4)
        
        # แทนที่ Label เดิมด้วย BoxLayout สำหรับแสดงค่า Tax
        self.status_box = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=dp(5))
        
        close_btn = Button(text="CLOSE", size_hint_x=0.2, background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        
        self.header.add_widget(self.title)
        self.header.add_widget(self.status_box)
        self.header.add_widget(close_btn)
        self.root_box.add_widget(self.header)
        
        self.nav_container = BoxLayout(size_hint_y=None, height=dp(40))
        self.root_box.add_widget(self.nav_container)
        
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_y=True, do_scroll_x=False)
        self.content_grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15), padding=dp(10))
        self.content_grid.bind(minimum_height=self.content_grid.setter('height'))
        self.scroll.add_widget(self.content_grid)
        
        self.root_box.add_widget(self.scroll)
        self.add_widget(self.root_box)
        self.refresh_ui()
        
    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]
        
    def change_sv(self, sv):
        self.app.play_click_sound()
        self.panel.active_sub_village = sv
        self.refresh_ui()

    def refresh_ui(self):
        self.nav_container.clear_widgets()
        self.nav_container.add_widget(create_subvillage_nav(self.panel, self))
        self.content_grid.clear_widgets()
        
        tax = self.app.tax_points.get(self.node.faction, 0)
        addons = self.panel.get_active_addons()
        tav_lvl = addons.get('tavern', 1)
        
        # อัปเดต Status Box (Tax + Tavern Level)
        self.status_box.clear_widgets()
        tax_img = Image(source='assets/icon_effect/tax.png', size_hint_x=None, width=dp(24))
        self.status_box.add_widget(tax_img)
        self.status_box.add_widget(Label(text=f"{tax} | Tavern Lvl: {tav_lvl}", font_size='16sp', color=(0, 1, 0, 1), halign='left'))
        
        shop = self.panel.active_sub_village['shop_recruits'] if self.panel.active_sub_village else getattr(self.node, 'shop_recruits', {})
        
        def build_row(row_key):
            if row_key not in shop: return
            row_data = shop[row_key]
            title = row_data.get('title', f"Row: {row_key}")
            req_lvl = row_data['req_lvl']
            items = row_data['data']
            
            row_title = Label(text=f"[b]{title}[/b]", markup=True, size_hint_y=None, height=dp(30), halign='center', color=(0.9,0.8,0.2,1))
            self.content_grid.add_widget(row_title)
            
            if tav_lvl < req_lvl:
                locked_btn = Button(text=f"[b]Unlock: Tavern Lvl {req_lvl}[/b]", markup=True, background_color=(0.3, 0.1, 0.1, 1), size_hint_y=None, height=dp(140))
                self.content_grid.add_widget(locked_btn)
                return

            # ปรับความสูงของ row_box ขึ้นนิดหน่อยเพื่อเว้นที่ให้ตัวหนังสือบอกทรัพยากร
            row_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=None, height=dp(160))
            row_box.add_widget(Widget())  
            for idx, p_data in enumerate(items):
                if p_data is None:
                    card = RecruitCard(None, 0, self.node.faction, self.app, None)
                    row_box.add_widget(card)
                else:
                    p_name = p_data['name']
                    base_cost = p_data['cost']
                    final_cost = self.panel.get_discounted_price(base_cost, addons)
                    cb = lambda n, c, r=row_key, i=idx: self.on_buy_piece(n, c, r, i)
                    
                    # ห่อ Card ด้วย BoxLayout แนวดิ่งเพื่อใส่ข้อความไว้ด้านล่าง
                    wrap_box = BoxLayout(orientation='vertical', size_hint=(None, 1), width=dp(140))
                    
                    card = RecruitCard(p_name, final_cost, self.node.faction, self.app, cb)
                    wrap_box.add_widget(card)
                    
                    # กำหนดข้อความความต้องการทรัพยากร
                    req_text = ""
                    p_lower = p_name.lower()
                    if p_lower in ['pawn', 'levies']:
                        req_text = "2 Sup" # แสดงแค่อาหาร
                    elif p_lower in ['knight', 'bishop', 'rook']:
                        req_text = "2 Sup, 1 Wep T1"
                    elif p_lower in ['hastati', 'menatarm']:
                        req_text = "2 Sup, 1 Wep T2"
                    elif p_lower in ['royalguard', 'praetorian']:
                        req_text = "3 Sup, 1 Wep T3"
                        
                    if req_text:
                        lbl_req = Label(text=f"[size=11sp][color=00ffff]{req_text}[/color][/size]", markup=True, size_hint_y=None, height=dp(20))
                        wrap_box.add_widget(lbl_req)
                        
                    row_box.add_widget(wrap_box)
            row_box.add_widget(Widget())  
            self.content_grid.add_widget(row_box)
            
        build_row('row1'); build_row('row2'); build_row('row3'); build_row('row4'); build_row('row5')
        
    def on_buy_piece(self, piece_name, cost, row_key, idx):
        if self.panel.buy_piece(piece_name, cost, row_key, idx):
            self.refresh_ui()

# ----------------- Build Popup -----------------
class BuildPopup(ModalView):
    def __init__(self, panel, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), background_color=(0,0,0,0.8), auto_dismiss=True, **kwargs)
        self.panel = panel
        self.app = panel.app
        self.node = panel.current_node
        self.active_sv = panel.active_sub_village
        self.current_tab = 'manage' # กำหนด Tab เริ่มต้น
        
        self.root_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with self.root_box.canvas.before:
            Color(0.15, 0.1, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.5, 0.2, 1)
            self.border_line = Line(rounded_rectangle=[self.root_box.x, self.root_box.y, self.root_box.width, self.root_box.height, dp(12)], width=2)
        self.root_box.bind(pos=self._update_bg, size=self._update_bg)
        
        # --- ส่วน Header ---
        self.header = BoxLayout(size_hint_y=None, height=dp(40))
        self.title = Label(text="[b]CONSTRUCTION[/b]", markup=True, font_size='22sp', halign='left', color=(0.8, 0.5, 0.2, 1), size_hint_x=0.4)
        
        self.status_box = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=dp(5))
        
        close_btn = Button(text="CLOSE", size_hint_x=0.2, background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        
        self.header.add_widget(self.title)
        self.header.add_widget(self.status_box)
        self.header.add_widget(close_btn)
        self.root_box.add_widget(self.header)
        
        # --- ส่วนปุ่มสลับ Tab (MANAGE / UPGRADE) ---
        self.tab_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        
        self.btn_tab_manage = Button(text="[b]MANAGE[/b]", markup=True, background_color=(0.3, 0.5, 0.8, 1))
        self.btn_tab_manage.bind(on_release=lambda x: self.switch_tab('manage'))
        
        self.btn_tab_upgrade = Button(text="[b]UPGRADE[/b]", markup=True, background_color=(0.2, 0.2, 0.2, 1))
        self.btn_tab_upgrade.bind(on_release=lambda x: self.switch_tab('upgrade'))
        
        self.tab_box.add_widget(self.btn_tab_manage)
        self.tab_box.add_widget(self.btn_tab_upgrade)
        self.root_box.add_widget(self.tab_box)
        
        # --- แถบตัวเลือก Sub-village (แสดงเฉพาะโหมด Upgrade) ---
        self.nav_container = BoxLayout(size_hint_y=None, height=dp(40))
        self.root_box.add_widget(self.nav_container)
        
        # --- พื้นที่เนื้อหา ---
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_y=True, do_scroll_x=False)
        self.content_grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        self.content_grid.bind(minimum_height=self.content_grid.setter('height'))
        self.scroll.add_widget(self.content_grid)
        
        self.root_box.add_widget(self.scroll)
        self.add_widget(self.root_box)
        self.refresh_ui()
        
    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]

    def switch_tab(self, tab_name):
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        self.current_tab = tab_name
        # อัปเดตสีปุ่ม Tab
        if tab_name == 'manage':
            self.btn_tab_manage.background_color = (0.3, 0.5, 0.8, 1)
            self.btn_tab_upgrade.background_color = (0.2, 0.2, 0.2, 1)
        else:
            self.btn_tab_manage.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_upgrade.background_color = (0.8, 0.5, 0.2, 1)
        self.refresh_ui()
        
    def change_sv(self, sv):
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        self.panel.active_sub_village = sv
        self.refresh_ui()

    def toggle_addon_mode(self, addons, key, instance):
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        # สลับค่าโหมด
        current_mode = addons.get(key, 'tax')
        addons[key] = 'resources' if current_mode == 'tax' else 'tax'
        self.refresh_ui()

    def refresh_ui(self):
        self.nav_container.clear_widgets()
        self.content_grid.clear_widgets()
        
        tax = self.app.tax_points.get(self.node.faction, 0)
        
        # อัปเดต Status Box (ช่องเงิน)
        self.status_box.clear_widgets()
        tax_img = Image(source='assets/icon_effect/tax.png', size_hint_x=None, width=dp(24))
        self.status_box.add_widget(tax_img)
        self.status_box.add_widget(Label(text=f"{tax}", font_size='16sp', color=(0, 1, 0, 1), halign='left'))
        
        econ_enabled = getattr(self.app, 'selected_economic_system', False)

        b_state = getattr(self.node, 'building_state', None)

        # ========================================================
        # 🟢 TAB: MANAGE
        # ========================================================
        if self.current_tab == 'manage':
            self.nav_container.height = 0  # ซ่อนปุ่มเลือกหมู่บ้านย่อย
            self.nav_container.opacity = 0
            
            if not econ_enabled:
                self.content_grid.add_widget(Label(text="[color=ffaa00]Economic System is disabled in this match.[/color]", markup=True, size_hint_y=None, height=dp(40)))
                return

            # Helper สำหรับสร้างแต่ละแถว (Row) ให้เรียงลงมา
            def build_manage_row(title, addons):
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10), padding=dp(5))
                
                # พื้นหลังของแถว
                with row.canvas.before:
                    Color(0.2, 0.2, 0.25, 1)
                    bg = RoundedRectangle(radius=[dp(8)])
                def update_bg(instance, value, bg=bg):
                    bg.pos = instance.pos
                    bg.size = instance.size
                row.bind(pos=update_bg, size=update_bg)
                
                row.add_widget(Label(text=f"[b]{title}[/b]", markup=True, size_hint_x=0.4))
                
                # 🌾 ปุ่มจัดการ Farm
                if addons.get('farm', 0) > 0:
                    f_mode = addons.get('farm_mode', 'tax')
                    f_text = "FARM: TAX" if f_mode == 'tax' else "FARM: RES"
                    f_color = (0.8, 0.6, 0.2, 1) if f_mode == 'tax' else (0.2, 0.6, 0.2, 1)
                    btn_farm = Button(text=f_text, background_color=f_color, size_hint_x=0.3)
                    btn_farm.bind(on_release=lambda x, a=addons: self.toggle_addon_mode(a, 'farm_mode', x))
                    row.add_widget(btn_farm)
                else:
                    row.add_widget(Widget(size_hint_x=0.3)) # เว้นว่างถ้าไม่มีฟาร์ม

                # ⛏️ ปุ่มจัดการ Mine
                if addons.get('special') == 'mine':
                    m_mode = addons.get('mine_mode', 'tax')
                    m_text = "MINE: TAX" if m_mode == 'tax' else "MINE: ORE"
                    m_color = (0.8, 0.6, 0.2, 1) if m_mode == 'tax' else (0.5, 0.5, 0.5, 1)
                    btn_mine = Button(text=m_text, background_color=m_color, size_hint_x=0.3)
                    btn_mine.bind(on_release=lambda x, a=addons: self.toggle_addon_mode(a, 'mine_mode', x))
                    row.add_widget(btn_mine)
                else:
                    row.add_widget(Widget(size_hint_x=0.3)) # เว้นว่างถ้าไม่มีเหมือง

                self.content_grid.add_widget(row)

            # 1. วาดแถวของฐานหลัก (Main Base)
            main_addons = getattr(self.node, 'addons', {'farm': 1, 'tavern': 1, 'special': None, 'special_lvl': 0})
            build_manage_row("Main Base", main_addons)
            
            # 2. วาดแถวของหมู่บ้านย่อยเรียงลงมา (ถ้าเป็น Castle)
            if self.node.node_type == 'castle' and hasattr(self.node, 'sub_villages'):
                for sv in self.node.sub_villages:
                    build_manage_row(f"Village {sv['id']}", sv['addons'])

            # --- วาดระบบ Market (ถ้ามี) ---
            if self.node.node_type == 'castle':
                if b_state == 'building_market':
                    self.content_grid.add_widget(Label(text="[color=ffff00]Market is under construction (1 Turn)...[/color]", markup=True, size_hint_y=None, height=dp(40)))
                elif b_state == 'building_makerspace':
                    self.content_grid.add_widget(Label(text="[color=ffff00]Makerspace is under construction (1 Turn)...[/color]", markup=True, size_hint_y=None, height=dp(40)))
                elif b_state == 'building_wallbuilder': # 🟢 เพิ่มแจ้งเตือนกำลังสร้างกำแพง
                    self.content_grid.add_widget(Label(text="[color=ffff00]Wallbuilder is under construction (1 Turn)...[/color]", markup=True, size_hint_y=None, height=dp(40)))
                elif b_state == 'destroying':
                    self.content_grid.add_widget(Label(text="[color=ff0000]Building is being demolished (1 Turn)...[/color]", markup=True, size_hint_y=None, height=dp(40)))
                # --- UI ของ Market ---
                elif b_state == 'market':
                    # สร้าง Header ตลาด
                    m_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
                    m_header.add_widget(Label(text="[b][color=d4af37]GRAND MARKET[/color][/b]", markup=True, halign='left'))
                    btn_destroy = Button(text="DESTROY", background_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.3)
                    btn_destroy.bind(on_release=self.destroy_castle_structure)
                    m_header.add_widget(btn_destroy)
                    self.content_grid.add_widget(m_header)
                    
                    # ลิสต์รายการสินค้าของ Market
                    rates = getattr(self.node, 'market_rates', {})
                    for r_key, r_val in rates.items():
                        r_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(5))
                        r_box.add_widget(Label(text=f"{r_key.capitalize()} (Rate: {r_val})", size_hint_x=0.4))
                        
                        btn_sell = Button(text=f"SELL (+{r_val} Tax)", background_color=(0.2, 0.6, 0.2, 1), size_hint_x=0.3)
                        btn_sell.bind(on_release=lambda x, k=r_key, r=r_val: self.trade_market(k, False, r))
                        
                        btn_buy = Button(text=f"BUY (-{r_val} Tax)", background_color=(0.8, 0.4, 0.2, 1), size_hint_x=0.3)
                        btn_buy.bind(on_release=lambda x, k=r_key, r=r_val: self.trade_market(k, True, r))
                        
                        r_box.add_widget(btn_sell)
                        r_box.add_widget(btn_buy)
                        self.content_grid.add_widget(r_box)

                # --- UI ของ Makerspace ---
                elif b_state == 'makerspace':
                    m_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
                    m_header.add_widget(Label(text="[b][color=00ffcc]MAKERSPACE[/color][/b]", markup=True, halign='left'))
                    btn_destroy = Button(text="DESTROY", background_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.3)
                    btn_destroy.bind(on_release=self.destroy_castle_structure)
                    m_header.add_widget(btn_destroy)
                    self.content_grid.add_widget(m_header)
                    
                    # Helper วาดสูตรคราฟต์ของ Makerspace
                    def add_recipe(label_text, cb_name):
                        r_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(5))
                        r_box.add_widget(Label(text=label_text, markup=True, size_hint_x=0.7))
                        btn_craft = Button(text="CRAFT", background_color=(0.2, 0.6, 0.8, 1), size_hint_x=0.3)
                        btn_craft.bind(on_release=lambda x, cb=cb_name: self.craft_item(cb))
                        r_box.add_widget(btn_craft)
                        self.content_grid.add_widget(r_box)

                    add_recipe("2 Coal + 2 Tax [color=00ff00]-> 1 Iron[/color]", 'coal_to_iron')
                    add_recipe("1 Silver + 2 Tax [color=00ff00]-> 1 Iron[/color]", 'silver_to_iron')
                    add_recipe("1 Gold + 2 Tax [color=00ff00]-> 3 Iron[/color]", 'gold_to_iron')
                    add_recipe("2 Wood + 3 Iron [color=00ffff]-> Weapon T1[/color]", 'weapon_t1')
                    add_recipe("4 Wood + 3 Iron [color=00ffff]-> Weapon T2[/color]", 'weapon_t2')
                    add_recipe("6 Wood + 4 Iron [color=00ffff]-> Weapon T3[/color]", 'weapon_t3')

                # --- UI ของ Wallbuilder ---
                elif b_state == 'wallbuilder':
                    m_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
                    m_header.add_widget(Label(text="[b][color=aaaaaa]WALLBUILDER[/color][/b]", markup=True, halign='left'))
                    btn_destroy = Button(text="DESTROY", background_color=(0.8, 0.2, 0.2, 1), size_hint_x=0.3)
                    btn_destroy.bind(on_release=self.destroy_castle_structure)
                    m_header.add_widget(btn_destroy)
                    self.content_grid.add_widget(m_header)
                    
                    # เช็คสถานะ Cooldown ของ Wallbuilder อย่างเดียว
                    cd = getattr(self.node, 'wallbuilder_cooldown', 0)
                    if cd > 0:
                        status_text = f"[color=ff0000]COOLDOWN ({cd} Turns left)[/color]"
                    else:
                        status_text = "[color=00ff00]ACTIVE (70% Block Chance)[/color]"
                        
                    status_lbl = Label(text=f"Status: {status_text}", markup=True, size_hint_y=None, height=dp(30))
                    self.content_grid.add_widget(status_lbl)
                    
        # ========================================================
        # 🔴 TAB: UPGRADE
        # ========================================================
        elif self.current_tab == 'upgrade':
            self.nav_container.height = dp(40)  # โชว์ปุ่มเลือกหมู่บ้านย่อย
            self.nav_container.opacity = 1
            self.nav_container.add_widget(create_subvillage_nav(self.panel, self))
            
            addons = self.panel.get_active_addons()
            
            farm_lvl = addons.get('farm', 1)
            farm_cost = farm_lvl * 5
            if farm_lvl < 3:
                img = get_addon_img('farm', farm_lvl)
                self.content_grid.add_widget(BuildCard("Farm", f"Lvl {farm_lvl} -> {farm_lvl+1}", farm_cost, img, lambda: self.on_upgrade_addon('farm', farm_cost)))
                
            tav_lvl = addons.get('tavern', 1)
            tav_cost = tav_lvl * 6
            if tav_lvl < 3:
                img = get_addon_img('tavern', tav_lvl)
                self.content_grid.add_widget(BuildCard("Tavern", f"Lvl {tav_lvl} -> {tav_lvl+1}", tav_cost, img, lambda: self.on_upgrade_addon('tavern', tav_cost)))
                
            spec = addons.get('special')
            spec_lvl = addons.get('special_lvl', 0)
            if spec: 
                spec_cost = spec_lvl * 8
                if spec_lvl < 3:
                    img = get_addon_img(spec, spec_lvl)
                    self.content_grid.add_widget(BuildCard(spec.capitalize(), f"Lvl {spec_lvl} -> {spec_lvl+1}", spec_cost, img, lambda: self.on_upgrade_addon('special_lvl', spec_cost)))

            # --- วาด Card สร้างสิ่งปลูกสร้างปราสาท ---
            if self.node.node_type == 'castle' and self.panel.active_sub_village is None:
                if b_state is None:
                    # เปลี่ยนเป็น GridLayout เพื่อรองรับตึกจำนวนมากโดยไม่ทำให้ UI เสียทรง
                    grid_b = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
                    grid_b.bind(minimum_height=grid_b.setter('height'))
                    
                    # สร้างตึก Market
                    grid_b.add_widget(BuildCard("Market", "Trade items\nCost: 3 Wood", 3, "assets/icon_effect/tax.png", lambda: self.build_castle_structure('market', 3)))
                    # สร้างตึก Makerspace
                    grid_b.add_widget(BuildCard("Makerspace", "Craft weapons\nCost: 4 Wood", 4, "assets/icon_effect/base_atk.png", lambda: self.build_castle_structure('makerspace', 4)))
                    # 🟢 สร้างตึก Wallbuilder
                    grid_b.add_widget(BuildCard("Wallbuilder", "70% Block Attack\nCost: 9 Wood", 9, "assets/icon_effect/buff_def.png", lambda: self.build_castle_structure('wallbuilder', 9)))
                    
                    self.content_grid.add_widget(grid_b)

    def on_upgrade_addon(self, key, cost):
        self.panel.upgrade_addon(key, cost)
        self.refresh_ui()

    def build_castle_structure(self, structure_name, wood_cost):
        if getattr(self.app, 'wood_points', {}).get(self.node.faction, 0) < wood_cost:
            return
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        
        self.app.wood_points[self.node.faction] -= wood_cost
        self.node.building_state = f'building_{structure_name}'
        
        # รีเฟรชจอใหญ่เผื่ออัปเดตเลขไม้
        if hasattr(self.panel.map_screen, 'update_resource_display'):
            self.panel.map_screen.update_resource_display()
        self.refresh_ui()

    def destroy_castle_structure(self, instance):
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        self.node.building_state = 'destroying'
        self.refresh_ui()

    def trade_market(self, res_type, is_buying, rate):
        fac = self.node.faction
        res_dict = {
            'wood': self.app.wood_points, 'coal': self.app.coal_points,
            'silver': self.app.silver_points, 'iron': self.app.iron_points, 'gold': self.app.gold_points,
            'weapon_t1': self.app.weapon_t1_points, # เพิ่มอาวุธเข้าไปในระบบ Trade
            'weapon_t2': self.app.weapon_t2_points,
            'weapon_t3': self.app.weapon_t3_points
        }
        
        if hasattr(self.app, 'play_click_sound'): self.app.play_click_sound()
        
        # rate เป็น int อยู่แล้ว เอามาใช้ได้เลย
        tax_val = int(rate) 
        
        if is_buying: 
            if self.app.tax_points.get(fac, 0) >= tax_val:
                self.app.tax_points[fac] -= tax_val
                res_dict[res_type][fac] += 1
        else: 
            if res_dict[res_type].get(fac, 0) >= 1:
                res_dict[res_type][fac] -= 1
                self.app.tax_points[fac] += tax_val
                
        if hasattr(self.panel.map_screen, 'update_resource_display'):
            self.panel.map_screen.update_resource_display()
        self.refresh_ui()

    def craft_item(self, recipe_name):
        fac = self.node.faction
        app = self.app
        if hasattr(app, 'play_click_sound'): app.play_click_sound()

        # เก็บสถานะการคราฟต์เพื่อเช็คว่าสำเร็จไหม
        success = False

        if recipe_name == 'coal_to_iron':
            if app.coal_points.get(fac, 0) >= 2 and app.tax_points.get(fac, 0) >= 2:
                app.coal_points[fac] -= 2; app.tax_points[fac] -= 2
                app.iron_points[fac] += 1
                success = True
        elif recipe_name == 'silver_to_iron':
            if app.silver_points.get(fac, 0) >= 1 and app.tax_points.get(fac, 0) >= 2:
                app.silver_points[fac] -= 1; app.tax_points[fac] -= 2
                app.iron_points[fac] += 1
                success = True
        elif recipe_name == 'gold_to_iron':
            if app.gold_points.get(fac, 0) >= 1 and app.tax_points.get(fac, 0) >= 2:
                app.gold_points[fac] -= 1; app.tax_points[fac] -= 2
                app.iron_points[fac] += 3
                success = True
        elif recipe_name == 'weapon_t1':
            if app.wood_points.get(fac, 0) >= 2 and app.iron_points.get(fac, 0) >= 3:
                app.wood_points[fac] -= 2; app.iron_points[fac] -= 3
                app.weapon_t1_points[fac] += 1
                success = True
        elif recipe_name == 'weapon_t2':
            if app.wood_points.get(fac, 0) >= 4 and app.iron_points.get(fac, 0) >= 3:
                app.wood_points[fac] -= 4; app.iron_points[fac] -= 3
                app.weapon_t2_points[fac] += 1
                success = True
        elif recipe_name == 'weapon_t3':
            if app.wood_points.get(fac, 0) >= 6 and app.iron_points.get(fac, 0) >= 4:
                app.wood_points[fac] -= 6; app.iron_points[fac] -= 4
                app.weapon_t3_points[fac] += 1
                success = True

        if success:
            if hasattr(self.panel.map_screen, 'update_resource_display'):
                self.panel.map_screen.update_resource_display()
            self.refresh_ui()

# ----------------- Army Status (เปลี่ยน Text เป็น BoxLayout Icons) -----------------
class ArmyStatusPopup(ModalView):
    def __init__(self, army_pieces, **kwargs):
        super().__init__(size_hint=(0.9, 0.9), background_color=(0, 0, 0, 0.8), auto_dismiss=True, **kwargs)
        self.root_box = BoxLayout(orientation='vertical', padding=[dp(20), dp(10), dp(20), dp(10)], spacing=dp(8))
        with self.root_box.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.2, 0.8, 1, 1)
            self.border_line = Line(rounded_rectangle=(self.root_box.x, self.root_box.y, self.root_box.width, self.root_box.height, dp(15)), width=2)
        self.root_box.bind(pos=self._update_bg, size=self._update_bg)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(5))
        header.add_widget(Label(size_hint_x=None, width=dp(80), text=''))
        title_lbl = Label(text="[b]ARMY STATUS[/b]", markup=True, font_size='20sp', halign='center', valign='middle', color=(0.2, 0.8, 1, 1))
        header.add_widget(title_lbl)
        close_btn = Button(text="CLOSE", size_hint_x=None, width=dp(80), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        self.root_box.add_widget(header)

        scroll = ScrollView(do_scroll_y=True, do_scroll_x=False)
        grid = GridLayout(cols=3, spacing=dp(12), padding=[dp(5), dp(5), dp(5), dp(5)], size_hint_x=1, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for p in army_pieces:
            box = BoxLayout(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(250), padding=dp(8), spacing=dp(4))
            with box.canvas.before:
                Color(0.15, 0.15, 0.18, 1)
                box_bg = RoundedRectangle(radius=[dp(8)])
            def update_box_bg(instance, value, bg=box_bg):
                bg.pos = instance.pos
                bg.size = instance.size
            box.bind(pos=update_box_bg, size=update_box_bg)
            
            p_cls_name = p.__class__.__name__.lower()
            tribe = getattr(p, 'tribe', 'the knight company')
            color = p.color
            lvl = getattr(p, 'upgrade_level', 0)
            path = getattr(p, 'upgrade_path', 'standard')
            
            stage_folder = "1base"
            if lvl > 0:
                if path == 'standard': stage_folder = "2upATK" if lvl == 1 else "3upDEF"
                elif path == 'special': stage_folder = "4up_rehidden" if lvl == 1 else "5up_reroll_ATK_DEF"
                
            if p_cls_name in ['pawn', 'hastati', 'levies']:
                num = getattr(p, 'variant', 1)
                filename = f"{p_cls_name}{num}.png"
            else: filename = f"{p_cls_name}.png"
            if getattr(p, 'name', '') == 'Prince': filename = 'prince.png'
            
            img = Image(source=safe_piece_path(p, tribe, color), size_hint=(1, 0.55), allow_stretch=True, keep_ratio=True)
            box.add_widget(img)
            
            p_name = getattr(p, 'name', p.__class__.__name__.capitalize())
            lvl_str = f" [color=ffff00]+{lvl}[/color]" if lvl > 0 else ""
            card_title = Label(text=f"[b]{p_name}{lvl_str}[/b]", markup=True, font_size='14sp', size_hint_y=0.15, halign='center', valign='middle')
            box.add_widget(card_title)
            
            # 1. เปลี่ยนตัวหนังสือเป็น BoxLayout ATK/DEF/COIN ไอคอน
            stats_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=dp(2))
            
            coin_img = Image(source='assets/icon_effect/base_coin.png', size_hint_x=None, width=dp(16))
            stats_box.add_widget(coin_img)
            stats_box.add_widget(Label(text=f"{p.coins}", font_size='12sp', color=(1, 1, 0, 1), halign='left'))
            
            atk_img = Image(source='assets/icon_effect/base_atk.png', size_hint_x=None, width=dp(16))
            stats_box.add_widget(atk_img)
            stats_box.add_widget(Label(text=f"{p.base_atk}", font_size='12sp', color=(1, 0.2, 0.2, 1), halign='left'))
            
            def_img = Image(source='assets/icon_effect/base_def.png', size_hint_x=None, width=dp(16))
            stats_box.add_widget(def_img)
            stats_box.add_widget(Label(text=f"{p.base_def}", font_size='12sp', color=(0.2, 0.6, 1, 1), halign='left'))
            box.add_widget(stats_box)

            # 2. เพิ่ม Dynamic Stats (บัฟพิเศษเฉพาะตัว)
            dynamic_box = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=dp(4))
            if p_cls_name == 'menatarm' and hasattr(p, 'charge_stacks'):
                dynamic_box.add_widget(Image(source='assets/icon_effect/charge.png', size_hint_x=None, width=dp(14)))
                dynamic_box.add_widget(Label(text=f"{p.charge_stacks}/3", font_size='11sp', color=(0, 1, 1, 1)))
            elif p_cls_name == 'hastati' and hasattr(p, 'def_stacks'):
                dynamic_box.add_widget(Image(source='assets/icon_effect/buff_def.png', size_hint_x=None, width=dp(14)))
                dynamic_box.add_widget(Label(text=f"{p.def_stacks}/5", font_size='11sp', color=(0, 1, 0, 1)))
            elif p_cls_name == 'praetorian' and hasattr(p, 'active_buffs'):
                dynamic_box.add_widget(Image(source='assets/icon_effect/buff_atk_def.png', size_hint_x=None, width=dp(14)))
                dynamic_box.add_widget(Label(text=f"{len(p.active_buffs)}/5", font_size='11sp', color=(1, 0.6, 0, 1)))
            elif p_cls_name == 'royalguard' and hasattr(p, 'rg_atk_buffs'):
                dynamic_box.add_widget(Image(source='assets/icon_effect/buff_atk.png', size_hint_x=None, width=dp(14)))
                dynamic_box.add_widget(Label(text=f"{p.rg_atk_buffs}", font_size='11sp', color=(1, 0.2, 0.2, 1)))
                dynamic_box.add_widget(Image(source='assets/icon_effect/buff_def.png', size_hint_x=None, width=dp(14)))
                dynamic_box.add_widget(Label(text=f"{p.rg_def_buffs}", font_size='11sp', color=(0.2, 0.6, 1, 1)))
            if len(dynamic_box.children) > 0: box.add_widget(dynamic_box)
            
            # Passives
            hp1 = getattr(p, 'hidden_passive', None)
            desc1 = hp1.description if hp1 and getattr(hp1, 'passive_type', None) else "None"
            passives_text = f"[color=00ffcc]P1:[/color] {desc1}"
            hp2 = getattr(p, 'second_hidden_passive', None)
            if hp2 and getattr(hp2, 'passive_type', None):
                passives_text += f"\n[color=ff00cc]P2:[/color] {hp2.description}"
                
            box.add_widget(Label(text=passives_text, markup=True, font_size='11sp', size_hint_y=0.2, halign='center', valign='middle'))
            grid.add_widget(box)
            
        scroll.add_widget(grid)
        self.root_box.add_widget(scroll)
        self.add_widget(self.root_box)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(15))

# ----------------- Upgrade Tree UI (เปลี่ยน Text เป็น BoxLayout Icons) -----------------
class TechCard(ButtonBehavior, BoxLayout):
    def __init__(self, title, desc, atk, def_pt, coins, img_path, is_unlocked, is_available, on_click_cb, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint=(None, None), size=(dp(160), dp(200)), **kwargs)
        self.is_unlocked = is_unlocked
        self.is_available = is_available
        self.on_click_cb = on_click_cb
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 0.9)
            self.bg = RoundedRectangle(radius=[dp(8)])
            if is_unlocked: Color(0.9, 0.8, 0.2, 1); width = 2.5
            elif is_available: Color(0.4, 0.8, 0.4, 1); width = 2
            else: Color(0.3, 0.3, 0.35, 1); width = 1.5
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=width)
            
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='15sp', size_hint_y=0.15))
        
        img = Image(source=img_path, allow_stretch=True, keep_ratio=True, size_hint_y=0.55)
        if not is_unlocked and not is_available: img.opacity = 0.4
        self.add_widget(img)
        
        # แทนที่ Label(ATK/DEF/Coin) ด้วย BoxLayout + Icon
        stats_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=dp(2))
        atk_img = Image(source='assets/icon_effect/base_atk.png', size_hint_x=None, width=dp(14))
        stats_box.add_widget(atk_img)
        stats_box.add_widget(Label(text=f"{atk}", font_size='11sp', color=(1, 0.2, 0.2, 1)))
        
        def_img = Image(source='assets/icon_effect/base_def.png', size_hint_x=None, width=dp(14))
        stats_box.add_widget(def_img)
        stats_box.add_widget(Label(text=f"{def_pt}", font_size='11sp', color=(0.2, 0.6, 1, 1)))
        
        coin_img = Image(source='assets/icon_effect/base_coin.png', size_hint_x=None, width=dp(14))
        stats_box.add_widget(coin_img)
        stats_box.add_widget(Label(text=f"{coins}", font_size='11sp', color=(1, 1, 0, 1)))
        
        if not is_unlocked and not is_available: stats_box.opacity = 0.4
        self.add_widget(stats_box)
        
        self.add_widget(Label(text=f"[color=00ffcc]{desc}[/color]", markup=True, font_size='11sp', size_hint_y=0.15, halign='center'))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        if self.is_available and self.on_click_cb: self.on_click_cb()

class UpgradeTreePopup(ModalView):
    def __init__(self, piece_obj, update_callback, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), background_color=(0, 0, 0, 0.8), auto_dismiss=False, **kwargs)
        self.piece = piece_obj
        self.update_callback = update_callback
        
        p_name = self.piece.__class__.__name__.lower()
        self.upgrade_cost = {'praetorian': 7, 'royalguard': 7, 'menatarm': 5, 'knight': 4, 'bishop': 4, 'rook': 4, 'hastati': 3, 'levies': 2, 'pawn': 2}.get(p_name, 5)
        
        self.root_layout = FloatLayout()
        with self.root_layout.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.83, 0.68, 0.21, 1)
            self.border_line = Line(rounded_rectangle=(self.root_layout.x, self.root_layout.y, self.root_layout.width, self.root_layout.height, dp(15)), width=2)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)
        
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'top': 1}, padding=[dp(15), dp(5)])
        p_name_display = getattr(self.piece, 'name', self.piece.__class__.__name__.capitalize())
        
        title_box = BoxLayout(orientation='horizontal', size_hint_x=0.8, spacing=dp(5))
        title_box.add_widget(Label(text=f"[b]UPGRADE PATH: {p_name_display} (Cost: {self.upgrade_cost}[/b]", markup=True, font_size='20sp', halign='right', color=(1, 0.8, 0.2, 1)))
        title_box.add_widget(Image(source='assets/icon_effect/tax.png', size_hint_x=None, width=dp(20)))
        title_box.add_widget(Label(text="[b])[/b]", markup=True, font_size='20sp', halign='left', size_hint_x=None, width=dp(20), color=(1, 0.8, 0.2, 1)))
        
        header.add_widget(title_box)
        
        close_btn = Button(text="CLOSE", size_hint_x=None, width=dp(80), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        self.root_layout.add_widget(header)
        
        self.tree_layout = FloatLayout(size_hint=(1, 0.9), pos_hint={'y': 0})
        self.root_layout.add_widget(self.tree_layout)
        
        self.bind(size=self.draw_tree) 
        Clock.schedule_once(lambda dt: self.draw_tree(), 0.1)
        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(15))

    def draw_tree(self, *args):
        self.tree_layout.clear_widgets()
        self.tree_layout.canvas.before.clear()
        
        p = self.piece
        c_name = p.__class__.__name__.lower()
        tribe = getattr(p, 'tribe', 'the knight company')
        color = p.color
        lvl = getattr(p, 'upgrade_level', 0)
        path = getattr(p, 'upgrade_path', 'standard')
        
        if c_name in ['pawn', 'hastati', 'levies']: filename = f"{c_name}{getattr(p, 'variant', 1)}.png"
        else: filename = f"{c_name}.png"
        if getattr(p, 'name', '') == 'Prince': filename = 'prince.png'
            
        def _safe(folder):
            """Return the path for this folder, falling back to 1base if the file is absent."""
            p_path = f"assets/pieces/{tribe}/{color}/{folder}/{filename}"
            return p_path if os.path.isfile(p_path) else base_img

        base_img  = f"assets/pieces/{tribe}/{color}/1base/{filename}"
        atk1_img  = _safe('2upATK')
        def2_img  = _safe('3upDEF')

        has_special = c_name in ['praetorian', 'menatarm']
        spec1_img = _safe('4up_rehidden')      if has_special else None
        spec2_img = _safe('5up_reroll_ATK_DEF') if has_special else None

        def draw_line(p1, p2, is_active):
            with self.tree_layout.canvas.before:
                if is_active: Color(0.9, 0.8, 0.2, 1)
                else: Color(0.7, 0.7, 0.7, 1)
                Line(points=[p1[0], p1[1], p2[0], p2[1]], width=3 if is_active else 1.5)

        cx = self.width / 2 if self.width > 1 else dp(400)
        cy = self.height / 2 if self.height > 1 else dp(300)
        card_w, card_h = dp(160), dp(200)
        x_left, x_mid, x_right = cx - dp(240), cx, cx + dp(240)
        y_top, y_bot = cy + dp(120), cy - dp(120)

        b_atk = getattr(p, 'base_atk', p.base_points) if lvl == 0 else p.base_points
        b_def = getattr(p, 'base_def', p.base_points) if lvl == 0 else p.base_points
        
        node_base = TechCard("Base Form", "Default Stats", b_atk, b_def, p.coins, base_img, (lvl == 0), False, None)
        node_base.pos = (x_left - card_w/2, cy - card_h/2)
        self.tree_layout.add_widget(node_base)

        if not has_special:
            n1_atk = b_atk + 2
            node_u1 = TechCard("Rank I", "+2 Base ATK", n1_atk, b_def, p.coins, atk1_img, (lvl >= 1), (lvl == 0), lambda: self.do_upgrade("standard"))
            node_u1.pos = (x_mid - card_w/2, cy - card_h/2)
            self.tree_layout.add_widget(node_u1)
            
            node_u2 = TechCard("Rank II", "+2 Base DEF", n1_atk, b_def + 2, p.coins, def2_img, (lvl == 2), (lvl == 1), lambda: self.do_upgrade("standard"))
            node_u2.pos = (x_right - card_w/2, cy - card_h/2)
            self.tree_layout.add_widget(node_u2)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.right, node_base.center_y), (node_u1.x, node_u1.center_y), (lvl >= 1)), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1.right, node_u1.center_y), (node_u2.x, node_u2.center_y), (lvl == 2)), 0.1)
        else:
            n1_std_unlocked = (lvl >= 1 and path == "standard")
            node_u1_std = TechCard("Rank I (Combat)", "+2 Base ATK", b_atk+2, b_def, p.coins, atk1_img, n1_std_unlocked, (lvl == 0), lambda: self.do_upgrade("standard"))
            node_u1_std.pos = (x_mid - card_w/2, y_top - card_h/2)
            self.tree_layout.add_widget(node_u1_std)
            
            n2_std_unlocked = (lvl == 2 and path == "standard")
            node_u2_std = TechCard("Rank II (Combat)", "+2 Base DEF", b_atk+2, b_def+2, p.coins, def2_img, n2_std_unlocked, (lvl == 1 and path == "standard"), lambda: self.do_upgrade("standard"))
            node_u2_std.pos = (x_right - card_w/2, y_top - card_h/2)
            self.tree_layout.add_widget(node_u2_std)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.right, node_base.center_y), (node_u1_std.x, node_u1_std.center_y), n1_std_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_std.right, node_u1_std.center_y), (node_u2_std.x, node_u2_std.center_y), n2_std_unlocked), 0.1)

            n1_spc_unlocked = (lvl >= 1 and path == "special")
            desc1 = "Reroll Hidden Passive" if not n1_spc_unlocked else getattr(p.hidden_passive, 'description', 'Passive Re-rolled')
            
            node_u1_spc = TechCard("Rank I (Utility)", desc1, (p.base_atk if n1_spc_unlocked else b_atk), (p.base_def if n1_spc_unlocked else b_def), p.coins, spec1_img, n1_spc_unlocked, (lvl == 0), lambda: self.do_upgrade("special"))
            node_u1_spc.pos = (x_mid - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u1_spc)
            
            n2_spc_unlocked = (lvl == 2 and path == "special")
            desc2 = "Gain 2nd Hidden Passive" if not n2_spc_unlocked else getattr(p.second_hidden_passive, 'description', '2nd Passive Active')
            
            node_u2_spc = TechCard("Rank II (Utility)", desc2, p.base_atk, p.base_def, p.coins, spec2_img, n2_spc_unlocked, (lvl == 1 and path == "special"), lambda: self.do_upgrade("special"))
            node_u2_spc.pos = (x_right - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2_spc)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.right, node_base.center_y), (node_u1_spc.x, node_u1_spc.center_y), n1_spc_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_spc.right, node_u1_spc.center_y), (node_u2_spc.x, node_u2_spc.center_y), n2_spc_unlocked), 0.1)

    def do_upgrade(self, path):
        app = App.get_running_app()
        app.play_click_sound()
        faction = app.current_map_turn
        if app.tax_points.get(faction, 0) < self.upgrade_cost: return
        app.tax_points[faction] -= self.upgrade_cost
        if hasattr(self.piece, 'upgrade_piece'): self.piece.upgrade_piece(path)
        self.draw_tree()
        if self.update_callback: self.update_callback()