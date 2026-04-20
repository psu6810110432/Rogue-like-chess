# screens/match_setup/setup_section.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior

# ------------------ ระบบ Hover Tooltip สำหรับแผนที่ ------------------
class HoverTooltip(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.markup = True
        self.font_size = '13sp'
        self.halign = 'left'
        self.valign = 'middle'
        
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 0.95)
            self.bg = RoundedRectangle(radius=[dp(8)])
            Color(0.83, 0.68, 0.21, 1)
            self.border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)], width=1.2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics, texture_size=self.update_size)

    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(8)]

    def update_size(self, *args):
        self.size = (self.texture_size[0] + dp(30), self.texture_size[1] + dp(20))

class HoverInfoIcon(Label):
    def __init__(self, info_text, **kwargs):
        super().__init__(**kwargs)
        self.text = "[b]?[/b]"
        self.markup = True
        self.color = (0.83, 0.68, 0.21, 1)
        self.size_hint = (None, None)
        self.size = (dp(22), dp(22))
        self.info_text = info_text
        self._tooltip = None

        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.bg = RoundedRectangle(radius=[self.height/2])
            Color(0.83, 0.68, 0.21, 1)
            self.border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.height/2], width=1)
            
        self.bind(pos=self.update_bg, size=self.update_bg)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.bg.radius = [self.height/2]
        self.border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.height/2]

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window(): return
        wx, wy = self.to_window(self.x, self.y)
        if wx <= pos[0] <= wx + self.width and wy <= pos[1] <= wy + self.height:
            if not self._tooltip:
                self._tooltip = HoverTooltip(text=self.info_text)
                Window.add_widget(self._tooltip)
            self._tooltip.pos = (pos[0] + dp(15), pos[1] - self._tooltip.height - dp(15))
        else:
            if self._tooltip:
                Window.remove_widget(self._tooltip)
                self._tooltip = None

# ------------------ ระบบปุ่มกด Popup สำหรับ Legion ------------------
class ClickableInfoIcon(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "[b]?[/b]"
        self.markup = True
        self.color = (0.83, 0.68, 0.21, 1)
        self.size_hint = (None, None)
        self.size = (dp(26), dp(26))

        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.bg = RoundedRectangle(radius=[self.height/2])
            Color(0.83, 0.68, 0.21, 1)
            self.border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.height/2], width=1.5)
            
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.bg.radius = [self.height/2]
        self.border.rounded_rectangle = [self.x, self.y, self.width, self.height, self.height/2]

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()
        from components.encyclopedia_popup import EncyclopediaPopup
        EncyclopediaPopup().open()


# ------------------ ส่วนหลักของ UI ------------------
class SelectionCard(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.markup = True
        self.val = ''
        self.is_selected = False
        
        with self.canvas.before:
            self.card_bg_color = Color(0.1, 0.1, 0.12, 0.7) 
            self.card_rect = RoundedRectangle(radius=[12])
            self.card_border_color = Color(0.3, 0.3, 0.35, 1) 
            self.card_border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 12], width=1.2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics, state=self.update_state)

    def update_graphics(self, *args):
        self.card_rect.pos = self.pos
        self.card_rect.size = self.size
        self.card_border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 12]

    def update_state(self, *args):
        if not self.is_selected:
            if self.state == 'down':
                self.card_bg_color.rgba = (0.2, 0.2, 0.25, 0.8)
            else:
                self.card_bg_color.rgba = (0.1, 0.1, 0.12, 0.7)

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.card_bg_color.rgba = (0.15, 0.2, 0.15, 0.85) 
            self.card_border_color.rgba = (0.83, 0.68, 0.21, 1) 
            self.card_border_line.width = 2.0
        else:
            self.card_bg_color.rgba = (0.1, 0.1, 0.12, 0.7)
            self.card_border_color.rgba = (0.3, 0.3, 0.35, 1)
            self.card_border_line.width = 1.2


