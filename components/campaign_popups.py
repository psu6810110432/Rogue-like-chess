# components/campaign_popups.py
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

            row_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=None, height=dp(140))
            row_box.add_widget(Widget())  
            for idx, p_data in enumerate(items):
                if p_data is None:
                    card = RecruitCard(None, 0, self.node.faction, self.app, None)
                else:
                    p_name = p_data['name']
                    base_cost = p_data['cost']
                    final_cost = self.panel.get_discounted_price(base_cost, addons)
                    cb = lambda n, c, r=row_key, i=idx: self.on_buy_piece(n, c, r, i)
                    card = RecruitCard(p_name, final_cost, self.node.faction, self.app, cb)
                row_box.add_widget(card)
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
        
        self.root_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with self.root_box.canvas.before:
            Color(0.15, 0.1, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.5, 0.2, 1)
            self.border_line = Line(rounded_rectangle=[self.root_box.x, self.root_box.y, self.root_box.width, self.root_box.height, dp(12)], width=2)
        self.root_box.bind(pos=self._update_bg, size=self._update_bg)
        
        self.header = BoxLayout(size_hint_y=None, height=dp(40))
        self.title = Label(text="[b]CONSTRUCTION[/b]", markup=True, font_size='22sp', halign='left', color=(0.8, 0.5, 0.2, 1), size_hint_x=0.4)
        
        # แท่นที่ Label เดิมด้วย BoxLayout สำหรับค่า Tax
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
        self.content_grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
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
        
        # อัปเดต Status Box
        self.status_box.clear_widgets()
        tax_img = Image(source='assets/icon_effect/tax.png', size_hint_x=None, width=dp(24))
        self.status_box.add_widget(tax_img)
        self.status_box.add_widget(Label(text=f"{tax}", font_size='16sp', color=(0, 1, 0, 1), halign='left'))
        
        farm_lvl = addons.get('farm', 1)
        farm_cost = farm_lvl * 5
        if farm_lvl < 3:
            img = get_addon_img('farm', farm_lvl)
            self.content_grid.add_widget(BuildCard("Farm", f"Lvl {farm_lvl} -> {farm_lvl+1}\n(+2 Tax)", farm_cost, img, lambda: self.on_upgrade_addon('farm', farm_cost)))
            
        tav_lvl = addons.get('tavern', 1)
        tav_cost = tav_lvl * 6
        if tav_lvl < 3:
            img = get_addon_img('tavern', tav_lvl)
            self.content_grid.add_widget(BuildCard("Tavern", f"Lvl {tav_lvl} -> {tav_lvl+1}\n(Unlocks Units)", tav_cost, img, lambda: self.on_upgrade_addon('tavern', tav_cost)))
            
        spec = addons.get('special')
        spec_lvl = addons.get('special_lvl', 0)
        if spec and spec not in ['mine']: 
            spec_cost = spec_lvl * 8
            if spec_lvl < 3:
                img = get_addon_img(spec, spec_lvl)
                self.content_grid.add_widget(BuildCard(spec.capitalize(), f"Lvl {spec_lvl} -> {spec_lvl+1}", spec_cost, img, lambda: self.on_upgrade_addon('special_lvl', spec_cost)))
                
    def on_upgrade_addon(self, key, cost):
        self.panel.upgrade_addon(key, cost)
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
            
            img = Image(source=f"assets/pieces/{tribe}/{color}/{stage_folder}/{filename}", size_hint=(1, 0.55), allow_stretch=True, keep_ratio=True)
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
            
        base_img = f"assets/pieces/{tribe}/{color}/1base/{filename}"
        atk1_img = f"assets/pieces/{tribe}/{color}/2upATK/{filename}"
        def2_img = f"assets/pieces/{tribe}/{color}/3upDEF/{filename}"
        
        has_special = c_name in ['praetorian', 'menatarm']
        spec1_img = f"assets/pieces/{tribe}/{color}/4up_rehidden/{filename}" if has_special else None
        spec2_img = f"assets/pieces/{tribe}/{color}/5up_reroll_ATK_DEF/{filename}" if has_special else None

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