# components/campaign_panel.py
import math
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation

from components.campaign_cards import PieceCard, RecruitCard
from components.campaign_popups import ArmyStatusPopup
from logic.campaign_helpers import generate_piece

def get_addon_img(addon, lvl):
    folder = "base1" if lvl <= 1 else ("up1" if lvl == 2 else "up2")
    return f"assets/structure/addon/{folder}/{addon}.png"

class BuildCard(ButtonBehavior, FloatLayout):
    def __init__(self, title, desc, cost, img_path, on_click_cb, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(160), dp(100)), **kwargs)
        self.bind(on_release=lambda x: on_click_cb())
        
        with self.canvas.before:
            Color(0.15, 0.25, 0.15, 1)
            self.bg = RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # แสดงรูปสิ่งก่อสร้างทางซ้าย และข้อความอยู่ทางขวา
        self.add_widget(Image(source=img_path, size_hint=(0.35, 0.8), pos_hint={'x': 0.05, 'center_y': 0.5}, allow_stretch=True, keep_ratio=True))
        
        lbl_box = BoxLayout(orientation='vertical', size_hint=(0.55, 0.9), pos_hint={'right': 0.95, 'center_y': 0.5})
        lbl_box.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='14sp', halign='center'))
        lbl_box.add_widget(Label(text=f"[size=11sp]{desc}[/size]", markup=True, halign='center'))
        lbl_box.add_widget(Label(text=f"[color=ffff00]Cost: {cost} Tax[/color]", markup=True, font_size='12sp', halign='center'))
        self.add_widget(lbl_box)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size


