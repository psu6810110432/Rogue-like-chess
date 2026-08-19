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
from kivy.uix.image import Image


def apply_nearest_texture_filter(image_widget):
    image_widget.mag_filter = 'nearest'
    image_widget.min_filter = 'nearest'
    if image_widget.texture:
        image_widget.texture.mag_filter = 'nearest'
        image_widget.texture.min_filter = 'nearest'


class MapSelectionCard(ButtonBehavior, BoxLayout):
    def __init__(self, text, image_source, val, **kwargs):
        super().__init__(orientation='vertical', padding=dp(8), spacing=dp(5), **kwargs)
        self.val = val
        self.is_selected = False
        
        with self.canvas.before:
            self.card_bg_color = Color(0.1, 0.1, 0.12, 0.7)
            self.card_rect = RoundedRectangle(radius=[12])
            self.card_border_color = Color(0.3, 0.3, 0.35, 1)
            self.card_border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 12], width=1.2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics, state=self.update_state)

        # 1. เพิ่มส่วนรูปภาพ + ตั้งค่าความคมชัดผ่านการ bind texture
        self.img = Image(source=image_source, allow_stretch=True, keep_ratio=False, size_hint_y=0.75)
        apply_nearest_texture_filter(self.img)
        self.img.bind(texture=self._update_texture_filter)
        self.add_widget(self.img)

        # 2. เพิ่มส่วนข้อความ
        self.lbl = Label(text=text, markup=True, halign='center', valign='middle', size_hint_y=0.25)
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.add_widget(self.lbl)

    def _update_texture_filter(self, instance, texture):
        # ทำให้รูปคมชัดแบบ Nearest เมื่อ texture ถูกโหลดเสร็จ
        if texture:
            texture.mag_filter = 'nearest'
            texture.min_filter = 'nearest'
            instance.mag_filter = 'nearest'
            instance.min_filter = 'nearest'

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

