# components/campaign_popups.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView

class ArmyStatusPopup(ModalView):
    def __init__(self, army_pieces, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), background_color=(0, 0, 0, 0.8), auto_dismiss=True, **kwargs)
        self.root_layout = FloatLayout()
        with self.root_layout.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(15)])
            Color(0.2, 0.8, 1, 1)
            self.border_line = Line(rounded_rectangle=(self.root_layout.x, self.root_layout.y, self.root_layout.width, self.root_layout.height, dp(15)), width=2)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'top': 1}, padding=[dp(15), dp(5)])
        header.add_widget(Label(text="[b]ARMY STATUS[/b]", markup=True, font_size='20sp', halign='left', color=(0.2, 0.8, 1, 1)))
        
        close_btn = Button(text="CLOSE", size_hint_x=None, width=dp(80), background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        self.root_layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 0.9), pos_hint={'y': 0})
        grid = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for p in army_pieces:
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10))
            with box.canvas.before:
                Color(0.15, 0.15, 0.18, 1)
                box_bg = RoundedRectangle(radius=[dp(8)])
            
            def update_box_bg(instance, value, bg=box_bg):
                bg.pos = instance.pos
                bg.size = instance.size
            box.bind(pos=update_box_bg, size=update_box_bg)
            
            p_name = getattr(p, 'name', p.__class__.__name__.capitalize())
            if "(Commander)" in p_name: 
                p_name = p_name.replace(" (Commander)", "") + " [color=ffff00](Commander)[/color]"
            
            title_lbl = Label(text=f"[b]{p_name}[/b]", markup=True, font_size='16sp', size_hint_y=0.3)
            stats_lbl = Label(text=f"[color=aaaaaa]BP:[/color] {p.base_points}  |  [color=ff5555]ATK:[/color] {p.base_atk}  |  [color=5555ff]DEF:[/color] {p.base_def}", markup=True, font_size='14sp', size_hint_y=0.3)
            
            hp1 = getattr(p, 'hidden_passive', None)
            desc1 = hp1.description if hp1 and getattr(hp1, 'passive_type', None) else "None"
            passives_text = f"[color=00ffcc]Passive 1:[/color] {desc1}"
            
            hp2 = getattr(p, 'second_hidden_passive', None)
            if hp2 and getattr(hp2, 'passive_type', None):
                desc2 = hp2.description
                passives_text += f"  |  [color=ff00cc]Passive 2:[/color] {desc2}"
            
            pass_lbl = Label(text=passives_text, markup=True, font_size='12sp', size_hint_y=0.4, halign='center')
            
            box.add_widget(title_lbl)
            box.add_widget(stats_lbl)
            box.add_widget(pass_lbl)
            
            grid.add_widget(box)

        scroll.add_widget(grid)
        self.root_layout.add_widget(scroll)
        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(15))