class CampaignArmyPanel(FloatLayout):
    def __init__(self, map_screen, app, **kwargs):
        super().__init__(size_hint=(0.85, None), height=dp(230), pos_hint={'x': 0.02, 'y': -0.5}, **kwargs) 
        self.map_screen = map_screen
        self.app = app
        self.current_node = None
        self.current_tab = 'army'
        self.is_upgrade_mode = False 
        self.active_sub_village = None 

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.bg = RoundedRectangle(radius=[dp(12)])
            self.border_color = Color(0.5, 0.5, 0.5, 1)
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=2)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.header_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), pos_hint={'top': 1, 'x': 0}, padding=[dp(10), dp(5)])
        
        self.header_lbl = Label(text="ARMY HQ", bold=True, font_size='18sp', size_hint_x=0.3, halign='left')
        self.status_lbl = Label(text="", markup=True, size_hint_x=0.2, font_size='14sp')
        
        self.btn_tab_army = Button(text="[b]ARMY[/b]", markup=True, size_hint_x=0.12, background_color=(0.3, 0.5, 0.8, 1))
        self.btn_tab_army.bind(on_release=lambda x: self.switch_tab('army'))
        self.btn_tab_recruit = Button(text="[b]RECRUIT[/b]", markup=True, size_hint_x=0.12, background_color=(0.2, 0.2, 0.2, 1))
        self.btn_tab_recruit.bind(on_release=lambda x: self.switch_tab('recruit'))
        self.btn_tab_build = Button(text="[b]BUILD[/b]", markup=True, size_hint_x=0.12, background_color=(0.2, 0.2, 0.2, 1))
        self.btn_tab_build.bind(on_release=lambda x: self.switch_tab('build'))
        
        btn_close = Button(text="CLOSE", size_hint_x=0.1, background_color=(0.5, 0.2, 0.2, 1))
        btn_close.bind(on_release=self.close_panel)
        
        self.header_box.add_widget(self.header_lbl)
        self.header_box.add_widget(self.status_lbl)
        self.header_box.add_widget(self.btn_tab_army)
        self.header_box.add_widget(self.btn_tab_recruit)
        self.header_box.add_widget(self.btn_tab_build)
        self.header_box.add_widget(btn_close)
        self.add_widget(self.header_box)

        self.sub_village_nav = BoxLayout(orientation='horizontal', size_hint=(0.7, 0.1), pos_hint={'x': 0.02, 'y': 0.75}, spacing=dp(5))
        self.add_widget(self.sub_village_nav)

        self.content_scroll = ScrollView(size_hint=(0.7, 0.65), pos_hint={'x': 0.02, 'y': 0.05}, do_scroll_x=True, do_scroll_y=False)
        self.content_grid = GridLayout(rows=1, spacing=dp(8), size_hint_x=None, padding=dp(5))
        self.content_grid.bind(minimum_width=self.content_grid.setter('width'))
        self.content_scroll.add_widget(self.content_grid)
        self.add_widget(self.content_scroll)

        self.action_box = BoxLayout(orientation='vertical', size_hint=(0.25, 0.7), pos_hint={'right': 0.98, 'y': 0.05}, spacing=dp(5))
        self.btn_action = Button(text="[b]MARCH / ATTACK[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1), size_hint_y=0.6)
        self.btn_action.bind(on_release=self.execute_action)
        self.action_box.add_widget(self.btn_action)
        
        self.sub_action_box = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=0.4)
        self.btn_status = Button(text="[b]STATUS[/b]", markup=True, background_color=(0.2, 0.6, 0.8, 1))
        self.btn_status.bind(on_release=self.show_army_status)
        self.sub_action_box.add_widget(self.btn_status)
        
        self.btn_upgrade = Button(text="[b]UPGRADE[/b]", markup=True, background_color=(0.6, 0.2, 0.8, 1))
        self.btn_upgrade.bind(on_release=self.toggle_upgrade_mode)
        self.sub_action_box.add_widget(self.btn_upgrade)
        
        self.action_box.add_widget(self.sub_action_box)
        self.add_widget(self.action_box)
        self.piece_cards = []

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(12))

    def open_for_node(self, node):
        from kivy.animation import Animation
        self.current_node = node
        self.active_sub_village = None 
        self.header_lbl.text = f"{node.faction.upper()} {node.node_type.upper()}"
        self.is_upgrade_mode = False
        
        for n in self.map_screen.nodes_list:
            n.is_selected_node = (n == node)
            n.update_graphics()
        
        if node.faction == 'white': self.border_color.rgba = (0.9, 0.9, 0.9, 1)
        elif node.faction == 'black': self.border_color.rgba = (0.3, 0.3, 0.4, 1)
        
        self.switch_tab('army')
        Animation(pos_hint={'y': 0.02}, duration=0.3, t='out_quad').start(self)

    def update_sub_village_nav(self):
        self.sub_village_nav.clear_widgets()
        if self.current_tab == 'army' or self.current_node.node_type != 'castle': return
        
        btn_main = Button(text="Castle", font_size='12sp', background_color=(0.5, 0.5, 0.2, 1) if self.active_sub_village is None else (0.2, 0.2, 0.2, 1))
        btn_main.bind(on_release=lambda x: self.select_sub_village(None))
        self.sub_village_nav.add_widget(btn_main)
        
        for sv in self.current_node.sub_villages:
            btn_v = Button(text=f"Village {sv['id']}", font_size='12sp', background_color=(0.5, 0.5, 0.2, 1) if self.active_sub_village == sv else (0.2, 0.2, 0.2, 1))
            btn_v.bind(on_release=lambda x, v=sv: self.select_sub_village(v))
            self.sub_village_nav.add_widget(btn_v)

    def select_sub_village(self, sv):
        self.app.play_click_sound()
        self.active_sub_village = sv
        self.switch_tab(self.current_tab) 

    def get_active_addons(self):
        if self.active_sub_village: return self.active_sub_village['addons']
        return getattr(self.current_node, 'addons', {'farm': 1, 'tavern': 1, 'special': None, 'special_lvl': 0})

    def close_panel(self, *args):
        from kivy.animation import Animation
        self.app.play_click_sound()
        for n in self.map_screen.nodes_list:
            n.is_selected_node = False
            n.update_graphics()
        Animation(pos_hint={'y': -0.5}, duration=0.2).start(self)

    def toggle_upgrade_mode(self, instance):
        self.app.play_click_sound()
        self.is_upgrade_mode = not self.is_upgrade_mode
        if self.is_upgrade_mode:
            self.btn_upgrade.background_color = (0.8, 0.8, 0.2, 1)
            self.map_screen.status_lbl.text = f"[color=ffff00]UPGRADE MODE: Tax {self.app.tax_points.get(self.current_node.faction, 0)} | Select a unit to open Tech Tree.[/color]"
            for card in self.piece_cards:
                card.is_selected = False
                card.border_color.rgba = (0.3, 0.3, 0.35, 1)
                card.border_line.width = 1.5
        else:
            self.switch_tab('army')

    def show_army_status(self, instance):
        self.app.play_click_sound()
        if not self.current_node or not self.current_node.army_pieces: return
        pop = ArmyStatusPopup(self.current_node.army_pieces)
        pop.open()

    def get_discounted_price(self, base_cost, addons):
        if addons.get('special') == 'statue':
            lvl = addons.get('special_lvl', 1)
            if lvl == 1: return max(math.ceil(base_cost/2), base_cost - 1)
            elif lvl == 2: return max(math.ceil(base_cost/2), base_cost - 2)
            elif lvl >= 3: return math.ceil(base_cost / 2)
        return base_cost

    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        self.is_upgrade_mode = False
        self.content_grid.clear_widgets()
        self.piece_cards.clear()
        self.update_sub_village_nav()

        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False))
        max_cap = 16 if headers > 0 else 8
        total = len(self.current_node.army_pieces)

        if tab_name == 'army':
            self.btn_tab_army.background_color = (0.3, 0.5, 0.8, 1)
            self.btn_tab_recruit.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_build.background_color = (0.2, 0.2, 0.2, 1)
            
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            self.status_lbl.text = f"Cap: [b]{total}/{max_cap}[/b] | Fatigue: [color=00ff00]{fatigue}/6[/color]"
            
            self.btn_action.text = "[b]MARCH / ATTACK[/b]"
            self.btn_action.background_color = (0.8, 0.2, 0.2, 1)
            self.btn_action.disabled = False
            self.sub_action_box.opacity = 1
            self.btn_status.disabled = False 
            self.btn_upgrade.disabled = False
            
            for p in self.current_node.army_pieces:
                card = PieceCard(p, map_screen_ref=self.map_screen) 
                self.piece_cards.append(card)
                self.content_grid.add_widget(card)

        elif tab_name == 'recruit':
            self.btn_tab_army.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_recruit.background_color = (0.3, 0.8, 0.3, 1)
            self.btn_tab_build.background_color = (0.2, 0.2, 0.2, 1)
            
            tax = self.app.tax_points.get(self.current_node.faction, 0)
            addons = self.get_active_addons()
            tav_lvl = addons.get('tavern', 1)
            is_castle = (self.current_node.node_type == 'castle' and self.active_sub_village is None)
            
            self.status_lbl.text = f"Tax: [color=00ff00]{tax}[/color] | Tavern Lvl: {tav_lvl}"
            
            self.btn_action.text = "[b]SELECT UNIT TO RECRUIT[/b]"
            self.btn_action.background_color = (0.3, 0.3, 0.3, 1)
            self.btn_action.disabled = True
            self.sub_action_box.opacity = 0
            self.btn_status.disabled = True 
            self.btn_upgrade.disabled = True
            
            pool = []
            if tav_lvl >= 1: pool.extend([('pawn', 2), ('levies', 2), ('knight', 4), ('bishop', 4), ('rook', 4)])
            if tav_lvl >= 3 or (is_castle and tav_lvl >= 2): pool.extend([('hastati', 3), ('menatarm', 5)])
            if is_castle and tav_lvl >= 4: pool.extend([('praetorian', 7), ('royalguard', 7)])
            
            unlock_costs = {'praetorian': 14, 'royalguard': 14, 'hastati': 6}
            
            for p_name, base_cost in pool:
                final_cost = self.get_discounted_price(base_cost, addons)
                is_locked = p_name not in self.app.unlocked_units.get(self.current_node.faction, set())
                ucost = unlock_costs.get(p_name, 0)
                card = RecruitCard(p_name, final_cost, self.current_node.faction, self.app, self.buy_piece, is_locked=is_locked, unlock_cost=ucost)
                self.content_grid.add_widget(card)
                
        elif tab_name == 'build':
            self.btn_tab_army.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_recruit.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_build.background_color = (0.8, 0.5, 0.2, 1)
            
            tax = self.app.tax_points.get(self.current_node.faction, 0)
            addons = self.get_active_addons()
            
            self.status_lbl.text = f"Tax: [color=00ff00]{tax}[/color] | Upgrading Buildings"
            self.btn_action.disabled = True
            self.btn_action.opacity = 0
            self.sub_action_box.opacity = 0
            
            farm_lvl = addons.get('farm', 1)
            farm_cost = farm_lvl * 5
            if farm_lvl < 3:
                img = get_addon_img('farm', farm_lvl)
                self.content_grid.add_widget(BuildCard("Farm", f"Lvl {farm_lvl} -> {farm_lvl+1}\n(+2 Tax)", farm_cost, img, lambda: self.upgrade_addon('farm', farm_cost)))
                
            tav_lvl = addons.get('tavern', 1)
            tav_max = 5 if (self.current_node.node_type == 'castle' and self.active_sub_village is None) else 3
            tav_cost = tav_lvl * 6
            if tav_lvl < tav_max:
                img = get_addon_img('tavern', tav_lvl)
                self.content_grid.add_widget(BuildCard("Tavern", f"Lvl {tav_lvl} -> {tav_lvl+1}\n(Unlocks Units)", tav_cost, img, lambda: self.upgrade_addon('tavern', tav_cost)))
                
            spec = addons.get('special')
            spec_lvl = addons.get('special_lvl', 0)
            if spec and spec not in ['mine']: 
                max_slvl = 3 if spec in ['guard', 'statue'] else 2
                spec_cost = spec_lvl * 8
                if spec_lvl < max_slvl:
                    img = get_addon_img(spec, spec_lvl)
                    self.content_grid.add_widget(BuildCard(spec.capitalize(), f"Lvl {spec_lvl} -> {spec_lvl+1}", spec_cost, img, lambda: self.upgrade_addon('special_lvl', spec_cost)))

    def upgrade_addon(self, key, cost):
        self.app.play_click_sound()
        faction = self.current_node.faction
        if self.app.tax_points.get(faction, 0) < cost: return
        self.app.tax_points[faction] -= cost
        addons = self.get_active_addons()
        addons[key] += 1
        self.switch_tab('build')
        # ✨ เพิ่มบรรทัดนี้เพื่ออัปเดตภาพโหนดบนแผนที่ทันทีที่อัปเกรดสำเร็จ
        self.current_node.update_graphics()

    def buy_piece(self, piece_name, cost, is_locked, unlock_cost):
        self.app.play_click_sound()
        faction = self.current_node.faction
        
        if is_locked:
            if self.app.tax_points.get(faction, 0) >= unlock_cost:
                self.app.tax_points[faction] -= unlock_cost
                self.app.unlocked_units[faction].add(piece_name)
                self.switch_tab('recruit')
            return
            
        if self.app.tax_points[faction] < cost: return
        
        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False))
        max_cap = 16 if headers > 0 else 8
        if len(self.current_node.army_pieces) >= max_cap: return
        
        self.app.tax_points[faction] -= cost
        new_p = generate_piece(piece_name, faction, self.app)
        
        addons = self.get_active_addons()
        spec = addons.get('special')
        slvl = addons.get('special_lvl', 0)
        
        if spec == 'weaponsmith':
            new_p.base_atk += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'atk_buff'
            new_p.second_hidden_passive.description = f"Weaponsmith Forged (+{slvl} ATK)"
            
        elif spec == 'blacksmith':
            new_p.base_def += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'def_buff'
            new_p.second_hidden_passive.description = f"Blacksmith Forged (+{slvl} DEF)"
            
        self.current_node.army_pieces.append(new_p)
        self.switch_tab('recruit') 

    def execute_action(self, instance):
        if self.current_tab != 'army': return
        self.app.play_click_sound()
        fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
        if fatigue >= 6:
            self.map_screen.status_lbl.text = "[color=ff0000]ARMY IS EXHAUSTED (FATIGUE = 6)! MUST REST.[/color]"
            return
            
        selected_pieces = [card.piece_obj for card in self.piece_cards if card.is_selected]
        if len(selected_pieces) == 0: selected_pieces = self.current_node.army_pieces.copy() 
        if len(selected_pieces) == 0: return 
        
        for p in selected_pieces: self.current_node.army_pieces.remove(p)
            
        self.app.combat_marching_army = selected_pieces
        self.close_panel()
        self.map_screen.start_marching(self.current_node)