class IconSelectionCard(ButtonBehavior, BoxLayout):
    def __init__(self, text, image_source, val, **kwargs):
        # เปลี่ยน Layout เป็นแนวตั้ง (รูปภาพอยู่บน)
        super().__init__(orientation='vertical', padding=dp(8), spacing=dp(5), **kwargs)
        self.val = val
        self.is_selected = False
        
        with self.canvas.before:
            self.card_bg_color = Color(0.1, 0.1, 0.12, 0.7)
            self.card_rect = RoundedRectangle(radius=[12])
            self.card_border_color = Color(0.3, 0.3, 0.35, 1)
            self.card_border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 12], width=1.2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics, state=self.update_state)

        # 1. รูปภาพด้านบน
        self.img = Image(source=image_source, allow_stretch=True, keep_ratio=True, size_hint_y=0.7)
        apply_nearest_texture_filter(self.img)
        self.img.bind(texture=self._update_texture_filter)
        self.add_widget(self.img)

        # 2. ข้อความด้านล่าง
        self.lbl = Label(text=text, markup=True, halign='center', valign='middle', size_hint_y=0.3)
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.add_widget(self.lbl)

    def _update_texture_filter(self, instance, texture):
        if texture:
            texture.mag_filter = 'nearest'
            texture.min_filter = 'nearest'

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
            
        if getattr(app, 'sub_mode', 'Classic') == 'Divide_Conquer':
            from components.encyclopedia_dnc_popup import EncyclopediaDNCPopup
            EncyclopediaDNCPopup().open()
        else:
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
        self.app.match_type = '' 
        self.app.sub_mode = ''   
        self.app.selected_board = ''
        self.app.selected_unit_white = ''
        self.app.selected_unit_black = ''
        self.app.selected_time_limit = None  
        self.app.selected_economic_system = False
        
        # จัดเก็บหน้าสองหน้า
        self.page1 = BoxLayout(orientation='vertical', spacing=15)
        self.page2 = BoxLayout(orientation='vertical', spacing=15)
        
        # ================= PAGE 1 =================
        # 1. SELECT MATCH TYPE
        self.type_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=5)
        self.add_header(self.type_box, "1. SELECT MATCH TYPE")
        
        type_grid = GridLayout(cols=2, spacing=15) # เหลือ 2 คอลัมน์เพราะเอา ONLINE ออก
        self.type_cards = []
        type_options = [
            ('PVE', 'PVE', 'COMMANDER vs AI'),
            ('LOCAL_PVP', 'LOCAL PVP', 'Shared Screen Duel'),
        ]
        for val, title, desc in type_options:
            card = SelectionCard(text=f"[b]{title}[/b]\n[size=13sp][color=a0a0a0]{desc}[/color][/size]")
            card.val = val
            card.bind(on_press=self.play_sound, on_release=self.on_type_select)
            self.type_cards.append(card)
            type_grid.add_widget(card)
        self.type_box.add_widget(type_grid)
        self.page1.add_widget(self.type_box)

        # 2. SELECT GAME MODE
        self.mode_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=5, opacity=0, disabled=True)
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
        self.page1.add_widget(self.mode_box)

        # 3. SELECT MAP / SIZE 
        self.map_box = BoxLayout(orientation='vertical', size_hint_y=1, spacing=5, opacity=0, disabled=True)
        self.map_header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        self.map_box.add_widget(self.map_header_layout)
        
        self.map_grid = GridLayout(cols=5, spacing=12)
        self.map_box.add_widget(self.map_grid)
        self.page1.add_widget(self.map_box)


        # ================= PAGE 2 =================
        # 3.5 BATTLEFIELD OPTION (TURN TIME LIMIT)
        self.timer_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(90), spacing=5)
        self.add_header(self.timer_box, "BATTLEFIELD OPTIONS (TIMER)")
        timer_grid = GridLayout(cols=4, spacing=12)
        self.timer_cards = []
        timer_options = [
            (0, 'Unlimited'),
            (180, '3 Minutes'),
            (300, '5 Minutes'),
            (480, '8 Minutes'),
        ]
        for val, display in timer_options:
            card = SelectionCard(text=f"[b][size=15sp]{display}[/size][/b]")
            card.val = val
            card.bind(on_press=self.play_sound, on_release=self.on_timer_select)
            self.timer_cards.append(card)
            timer_grid.add_widget(card)
        self.timer_box.add_widget(timer_grid)
        self.page2.add_widget(self.timer_box)

        self.econ_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(0), spacing=5, opacity=0, disabled=True)
        
        # ใส่ Tooltip เพื่ออธิบายระบบให้ผู้เล่นอ่าน
        tooltip_econ = (
            "[color=d4af37][b]Standard Economy:[/b][/color] Farms produce only Tax.\n"
            "[color=00ff44][b]Advanced Economy:[/b][/color] You can switch farm outputs.\n"
            " - [b]Supplies:[/b] Equals to Tax amount.\n"
            " - [b]Wood:[/b] Lv1=3, Lv2=6, Lv3=9 per turn."
        )
        self.add_header(self.econ_box, "BATTLEFIELD OPTIONS (ECONOMIC)", tooltip_text=tooltip_econ)
        
        econ_grid = GridLayout(cols=2, spacing=12)
        self.econ_cards = []
        econ_options = [
            (False, 'Standard Economy', 'Farms produce only Tax'),
            (True, 'Advanced Economy', 'Farms can produce Supplies or Wood'),
        ]
        for val, title, desc in econ_options:
            card = SelectionCard(text=f"[b][size=15sp]{title}[/size][/b]\n[size=12sp][color=a0a0a0]{desc}[/color][/size]")
            card.val = val
            card.bind(on_press=self.play_sound, on_release=self.on_econ_select)
            self.econ_cards.append(card)
            econ_grid.add_widget(card)
            
        self.econ_box.add_widget(econ_grid)
        self.page2.add_widget(self.econ_box)

        # 4. SELECT FACTIONS
        self.fac_box = BoxLayout(orientation='vertical', size_hint_y=1, spacing=5)
        self.add_header(self.fac_box, "4. CHOOSE YOUR LEGION", clickable_info=True)
        
        self.fac_split = BoxLayout(orientation='horizontal', spacing=30)
        
        legion_options = [
            ('The Knight Company', 'assets/map_card/the_knight_company.png'),
            ('The Chaos Mankind', 'assets/map_card/the_chaos_mankind.png'),
            ('The Deep Anomaly', 'assets/map_card/the_deep_anomaly.png'),
            ('The Ancient Runes', 'assets/map_card/the_ancient_runes.png')
        ]
        
        # WHITE
        self.w_box = BoxLayout(orientation='vertical', spacing=8)
        self.w_box.add_widget(Label(text="DIVINE ORDER (WHITE)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.white_cards = []
        for f_name, f_img in legion_options:
            card = IconSelectionCard(text=f"[b][size=14sp]{f_name}[/size][/b]", image_source=f_img, val=f_name)
            card.bind(on_press=self.play_sound, on_release=self.on_white_select)
            self.white_cards.append(card)
            self.w_box.add_widget(card)
            
        # BLACK
        self.b_box = BoxLayout(orientation='vertical', spacing=8)
        self.b_box.add_widget(Label(text="DARK ABYSS (BLACK)", font_size='14sp', color=(0.8, 0.8, 0.8, 1), bold=True, size_hint_y=None, height=20))
        self.black_cards = []
        for f_name, f_img in legion_options:
            card = IconSelectionCard(text=f"[b][size=14sp]{f_name}[/size][/b]", image_source=f_img, val=f_name)
            card.bind(on_press=self.play_sound, on_release=self.on_black_select)
            self.black_cards.append(card)
            self.b_box.add_widget(card)
            
        self.fac_split.add_widget(self.w_box)
        self.fac_split.add_widget(self.b_box)
        self.fac_box.add_widget(self.fac_split)
        self.page2.add_widget(self.fac_box)

        # เริ่มต้นแสดงหน้าแรก
        self.add_widget(self.page1)
        self.current_page = 1
        self.update_selections()

    def switch_page(self, page_num):
        # สลับการแสดงผลหน้าของ UI
        self.clear_widgets()
        if page_num == 1:
            self.add_widget(self.page1)
            self.current_page = 1
        elif page_num == 2:
            self.add_widget(self.page2)
            self.current_page = 2
        
        # อัปเดตปุ่มใน SetupScreen (ถ้ามีการผูกไว้)
        if hasattr(self, 'screen_ref'):
            self.screen_ref.update_buttons()

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
        for c in self.type_cards: c.set_selected(c.val == self.app.match_type) #[cite: 2]
        for c in self.mode_cards: c.set_selected(c.val == self.app.sub_mode) #[cite: 2]
        for c in getattr(self, 'map_cards', []): c.set_selected(c.val == self.app.selected_board) #[cite: 2]
        for c in self.timer_cards: c.set_selected(c.val == self.app.selected_time_limit) #[cite: 2]
        
        # ✨ เพิ่มบรรทัดนี้ให้อัปเดต UI ปุ่ม Economic
        if hasattr(self, 'econ_cards'):
            for c in self.econ_cards: c.set_selected(c.val == self.app.selected_economic_system)
            
        for c in self.white_cards: c.set_selected(c.val == self.app.selected_unit_white) #[cite: 2]
        for c in self.black_cards: c.set_selected(c.val == self.app.selected_unit_black) #[cite: 2]

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

        # จัดการการแสดงผลของ Timer และ Economic Box สำหรับหน้าที่ 2
        if instance.val == 'Divide_Conquer':
            # ปิด Timer
            self.timer_box.disabled = True
            self.timer_box.height = dp(0)
            self.timer_box.opacity = 0
            self.app.selected_time_limit = None
            
            # เปิด Economic System (จุดที่เพิ่มเข้ามา)
            self.econ_box.disabled = False
            self.econ_box.height = dp(90) # ปรับความสูงให้พอดี
            self.econ_box.opacity = 1
        else:
            # เปิด Timer
            self.timer_box.disabled = False
            self.timer_box.height = dp(90)
            self.timer_box.opacity = 1
            
            # ปิด Economic System (จุดที่เพิ่มเข้ามา)
            self.econ_box.disabled = True
            self.econ_box.height = dp(0)
            self.econ_box.opacity = 0
            self.app.selected_economic_system = False

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
            options = [
                ('Classic Board', 'assets/map_card/classic.png'),
                ('Enchanted Forest', 'assets/map_card/enchanted_forest.png'),
                ('Desert Ruins', 'assets/map_card/desert_ruins.png'),
                ('Frozen Tundra', 'assets/map_card/frozen_trundra.png'),
                ('Random Board', 'assets/map_card/random.png')
            ]
            for mp, img_src in options:
                display_name = mp.replace(" Board", "")
                card = MapSelectionCard(text=f"[b][size=15sp]{display_name}[/size][/b]", image_source=img_src, val=mp)
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
            options = [
                ('Size_S', 'SMALL WORLD\n[size=12sp](3 Farming Bases)[/size]', 'assets/map_card/dnc_small.png'),
                ('Size_M', 'MEDIUM WORLD\n[size=12sp](5 Farming Bases)[/size]', 'assets/map_card/dnc_medium.png'),
                ('Size_L', 'LARGE WORLD\n[size=12sp](7 Farming Bases)[/size]', 'assets/map_card/dnc_large.png')
            ]
            for val, display_name, img_src in options:
                card = MapSelectionCard(text=f"[b][size=16sp]{display_name}[/size][/b]", image_source=img_src, val=val)
                card.bind(on_press=self.play_sound, on_release=self.on_map_select)
                self.map_cards.append(card)
                self.map_grid.add_widget(card)

    def on_timer_select(self, instance):
        self.app.selected_time_limit = instance.val
        self.update_selections()

    def on_econ_select(self, instance):
        self.app.selected_economic_system = instance.val
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