# screens/campaign_map_screen.py
import random
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock

def check_rect_overlap(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

def is_overlapping_any(rect, rect_list):
    for r in rect_list:
        if check_rect_overlap(rect, r): return True
    return False

def get_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

class UnitCounter(BoxLayout):
    def __init__(self, piece_name, count, update_cb, img_path, cost=0, can_recruit=False, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(5), **kwargs)
        self.piece_name = piece_name
        self.count = count
        self.update_cb = update_cb
        self.cost = cost

        self.add_widget(Image(source=img_path, size_hint_x=0.2, allow_stretch=True, keep_ratio=True))
        name_lbl = f"[b]{piece_name.capitalize()}[/b]"
        if cost > 0: name_lbl += f"\n[size=12sp][color=ffff00]Cost: {cost}[/color][/size]"
        self.add_widget(Label(text=name_lbl, markup=True, size_hint_x=0.3, halign='left'))
        
        self.lbl_count = Label(text=f"[b]{self.count}[/b]", markup=True, size_hint_x=0.3, font_size='18sp')
        self.add_widget(self.lbl_count)
        
        self.btn_plus = Button(text="[b]+[/b]", markup=True, size_hint_x=0.2, background_color=(0.2, 0.8, 0.2, 1))
        self.btn_plus.disabled = not can_recruit
        self.btn_plus.bind(on_release=self.increase)
        self.add_widget(self.btn_plus)

    def increase(self, instance):
        if self.update_cb(self.piece_name, self.count + 1, self.cost):
            self.count += 1
            self.lbl_count.text = f"[b]{self.count}[/b]"

class ArmyManagementPopup(ModalView):
    def __init__(self, node, app, **kwargs):
        super().__init__(size_hint=(0.85, 0.85), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        self.node = node
        self.app = app
        self.temp_army = node.army.copy()
        
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.6, 0.2, 1)
            self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=2)
        root.bind(pos=self._update_bg, size=self._update_bg)

        header_box = BoxLayout(size_hint_y=0.1)
        header_box.add_widget(Label(text=f"[b][color=d4af37]ARMY HQ - {node.node_type.upper()}[/color][/b]", markup=True, font_size='22sp'))
        self.lbl_tax = Label(text="", markup=True, font_size='18sp')
        header_box.add_widget(self.lbl_tax)
        root.add_widget(header_box)

        content_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=0.75)
        left_panel = ScrollView(size_hint_x=0.6)
        self.counter_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.counter_grid.bind(minimum_height=self.counter_grid.setter('height'))
        left_panel.add_widget(self.counter_grid)
        content_box.add_widget(left_panel)

        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=dp(10))
        with right_panel.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rp_bg = RoundedRectangle(radius=[dp(10)])
        right_panel.bind(pos=lambda i,v: setattr(self.rp_bg, 'pos', i.pos), size=lambda i,v: setattr(self.rp_bg, 'size', i.size))
        
        self.lbl_stats = Label(text="", markup=True, size_hint_y=0.5, font_size='15sp', halign='left', valign='top')
        self.lbl_stats.bind(size=self.lbl_stats.setter('text_size'))
        right_panel.add_widget(self.lbl_stats)

        self.btn_quick = Button(text="[b]QUICK RECRUIT (7 TAX)[/b]", markup=True, size_hint_y=0.2, background_color=(0.8, 0.6, 0.1, 1))
        self.btn_quick.bind(on_release=self.quick_recruit)
        right_panel.add_widget(self.btn_quick)
        
        content_box.add_widget(right_panel)
        root.add_widget(content_box)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=dp(20))
        btn_cancel = Button(text="[b]CLOSE[/b]", markup=True, background_color=(0.5, 0.2, 0.2, 1))
        btn_cancel.bind(on_release=self.dismiss)
        btn_confirm = Button(text="[b]SAVE ARMY[/b]", markup=True, background_color=(0.2, 0.6, 0.2, 1))
        btn_confirm.bind(on_release=self.confirm_save)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_confirm)
        root.add_widget(btn_box)

        self.add_widget(root)
        self.build_recruit_ui()
        self.update_summary()

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]

    def build_recruit_ui(self):
        self.counter_grid.clear_widgets()
        theme = getattr(self.app, f'selected_unit_{self.node.faction}', 'Medieval Knights')
        tribe = theme.lower().replace(" ", "") if theme != "Medieval Knights" else "medieval"
        categories = {'HEADER': [('king', 0), ('prince', 0)], 'HEAVY (Cost: 2)': [('queen', 2), ('rook', 2), ('bishop', 2), ('knight', 2)], 'LIGHT (Cost: 1)': [('pawn', 1)]}
        can_heavy = (self.node.node_type == 'castle')
        for cat_name, pieces in categories.items():
            self.counter_grid.add_widget(Label(text=f"[color=aaddff][b]--- {cat_name} ---[/b][/color]", markup=True, size_hint_y=None, height=dp(30), halign='left'))
            for p, cost in pieces:
                num = {'pawn':6, 'rook':3, 'knight':4, 'bishop':5, 'queen':2, 'king':1}.get(p, 1)
                img_path = f"assets/pieces/{tribe}/{self.node.faction}/chess {tribe}{num}.png"
                if p == 'prince': img_path = f"assets/pieces/{tribe}/{self.node.faction}/chess {tribe}1.png"
                
                allow_recruit = True
                if cost == 0: allow_recruit = False
                if not can_heavy and cost == 2: allow_recruit = False
                counter = UnitCounter(p, self.temp_army.get(p, 0), self.on_recruit_attempt, img_path, cost=cost, can_recruit=allow_recruit)
                self.counter_grid.add_widget(counter)

    def on_recruit_attempt(self, piece_name, new_count, cost):
        tax = self.app.tax_points[self.node.faction]
        if tax < cost: return False
        headers = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
        heavies = sum([self.temp_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        total = headers + heavies + self.temp_army.get('pawn', 0)
        max_cap = 18 if headers > 0 else 8
        if total >= max_cap: return False
        if piece_name == 'pawn' and heavies > 9: return False 
        
        self.app.tax_points[self.node.faction] -= cost
        self.temp_army[piece_name] = new_count
        self.update_summary()
        return True

    def quick_recruit(self, instance):
        tax = self.app.tax_points[self.node.faction]
        if tax < 7: return
        target = {'queen': 1, 'rook': 2, 'bishop': 2, 'knight': 2, 'pawn': 8}
        self.app.tax_points[self.node.faction] -= 7
        for p, target_count in target.items():
            while self.temp_army.get(p, 0) < target_count:
                headers = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
                curr_heavies = sum([self.temp_army.get(h, 0) for h in ['queen', 'rook', 'bishop', 'knight']])
                if headers + curr_heavies + self.temp_army.get('pawn', 0) >= (18 if headers > 0 else 8): break
                if p in ['queen', 'rook', 'bishop', 'knight'] and curr_heavies >= 9:
                    self.temp_army['pawn'] += 1
                else:
                    self.temp_army[p] += 1
        self.build_recruit_ui()
        self.update_summary()
        self.app.play_click_sound()

    def update_summary(self):
        tax = self.app.tax_points[self.node.faction]
        self.lbl_tax.text = f"TAX POINTS: [color=00ff00]{tax}[/color]"
        light_count = self.temp_army.get('pawn', 0)
        heavy_count = sum([self.temp_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        header_count = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
        max_cap = 18 if header_count > 0 else 8
        stats = f"Capacity: [b]{light_count+heavy_count+header_count} / {max_cap}[/b]\nHeavy: [color=ff6666]{heavy_count}[/color]\nLight: [color=66ff66]{light_count}[/color]\n"
        self.lbl_stats.text = stats

    def confirm_save(self, instance):
        self.node.army = self.temp_army.copy()
        self.app.play_click_sound()
        self.dismiss()

class TroopTransferCounter(BoxLayout):
    def __init__(self, piece_name, base_count, update_cb, img_path, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(5), **kwargs)
        self.piece_name = piece_name
        self.base_count = base_count
        self.army_count = 0
        self.update_cb = update_cb

        self.add_widget(Image(source=img_path, size_hint_x=0.15, allow_stretch=True, keep_ratio=True))
        self.add_widget(Label(text=f"[b]{piece_name.capitalize()}[/b]", markup=True, size_hint_x=0.25, halign='left'))
        self.lbl_base = Label(text=f"Base:\n[b]{self.base_count}[/b]", markup=True, size_hint_x=0.15, halign='center')
        self.add_widget(self.lbl_base)

        btn_left = Button(text="<", size_hint_x=0.1, background_color=(0.8, 0.2, 0.2, 1))
        btn_left.bind(on_release=self.move_to_base)
        self.add_widget(btn_left)
        btn_right = Button(text=">", size_hint_x=0.1, background_color=(0.2, 0.8, 0.2, 1))
        btn_right.bind(on_release=self.move_to_army)
        self.add_widget(btn_right)

        self.lbl_army = Label(text=f"March:\n[b]{self.army_count}[/b]", markup=True, size_hint_x=0.15, halign='center', color=(1, 0.8, 0, 1))
        self.add_widget(self.lbl_army)

    def move_to_army(self, instance):
        if self.base_count > 0:
            if self.update_cb(self.piece_name, 1): 
                self.base_count -= 1; self.army_count += 1
                self.lbl_base.text = f"Base:\n[b]{self.base_count}[/b]"
                self.lbl_army.text = f"March:\n[b]{self.army_count}[/b]"

    def move_to_base(self, instance):
        if self.army_count > 0:
            if self.update_cb(self.piece_name, -1): 
                self.base_count += 1; self.army_count -= 1
                self.lbl_base.text = f"Base:\n[b]{self.base_count}[/b]"
                self.lbl_army.text = f"March:\n[b]{self.army_count}[/b]"

class MarchSetupPopup(ModalView):
    def __init__(self, source_node, target_node, app, map_screen, **kwargs):
        super().__init__(size_hint=(0.7, 0.8), auto_dismiss=False, background_color=(0,0,0,0.8), **kwargs)
        self.source_node = source_node; self.target_node = target_node
        self.app = app; self.map_screen = map_screen
        self.temp_base_army = source_node.army.copy()
        self.marching_army = {'king': 0, 'prince': 0, 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0}
        
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with root.canvas.before:
            Color(0.15, 0.15, 0.2, 0.95); self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.3, 0.2, 1); self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=2)
        root.bind(pos=self._update_bg, size=self._update_bg)

        title_text = f"MARCHING TO {target_node.faction.upper()} {target_node.node_type.upper()}"
        root.add_widget(Label(text=f"[b][color=ffaa55]{title_text}[/color][/b]", markup=True, font_size='22sp', size_hint_y=0.1))
        self.lbl_status = Label(text="Capacity: 0 / 8", font_size='16sp', size_hint_y=0.05, color=(0.8,0.8,0.8,1))
        root.add_widget(self.lbl_status)

        self.scroll = ScrollView(size_hint_y=0.7)
        self.grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid); root.add_widget(self.scroll)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=dp(20))
        btn_cancel = Button(text="[b]CANCEL[/b]", markup=True, background_color=(0.5, 0.2, 0.2, 1))
        btn_cancel.bind(on_release=self.dismiss)
        btn_str = "[b]DEPLOY COMBAT[/b]" if target_node.faction != source_node.faction else "[b]MERGE ARMY[/b]"
        self.btn_confirm = Button(text=btn_str, markup=True, background_color=(0.8, 0.2, 0.2, 1) if target_node.faction != source_node.faction else (0.2, 0.6, 0.8, 1))
        self.btn_confirm.bind(on_release=self.confirm_march)
        btn_box.add_widget(btn_cancel); btn_box.add_widget(self.btn_confirm)
        root.add_widget(btn_box)
        self.add_widget(root); self.build_transfer_ui()

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]

    def build_transfer_ui(self):
        theme = getattr(self.app, f'selected_unit_{self.source_node.faction}', 'Medieval Knights')
        tribe = theme.lower().replace(" ", "") if theme != "Medieval Knights" else "medieval"
        for p in ['king', 'prince', 'queen', 'rook', 'bishop', 'knight', 'pawn']:
            if self.temp_base_army.get(p, 0) > 0: 
                num = {'pawn':6, 'rook':3, 'knight':4, 'bishop':5, 'queen':2, 'king':1}.get(p, 1)
                img_path = f"assets/pieces/{tribe}/{self.source_node.faction}/chess {tribe}{num}.png"
                if p == 'prince': img_path = f"assets/pieces/{tribe}/{self.source_node.faction}/chess {tribe}1.png"
                self.grid.add_widget(TroopTransferCounter(p, self.temp_base_army[p], self.on_transfer_attempt, img_path))

    def on_transfer_attempt(self, piece_name, direction):
        if direction == 1: 
            headers = self.marching_army.get('king', 0) + self.marching_army.get('prince', 0)
            if piece_name in ['king', 'prince']: headers += 1
            heavies = sum([self.marching_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
            if piece_name in ['queen', 'rook', 'bishop', 'knight']: heavies += 1
            lights = self.marching_army.get('pawn', 0)
            if piece_name == 'pawn': lights += 1
            if headers + heavies + lights > (18 if headers > 0 else 8): return False 
            self.marching_army[piece_name] += 1; self.temp_base_army[piece_name] -= 1
        else: 
            self.marching_army[piece_name] -= 1; self.temp_base_army[piece_name] += 1
        self.update_status(); return True

    def update_status(self):
        headers = self.marching_army.get('king', 0) + self.marching_army.get('prince', 0)
        heavies = sum([self.marching_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        lights = self.marching_army.get('pawn', 0)
        self.lbl_status.text = f"Marching Capacity: [b]{headers+heavies+lights} / {18 if headers > 0 else 8}[/b]  |  [color=ffcc00]Header: {'Yes' if headers > 0 else 'No'}[/color]"

    def confirm_march(self, instance):
        if sum(self.marching_army.values()) == 0: return 
        self.app.play_click_sound()
        self.source_node.army = self.temp_base_army.copy() 
        if self.target_node.faction == self.source_node.faction:
            for p, count in self.marching_army.items(): self.target_node.army[p] += count
        else:
            self.app.combat_marching_army = self.marching_army.copy() 
            self.map_screen.initiate_combat(self.source_node, self.target_node)
        self.dismiss()

class NodeActionMenu(ModalView):
    def __init__(self, node, app, map_screen, **kwargs):
        super().__init__(size_hint=(0.4, 0.4), auto_dismiss=True, background_color=(0,0,0,0.8), **kwargs)
        self.node = node; self.app = app; self.map_screen = map_screen
        root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        with root.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95); self.bg = RoundedRectangle(radius=[dp(12)])
            Color(0.8, 0.6, 0.2, 1); self.border_line = Line(rounded_rectangle=[root.x, root.y, root.width, root.height, dp(12)], width=2)
        root.bind(pos=self._update_bg, size=self._update_bg)
        root.add_widget(Label(text=f"[b]SELECT ACTION[/b]", markup=True, font_size='20sp', size_hint_y=0.2))
        btn_manage = Button(text="[b]MANAGE ARMY[/b]", markup=True, background_color=(0.2, 0.4, 0.8, 1))
        btn_manage.bind(on_release=self.open_manage)
        root.add_widget(btn_manage)
        btn_march = Button(text="[b]MARCH / ATTACK[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1))
        btn_march.bind(on_release=self.start_march)
        root.add_widget(btn_march)
        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]

    def open_manage(self, instance):
        self.app.play_click_sound(); self.dismiss(); ArmyManagementPopup(node=self.node, app=self.app).open()

    def start_march(self, instance):
        self.app.play_click_sound(); self.dismiss(); self.map_screen.start_marching(self.node)

class MapNode(Button):
    def __init__(self, node_type, faction, node_id, is_main_base=False, **kwargs):
        super().__init__(**kwargs)
        self.node_type, self.faction, self.node_id, self.is_main_base = node_type, faction, node_id, is_main_base 
        self.has_claimed_prince, self.neighbors = False, []             
        
        if self.is_main_base: self.army = {'king': 1, 'queen': 1, 'rook': 2, 'bishop': 2, 'knight': 2, 'pawn': 8, 'prince': 0}
        elif faction == 'red':
            if node_type == 'castle': self.army = {'king': 1, 'queen': 1, 'rook': 2, 'bishop': 2, 'knight': 2, 'pawn': 8, 'prince': 0}
            else: self.army = {'king': 0, 'queen': 0, 'rook': 1, 'bishop': 1, 'knight': 1, 'pawn': 8, 'prince': 0}
        else: self.army = {'king': 0, 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0, 'prince': 0}
        
        self.size_hint, self.size, self.background_color = (None, None), (dp(50), dp(50)), (0, 0, 0, 0) 
        with self.canvas.before:
            if self.is_main_base:
                Color(1, 0.8, 0, 0.4)
                self.aura = Ellipse(pos=(self.x - dp(10), self.y - dp(10)), size=(self.width + dp(20), self.height + dp(20)))
            else: self.aura = None
            if self.node_type == 'castle':
                self.color_inst = Color(0.5, 0.5, 0.55, 1); self.shape = Rectangle(pos=self.pos, size=self.size)
            else:
                self.color_inst = Color(0.85, 0.85, 0.85, 1); self.shape = Ellipse(pos=self.pos, size=self.size)
                
            if faction == 'white': fac_color = (0.9, 0.9, 0.9, 1)
            elif faction == 'black': fac_color = (0.1, 0.1, 0.1, 1)
            else: fac_color = (0.8, 0.2, 0.2, 1) 
            Color(*fac_color); self.border_line = Line(circle=(self.center_x, self.center_y, dp(28)), width=3)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.shape.pos, self.shape.size = self.pos, self.size
        self.border_line.circle = (self.center_x, self.center_y, dp(28))
        if self.aura: self.aura.pos, self.aura.size = (self.x - dp(10), self.y - dp(10)), (self.width + dp(20), self.height + dp(20))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        map_screen = app.root.get_screen('campaign_map')
        
        if map_screen.marching_from_node:
            if self in map_screen.marching_from_node.neighbors:
                MarchSetupPopup(source_node=map_screen.marching_from_node, target_node=self, app=app, map_screen=map_screen).open()
            else: map_screen.status_lbl.text = "[color=ff0000]TOO FAR! SELECT ADJACENT BASE.[/color]"
            map_screen.marching_from_node = None 
            return

        current_turn = getattr(app, 'current_map_turn', 'white')
        if self.faction == current_turn: NodeActionMenu(node=self, app=app, map_screen=map_screen).open()
        else: map_screen.status_lbl.text = "[color=ff0000]ENEMY TERRITORY. SELECT YOUR BASE TO ATTACK FROM.[/color]"

class CampaignMapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.map_content = FloatLayout(size_hint=(None, None), size=(9600, 5400))
        self.scroll_view.add_widget(self.map_content)
        self.ui_layer = FloatLayout()
        
        self.add_widget(self.scroll_view)
        self.add_widget(self.ui_layer)
        
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9); self.top_bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=self._update_top_bg, size=self._update_top_bg)
            
        back_btn = Button(text="< SETUP", size_hint_x=0.1, background_color=(0.5, 0.1, 0.1, 1))
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - TURN 1", bold=True, color=(1, 0.8, 0.2, 1), font_size='18sp', markup=True)
        top_bar.add_widget(self.status_lbl)
        
        next_btn = Button(text="END TURN >", size_hint_x=0.15, background_color=(0.2, 0.6, 0.2, 1))
        next_btn.bind(on_release=self.end_turn)
        top_bar.add_widget(next_btn)
        self.ui_layer.add_widget(top_bar)
        
        self.nodes_list = []
        self.marching_from_node = None 

    def _update_top_bg(self, instance, value):
        self.top_bg.pos, self.top_bg.size = instance.pos, instance.size

    def on_enter(self):
        app = App.get_running_app()
        # ✨ เช็คเพื่อให้จดจำแมพ (ไม่สร้างใหม่ถ้าเพิ่งรบเสร็จ)
        if not getattr(app, 'campaign_initialized', False):
            app.current_map_turn = 'white'
            app.turn_number = 1
            app.tax_points = {'white': 0, 'black': 0} 
            self.marching_from_node = None
            Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)
            app.campaign_initialized = True
        else:
            self.marching_from_node = None

    def go_back(self, instance):
        app = App.get_running_app()
        app.campaign_initialized = False # รีเซ็ตแมพเมื่อกลับหน้า Setup
        self.manager.current = 'setup'

    def start_marching(self, source_node):
        self.marching_from_node = source_node
        self.status_lbl.text = "[color=00ffff]SELECT ADJACENT TARGET TO MARCH / ATTACK...[/color]"

    def initiate_combat(self, source_node, target_node):
        app = App.get_running_app()
        app.combat_source = source_node
        app.combat_target = target_node
        
        target_army = target_node.army.copy()
        if target_node.faction == 'red':
            target_count = random.randint(8, 12)
            current_count = sum(target_army.values())
            removable_pieces = ['queen', 'rook', 'bishop', 'knight', 'pawn']
            
            while current_count > target_count:
                available_to_remove = [p for p in removable_pieces if target_army.get(p, 0) > 0]
                if not available_to_remove: break
                p_to_remove = random.choice(available_to_remove)
                target_army[p_to_remove] -= 1
                current_count -= 1
                
        app.combat_target_army = target_army
        
        gameplay_screen = self.manager.get_screen('gameplay')
        gameplay_screen.setup_game(mode='Divide_Conquer')
        self.manager.current = 'gameplay'

    def end_turn(self, instance):
        app = App.get_running_app()
        app.play_click_sound()
        self.marching_from_node = None
        
        tax_collected = sum([3 if n.node_type == 'village' else 6 for n in self.nodes_list if n.faction == app.current_map_turn])
        app.tax_points[app.current_map_turn] += tax_collected
        
        if app.current_map_turn == 'white':
            app.current_map_turn = 'black'
            self.status_lbl.text = f"DARK ABYSS (BLACK) - TURN {app.turn_number}"
            self.status_lbl.color = (0.6, 0.6, 0.8, 1)
        else:
            app.current_map_turn = 'white'
            app.turn_number += 1
            self.status_lbl.text = f"DIVINE ORDER (WHITE) - TURN {app.turn_number}"
            self.status_lbl.color = (1, 0.8, 0.2, 1)

    def generate_procedural_map(self):
        self.map_content.clear_widgets()
        self.map_content.canvas.before.clear()
        self.nodes_list.clear()
        
        app = App.get_running_app()
        size_val = getattr(app, 'selected_board', 'Size_S')
        num_castles, num_villages = {'Size_S':(1,2), 'Size_M':(2,3), 'Size_L':(3,4)}.get(size_val, (1,2))
        map_w, map_h = 9600, 5400
        water_rects, nodes_data = [], []

        with self.map_content.canvas.before:
            Color(0.12, 0.18, 0.12, 1)
            Rectangle(pos=(0, 0), size=(map_w, map_h))
            Color(0.1, 0.4, 0.6, 0.6)
            for _ in range(150):
                w, h = random.randint(200, 700), random.randint(200, 700)
                x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                if not is_overlapping_any((x, y, w, h), water_rects):
                    water_rects.append((x, y, w, h))
                    Rectangle(pos=(x, y), size=(w, h))

        def generate_nodes_for_faction(base_faction, count_castles, count_villages, min_x, max_x):
            faction_nodes = []
            types_to_spawn = ['castle'] * count_castles + ['village'] * count_villages
            for i, n_type in enumerate(types_to_spawn):
                for attempt in range(500):
                    nx, ny = random.randint(min_x, max_x), random.randint(300, map_h - 300)
                    if is_overlapping_any((nx-80, ny-80, 160, 160), water_rects): continue
                    too_close = any(get_distance((nx, ny), ex['pos']) < dp(200) for ex in nodes_data + faction_nodes)
                    if not too_close:
                        is_main = (i == 0)
                        faction_nodes.append({'pos': (nx, ny), 'faction': base_faction if is_main else 'red', 'type': n_type, 'id': f"{base_faction[0].upper()}{i}", 'main': is_main})
                        break
            return faction_nodes

        w_nodes = generate_nodes_for_faction('white', num_castles, num_villages, 500, 4000)
        b_nodes = generate_nodes_for_faction('black', num_castles, num_villages, 5600, 9100)
        nodes_data = w_nodes + b_nodes

        nodes_dict = {}
        for data in nodes_data:
            node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'])
            node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
            self.nodes_list.append(node)
            nodes_dict[data['id']] = node

        def create_connections(nodes):
            edges = []
            if not nodes: return edges
            visited, unvisited = [nodes[0]], nodes[1:]
            while unvisited:
                min_dist, best_edge, best_u = float('inf'), None, None
                for v in visited:
                    for u in unvisited:
                        dist = get_distance(v['pos'], u['pos'])
                        if dist < min_dist: min_dist, best_edge, best_u = dist, (v, u), u
                edges.append(best_edge); visited.append(best_u); unvisited.remove(best_u)
            for _ in range(len(nodes) // 2):
                u, v = random.sample(nodes, 2)
                if (u, v) not in edges and (v, u) not in edges: edges.append((u, v))
            return edges

        white_edges = create_connections(w_nodes)
        black_edges = create_connections(b_nodes)
        
        min_cross, cross_edge = float('inf'), None
        for w in w_nodes:
            for b in b_nodes:
                d = get_distance(w['pos'], b['pos'])
                if d < min_cross: min_cross, cross_edge = d, (w, b)

        with self.map_content.canvas.before:
            Color(0.85, 0.75, 0.3, 0.8)
            for u, v in white_edges + black_edges:
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4)
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])
            if cross_edge:
                u, v = cross_edge
                Color(0.9, 0.4, 0.2, 0.9)
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=8)
                nodes_dict[u['id']].neighbors.append(nodes_dict[v['id']])
                nodes_dict[v['id']].neighbors.append(nodes_dict[u['id']])

        for node in self.nodes_list: self.map_content.add_widget(node)
        self.scroll_view.scroll_x, self.scroll_view.scroll_y = 0.5, 0.5