class TechCard(ButtonBehavior, BoxLayout):
    def __init__(self, title, desc, atk, def_pt, coins, img_path, is_unlocked, is_available, on_click_cb, **kwargs):
        super().__init__(orientation='vertical', padding=dp(5), spacing=dp(2), size_hint=(None, None), size=(dp(120), dp(160)), **kwargs)
        self.is_unlocked = is_unlocked
        self.is_available = is_available
        self.on_click_cb = on_click_cb
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 0.9)
            self.bg = RoundedRectangle(radius=[dp(8)])
            
            if is_unlocked:
                Color(0.9, 0.8, 0.2, 1) 
                width = 2
            elif is_available:
                Color(0.4, 0.8, 0.4, 1) 
                width = 1.5
            else:
                Color(0.3, 0.3, 0.35, 1) 
                width = 1
                
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=width)
            
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Label(text=f"[b]{title}[/b]", markup=True, font_size='13sp', size_hint_y=0.15))
        
        img = Image(source=img_path, allow_stretch=True, keep_ratio=True, size_hint_y=0.4)
        if not is_unlocked and not is_available: img.opacity = 0.4
        self.add_widget(img)
        
        stats_color = "aaaaaa" if not is_unlocked and not is_available else "ffffff"
        self.add_widget(Label(text=f"[color={stats_color}]ATK: {atk} | DEF: {def_pt}\nCoins: {coins}[/color]", markup=True, font_size='11sp', size_hint_y=0.25, halign='center'))
        self.add_widget(Label(text=f"[color=00ffcc]{desc}[/color]", markup=True, font_size='10sp', size_hint_y=0.2, halign='center'))

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def on_release(self):
        if self.is_available and self.on_click_cb:
            self.on_click_cb()

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
        header.add_widget(Label(text=f"[b]UPGRADE PATH: {p_name_display} (Cost: {self.upgrade_cost} Tax)[/b]", markup=True, font_size='20sp', halign='left', color=(1, 0.8, 0.2, 1)))
        
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
                if is_active:
                    Color(0.9, 0.8, 0.2, 1)
                else:
                    Color(0.7, 0.7, 0.7, 1) 
                Line(points=[p1[0], p1[1], p2[0], p2[1]], width=2.5 if is_active else 1.5)

        cx = self.width / 2 if self.width > 1 else dp(400)
        cy = self.height / 2 if self.height > 1 else dp(300)
        card_w, card_h = dp(120), dp(160)
        
        y_top = cy + dp(120)
        y_mid = cy - dp(40)
        y_bot = cy - dp(200)

        b_atk = getattr(p, 'base_atk', p.base_points) if lvl == 0 else p.base_points
        b_def = getattr(p, 'base_def', p.base_points) if lvl == 0 else p.base_points
        
        node_base = TechCard("Base Form", "Default Stats", b_atk, b_def, p.coins, base_img, (lvl == 0), False, None)
        node_base.pos = (cx - card_w/2, y_top - card_h/2)
        self.tree_layout.add_widget(node_base)

        if not has_special:
            n1_unlocked = (lvl >= 1)
            n1_avail = (lvl == 0)
            n1_atk = b_atk + 2
            node_u1 = TechCard("Rank I", "+2 Base ATK", n1_atk, b_def, p.coins, atk1_img, n1_unlocked, n1_avail, lambda: self.do_upgrade("standard"))
            node_u1.pos = (cx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1)
            
            n2_unlocked = (lvl == 2)
            n2_avail = (lvl == 1)
            n2_def = b_def + 2
            node_u2 = TechCard("Rank II", "+2 Base DEF", n1_atk, n2_def, p.coins, def2_img, n2_unlocked, n2_avail, lambda: self.do_upgrade("standard"))
            node_u2.pos = (cx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1.center_x, node_u1.top), n1_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1.center_x, node_u1.y), (node_u2.center_x, node_u2.top), n2_unlocked), 0.1)
            
        else:
            lx = cx - dp(100)
            rx = cx + dp(100)
            
            n1_std_unlocked = (lvl >= 1 and path == "standard")
            n1_std_avail = (lvl == 0)
            node_u1_std = TechCard("Rank I (Combat)", "+2 Base ATK", b_atk+2, b_def, p.coins, atk1_img, n1_std_unlocked, n1_std_avail, lambda: self.do_upgrade("standard"))
            node_u1_std.pos = (lx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1_std)
            
            n2_std_unlocked = (lvl == 2 and path == "standard")
            n2_std_avail = (lvl == 1 and path == "standard")
            node_u2_std = TechCard("Rank II (Combat)", "+2 Base DEF", b_atk+2, b_def+2, p.coins, def2_img, n2_std_unlocked, n2_std_avail, lambda: self.do_upgrade("standard"))
            node_u2_std.pos = (lx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2_std)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1_std.center_x, node_u1_std.top), n1_std_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_std.center_x, node_u1_std.y), (node_u2_std.center_x, node_u2_std.top), n2_std_unlocked), 0.1)

            n1_spc_unlocked = (lvl >= 1 and path == "special")
            n1_spc_avail = (lvl == 0)
            desc1 = "Reroll Hidden Passive" if not n1_spc_unlocked else getattr(p.hidden_passive, 'description', 'Passive Re-rolled')
            n1_spc_atk = b_atk if not n1_spc_unlocked else p.base_atk
            n1_spc_def = b_def if not n1_spc_unlocked else p.base_def
            
            node_u1_spc = TechCard("Rank I (Utility)", desc1, n1_spc_atk, n1_spc_def, p.coins, spec1_img, n1_spc_unlocked, n1_spc_avail, lambda: self.do_upgrade("special"))
            node_u1_spc.pos = (rx - card_w/2, y_mid - card_h/2)
            self.tree_layout.add_widget(node_u1_spc)
            
            n2_spc_unlocked = (lvl == 2 and path == "special")
            n2_spc_avail = (lvl == 1 and path == "special")
            desc2 = "Gain 2nd Hidden Passive" if not n2_spc_unlocked else getattr(p.second_hidden_passive, 'description', '2nd Passive Active')
            
            node_u2_spc = TechCard("Rank II (Utility)", desc2, p.base_atk, p.base_def, p.coins, spec2_img, n2_spc_unlocked, n2_spc_avail, lambda: self.do_upgrade("special"))
            node_u2_spc.pos = (rx - card_w/2, y_bot - card_h/2)
            self.tree_layout.add_widget(node_u2_spc)
            
            Clock.schedule_once(lambda dt: draw_line((node_base.center_x, node_base.y), (node_u1_spc.center_x, node_u1_spc.top), n1_spc_unlocked), 0.1)
            Clock.schedule_once(lambda dt: draw_line((node_u1_spc.center_x, node_u1_spc.y), (node_u2_spc.center_x, node_u2_spc.top), n2_spc_unlocked), 0.1)

    def do_upgrade(self, path):
        app = App.get_running_app()
        app.play_click_sound()
        
        faction = app.current_map_turn
        if app.tax_points.get(faction, 0) < self.upgrade_cost:
            return
            
        app.tax_points[faction] -= self.upgrade_cost
        
        if hasattr(self.piece, 'upgrade_piece'):
            self.piece.upgrade_piece(path)
            
        self.draw_tree()
        if self.update_callback:
            self.update_callback()