class SetupSection(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=[20, 10, 20, 10], spacing=15, **kwargs)
        self.app = App.get_running_app()
        self.app.match_type = '' # PVE / PVP
        self.app.sub_mode = ''   # Classic / Divide_Conquer
        self.app.selected_board = ''
        self.app.selected_unit_white = ''
        self.app.selected_unit_black = ''

        # 1. SELECT MATCH TYPE
        self.type_box = BoxLayout(orientation='vertical', size_hint_y=0.18, spacing=5)
        self.add_header(self.type_box, "1. SELECT MATCH TYPE")
        
        type_grid = GridLayout(cols=2, spacing=20)
        self.type_cards = []
        for m in ['PVE', 'PVP']:
            desc = "COMMANDER vs AI" if m=='PVE' else "DUEL BETWEEN LORDS"
            card = SelectionCard(text=f"[b]{m}[/b]\n[size=14sp][color=a0a0a0]{desc}[/color][/size]")
            card.val = m
            card.bind(on_press=self.play_sound, on_release=self.on_type_select)
            self.type_cards.append(card)
            type_grid.add_widget(card)
        self.type_box.add_widget(type_grid)
        self.add_widget(self.type_box)

        # 2. SELECT GAME MODE
        self.mode_box = BoxLayout(orientation='vertical', size_hint_y=0.18, spacing=5, opacity=0, disabled=True)
        self.add_header(self.mode_box, "2. SELECT GAME MODE")
        
        mode_grid = GridLayout(cols=2, spacing=20)
        self.mode_cards = []
        
        modes = [
            ('Classic', "CLASSIC CHESS", "Standard Rules & Combat"),
            ('Divide_Conquer', "DIVIDE & CONQUER", "Total War Style, Farming & Conquest")
        ]
        for val, title, desc in modes:
            card = SelectionCard(text=f"[b]{title}[/b]\n[size=13sp][color=a0a0a0]{desc}[/color][/size]")
            card.val = val
            card.bind(on_press=self.play_sound, on_release=self.on_mode_select)
            self.mode_cards.append(card)
            mode_grid.add_widget(card)
        self.mode_box.add_widget(mode_grid)
        self.add_widget(self.mode_box)

        # 3. SELECT MAP / SIZE (Dynamically changes based on Mode)
        self.map_box = BoxLayout(orientation='vertical', size_hint_y=0.22, spacing=5, opacity=0, disabled=True)
        self.map_header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        self.map_box.add_widget(self.map_header_layout)
        
        self.map_grid = GridLayout(cols=5, spacing=12)
        self.map_box.add_widget(self.map_grid)
        self.add_widget(self.map_box)

        # 4. SELECT FACTIONS
        self.fac_box = BoxLayout(orientation='vertical', size_hint_y=0.42, spacing=5, opacity=0, disabled=True)
        self.add_header(self.fac_box, "4. CHOOSE YOUR LEGION", clickable_info=True)
        
        self.fac_split = BoxLayout(orientation='horizontal', spacing=30)
        
        # WHITE
        self.w_box = BoxLayout(orientation='vertical', spacing=8, opacity=0)
        self.w_box.add_widget(Label(text="DIVINE ORDER (WHITE)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.white_cards = []
        # ✨ อัปเดตรายชื่อเผ่า และเพิ่ม Bandit
        for f in ['The Knight Company', 'The Chaos Mankind', 'The Deep Anomaly', 'The Ancient Runes']:
            card = SelectionCard(text=f"[b][size=16sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_press=self.play_sound, on_release=self.on_white_select)
            self.white_cards.append(card)
            self.w_box.add_widget(card)
            
        # BLACK
        self.b_box = BoxLayout(orientation='vertical', spacing=8, opacity=0)
        self.b_box.add_widget(Label(text="DARK ABYSS (BLACK)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.black_cards = []
        # ✨ อัปเดตรายชื่อเผ่า และเพิ่ม Bandit
        for f in ['The Knight Company', 'The Chaos Mankind', 'The Deep Anomaly', 'The Ancient Runes']:
            card = SelectionCard(text=f"[b][size=16sp]{f}[/size][/b]")
            card.val = f
            card.bind(on_press=self.play_sound, on_release=self.on_black_select)
            self.black_cards.append(card)
            self.b_box.add_widget(card)
            
        self.fac_split.add_widget(self.w_box)
        self.fac_split.add_widget(self.b_box)
        self.fac_box.add_widget(self.fac_split)
        self.add_widget(self.fac_box)

        self.update_selections()

    def add_header(self, parent_box, text, tooltip_text=None, clickable_info=False):
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        
        lbl = Label(text=f"[color=d4af37][b]{text}[/b][/color]", markup=True, font_size='20sp', halign='left', size_hint_x=None)
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'width', value[0]))
        header_layout.add_widget(lbl)
        
        if tooltip_text:
            icon = HoverInfoIcon(info_text=tooltip_text)
            icon_container = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=1)
            icon_container.add_widget(icon)
            header_layout.add_widget(icon_container)
        elif clickable_info:
            icon = ClickableInfoIcon()
            icon_container = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=1)
            icon_container.add_widget(icon)
            header_layout.add_widget(icon_container)
        else:
            header_layout.add_widget(Widget(size_hint_x=1))
            
        parent_box.add_widget(header_layout)

    def play_sound(self, instance):
        if hasattr(self.app, 'play_click_sound'):
            self.app.play_click_sound()

    def update_selections(self):
        for c in self.type_cards: c.set_selected(c.val == self.app.match_type)
        for c in self.mode_cards: c.set_selected(c.val == self.app.sub_mode)
        for c in getattr(self, 'map_cards', []): c.set_selected(c.val == self.app.selected_board)
        for c in self.white_cards: c.set_selected(c.val == self.app.selected_unit_white)
        for c in self.black_cards: c.set_selected(c.val == self.app.selected_unit_black)

    def on_type_select(self, instance):
        self.app.match_type = instance.val
        self.update_selections()
        
        self.mode_box.disabled = False
        Animation(opacity=1, duration=0.3).start(self.mode_box)

    def on_mode_select(self, instance):
        self.app.sub_mode = instance.val
        
        self.load_map_options()
        self.update_selections()
        
        self.map_box.disabled = False
        Animation(opacity=1, duration=0.3).start(self.map_box)

    def load_map_options(self):
        self.map_header_layout.clear_widgets()
        self.map_grid.clear_widgets()
        self.map_cards = []
        
        if self.app.sub_mode == 'Classic':
            lbl = Label(text=f"[color=d4af37][b]3. STRATEGIC BATTLEFIELD[/b][/color]", markup=True, font_size='20sp', halign='left', size_hint_x=None)
            lbl.bind(texture_size=lambda instance, value: setattr(instance, 'width', value[0]))
            self.map_header_layout.add_widget(lbl)
            
            tooltip = (
                "[color=ffcc00][b]Classic:[/b][/color] Standard chess battlefield.\n"
                "[color=00ff44][b]Enchanted Forest:[/b][/color] Thorny vines may sprout.\n"
                "[color=ffaa00][b]Desert Ruins:[/b][/color] Sandstorm affects empty lines.\n"
                "[color=00ccff][b]Frozen Tundra:[/b][/color] Freezes pieces and blocks squares."
            )
            icon_container = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=1)
            icon_container.add_widget(HoverInfoIcon(info_text=tooltip))
            self.map_header_layout.add_widget(icon_container)
            
            self.map_grid.cols = 5
            options = ['Classic Board', 'Enchanted Forest', 'Desert Ruins', 'Frozen Tundra', 'Random Board']
            for mp in options:
                display_name = mp.replace(" Board", "")
                card = SelectionCard(text=f"[b][size=15sp]{display_name}[/size][/b]")
                card.val = mp
                card.bind(on_press=self.play_sound, on_release=self.on_map_select)
                self.map_cards.append(card)
                self.map_grid.add_widget(card)
                
        else: # Divide & Conquer
            lbl = Label(text=f"[color=d4af37][b]3. SELECT WORLD SIZE[/b][/color]", markup=True, font_size='20sp', halign='left', size_hint_x=None)
            lbl.bind(texture_size=lambda instance, value: setattr(instance, 'width', value[0]))
            self.map_header_layout.add_widget(lbl)
            
            tooltip = (
                "Select how many farming bases you can control per side.\n"
                "[b]Small:[/b] 3 Farms per faction\n"
                "[b]Medium:[/b] 5 Farms per faction\n"
                "[b]Large:[/b] 7 Farms per faction"
            )
            icon_container = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=1)
            icon_container.add_widget(HoverInfoIcon(info_text=tooltip))
            self.map_header_layout.add_widget(icon_container)
            
            self.map_grid.cols = 3
            options = [('Size_S', 'SMALL WORLD\n[size=12sp](3 Farming Bases)[/size]'), 
                       ('Size_M', 'MEDIUM WORLD\n[size=12sp](5 Farming Bases)[/size]'), 
                       ('Size_L', 'LARGE WORLD\n[size=12sp](7 Farming Bases)[/size]')]
            for val, display_name in options:
                card = SelectionCard(text=f"[b][size=16sp]{display_name}[/size][/b]")
                card.val = val
                card.bind(on_press=self.play_sound, on_release=self.on_map_select)
                self.map_cards.append(card)
                self.map_grid.add_widget(card)

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