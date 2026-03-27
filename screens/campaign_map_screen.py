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

# ----------------- ฟังก์ชันตัวช่วย -----------------
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


# ----------------- UI หน้าต่างจัดการกองทัพ -----------------
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
        
        # ปิดปุ่มลบ (ไม่ให้ขายทหารทิ้งเพื่อเอาเงินคืน) ให้จัดทัพหรือซื้อเพิ่มได้อย่างเดียว
        self.lbl_count = Label(text=f"[b]{self.count}[/b]", markup=True, size_hint_x=0.3, font_size='18sp')
        self.add_widget(self.lbl_count)
        
        self.btn_plus = Button(text="[b]+[/b]", markup=True, size_hint_x=0.2, background_color=(0.2, 0.8, 0.2, 1))
        self.btn_plus.disabled = not can_recruit
        self.btn_plus.bind(on_release=self.increase)
        self.add_widget(self.btn_plus)

    def increase(self, instance):
        # ส่งเรื่องไปให้ Popup จัดการหักเงินและเช็คลิมิต
        success = self.update_cb(self.piece_name, self.count + 1, self.cost)
        if success:
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

        # --- Header ---
        header_box = BoxLayout(size_hint_y=0.1)
        title = f"ARMY HQ - {node.node_type.upper()} ({node.faction.upper()})"
        header_box.add_widget(Label(text=f"[b][color=d4af37]{title}[/color][/b]", markup=True, font_size='22sp'))
        
        # แสดง Tax Points ปัจจุบันของฝ่ายนั้น
        self.lbl_tax = Label(text="", markup=True, font_size='18sp')
        header_box.add_widget(self.lbl_tax)
        root.add_widget(header_box)

        # --- Content ---
        content_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=0.75)
        
        # ซ้าย: จัดการทหาร
        left_panel = ScrollView(size_hint_x=0.6)
        self.counter_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.counter_grid.bind(minimum_height=self.counter_grid.setter('height'))
        left_panel.add_widget(self.counter_grid)
        content_box.add_widget(left_panel)

        # ขวา: Status & Quick Recruit
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=dp(10))
        with right_panel.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rp_bg = RoundedRectangle(radius=[dp(10)])
        right_panel.bind(pos=lambda i,v: setattr(self.rp_bg, 'pos', i.pos), size=lambda i,v: setattr(self.rp_bg, 'size', i.size))
        
        self.lbl_stats = Label(text="", markup=True, size_hint_y=0.5, font_size='15sp', halign='left', valign='top')
        self.lbl_stats.bind(size=self.lbl_stats.setter('text_size'))
        right_panel.add_widget(self.lbl_stats)

        # ปุ่ม Quick Recruit
        self.btn_quick = Button(text="[b]QUICK RECRUIT (7 TAX)[/b]\n[size=12sp]Restore Classic Army[/size]", markup=True, size_hint_y=0.2, background_color=(0.8, 0.6, 0.1, 1))
        self.btn_quick.bind(on_release=self.quick_recruit)
        right_panel.add_widget(self.btn_quick)
        
        content_box.add_widget(right_panel)
        root.add_widget(content_box)

        # --- Footer ---
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
        
        categories = {
            'HEADER': [('king', 0), ('prince', 0)], # ไม่ให้ซื้อ Header โดยตรง
            'HEAVY (Cost: 2)': [('queen', 2), ('rook', 2), ('bishop', 2), ('knight', 2)],
            'LIGHT (Cost: 1)': [('pawn', 1)]
        }
        
        # กฎ: หมู่บ้านรับได้แค่ Light, ปราสาทรับได้ทั้งหมด
        can_heavy = (self.node.node_type == 'castle')
        
        for cat_name, pieces in categories.items():
            self.counter_grid.add_widget(Label(text=f"[color=aaddff][b]--- {cat_name} ---[/b][/color]", markup=True, size_hint_y=None, height=dp(30), halign='left'))
            for p, cost in pieces:
                num = {'pawn':6, 'rook':3, 'knight':4, 'bishop':5, 'queen':2, 'king':1}.get(p, 1)
                img_path = f"assets/pieces/{tribe}/{self.node.faction}/chess {tribe}{num}.png"
                if p == 'prince': img_path = f"assets/pieces/{tribe}/{self.node.faction}/chess {tribe}1.png"
                
                allow_recruit = True
                if cost == 0: allow_recruit = False # Header ซื้อไม่ได้
                if not can_heavy and cost == 2: allow_recruit = False # หมู่บ้านซื้อ Heavy ไม่ได้
                
                counter = UnitCounter(p, self.temp_army.get(p, 0), self.on_recruit_attempt, img_path, cost=cost, can_recruit=allow_recruit)
                self.counter_grid.add_widget(counter)

    def on_recruit_attempt(self, piece_name, new_count, cost):
        tax = self.app.tax_points[self.node.faction]
        if tax < cost: return False # เงินไม่พอ
        
        headers = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
        heavies = sum([self.temp_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        lights = self.temp_army.get('pawn', 0)
        total = headers + heavies + lights
        max_cap = 18 if headers > 0 else 8
        
        if total >= max_cap: return False # ทัพเต็ม
        
        # กฎ: ถ้า Heavy > 9 ห้ามเกณฑ์ Light (Pawn)
        if piece_name == 'pawn' and heavies > 9:
            return False 

        # หักเงินและเพิ่มทหาร
        self.app.tax_points[self.node.faction] -= cost
        self.temp_army[piece_name] = new_count
        self.update_summary()
        return True

    def quick_recruit(self, instance):
        tax = self.app.tax_points[self.node.faction]
        if tax < 7: return
        
        target = {'queen': 1, 'rook': 2, 'bishop': 2, 'knight': 2, 'pawn': 8}
        heavies = sum([self.temp_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        
        # ลดเงินก่อน
        self.app.tax_points[self.node.faction] -= 7
        
        for p, target_count in target.items():
            while self.temp_army.get(p, 0) < target_count:
                headers = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
                curr_heavies = sum([self.temp_army.get(h, 0) for h in ['queen', 'rook', 'bishop', 'knight']])
                total = headers + curr_heavies + self.temp_army.get('pawn', 0)
                max_cap = 18 if headers > 0 else 8
                
                if total >= max_cap: break
                
                # ถ้ากำลังจะเติม Heavy แต่ Heavy เกิน 9 แล้ว ให้เติม Pawn แทน
                if p in ['queen', 'rook', 'bishop', 'knight'] and curr_heavies >= 9:
                    self.temp_army['pawn'] += 1
                else:
                    self.temp_army[p] += 1

        self.build_recruit_ui() # รีเฟรช UI
        self.update_summary()
        self.app.play_click_sound()

    def update_summary(self):
        tax = self.app.tax_points[self.node.faction]
        self.lbl_tax.text = f"TAX POINTS: [color=00ff00]{tax}[/color]"
        
        light_count = self.temp_army.get('pawn', 0)
        heavy_count = sum([self.temp_army.get(p, 0) for p in ['queen', 'rook', 'bishop', 'knight']])
        header_count = self.temp_army.get('king', 0) + self.temp_army.get('prince', 0)
        total = light_count + heavy_count + header_count
        max_cap = 18 if header_count > 0 else 8

        stats = (
            f"Capacity: [b]{total} / {max_cap}[/b]\n"
            f"Headers: [color=ffcc00]{header_count}[/color]\n"
            f"Heavy (Max 9 for Light): [color=ff6666]{heavy_count}[/color]\n"
            f"Light (Pawn): [color=66ff66]{light_count}[/color]\n\n"
            f"[b][color=aaaaaa]ARMY EFFECTS:[/color][/b]\n"
        )
        
        if light_count > 12: stats += "[color=00ff00]✔ Swift March (2 Hexes)[/color]\n"
        if heavy_count > 9: stats += "[color=ff0000]✖ Elitism (Cannot recruit Light)[/color]\n"
        
        self.lbl_stats.text = stats

    def confirm_save(self, instance):
        self.node.army = self.temp_army.copy()
        self.app.play_click_sound()
        self.dismiss()


# ----------------- คลาส MapNode -----------------
class MapNode(Button):
    def __init__(self, node_type, faction, node_id, is_main_base=False, **kwargs):
        super().__init__(**kwargs)
        self.node_type = node_type 
        self.faction = faction     # 'white', 'black', or 'red' (Neutral)
        self.node_id = node_id
        self.is_main_base = is_main_base # True เฉพาะปราสาทเริ่มต้น
        
        # จัดทัพเริ่มต้น
        if self.is_main_base:
            self.army = {'king': 1, 'queen': 1, 'rook': 2, 'bishop': 2, 'knight': 2, 'pawn': 8, 'prince': 0}
        else:
            self.army = {'king': 0, 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0, 'prince': 0}
        
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        self.background_color = (0, 0, 0, 0) 
        
        with self.canvas.before:
            # ✨ สร้างออร่าสีเหลืองถ้าเป็นปราสาทหลัก
            if self.is_main_base:
                Color(1, 0.8, 0, 0.4)
                self.aura = Ellipse(pos=(self.x - dp(10), self.y - dp(10)), size=(self.width + dp(20), self.height + dp(20)))
            else:
                self.aura = None

            if self.node_type == 'castle':
                self.color_inst = Color(0.5, 0.5, 0.55, 1)
                self.shape = Rectangle(pos=self.pos, size=self.size)
            else:
                self.color_inst = Color(0.85, 0.85, 0.85, 1)
                self.shape = Ellipse(pos=self.pos, size=self.size)
                
            # สีฝ่าย (White, Black, Red)
            if faction == 'white': fac_color = (0.9, 0.9, 0.9, 1)
            elif faction == 'black': fac_color = (0.1, 0.1, 0.1, 1)
            else: fac_color = (0.8, 0.2, 0.2, 1) # Red Neutral
            
            Color(*fac_color)
            self.border_line = Line(circle=(self.center_x, self.center_y, dp(28)), width=3)
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size
        self.border_line.circle = (self.center_x, self.center_y, dp(28))
        if self.aura:
            self.aura.pos = (self.x - dp(10), self.y - dp(10))
            self.aura.size = (self.width + dp(20), self.height + dp(20))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        
        current_turn = getattr(app, 'current_map_turn', 'white')
        
        # ตรวจสอบความเป็นเจ้าของ
        if self.faction == current_turn:
            ArmyManagementPopup(node=self, app=app).open()
        else:
            print(f"Cannot manage enemy/neutral territory! This is {self.faction.upper()}.")
            # TODO: สร้าง Popup สำหรับสั่งโจมตี (State 2)


# ----------------- คลาสหลัก CampaignMapScreen -----------------
class CampaignMapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.map_content = FloatLayout(size_hint=(None, None), size=(9600, 5400))
        self.scroll_view.add_widget(self.map_content)
        self.ui_layer = FloatLayout()
        
        self.add_widget(self.scroll_view)
        self.add_widget(self.ui_layer)
        
        # --- UI ทั่วไปด้านบน ---
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.top_bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=self._update_top_bg, size=self._update_top_bg)
            
        back_btn = Button(text="< SETUP", size_hint_x=0.1, background_color=(0.5, 0.1, 0.1, 1))
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - TURN 1", bold=True, color=(1, 0.8, 0.2, 1), font_size='18sp')
        top_bar.add_widget(self.status_lbl)
        
        # ✨ ปุ่ม Next Turn สำหรับเก็บภาษี
        next_btn = Button(text="END TURN >", size_hint_x=0.15, background_color=(0.2, 0.6, 0.2, 1))
        next_btn.bind(on_release=self.end_turn)
        top_bar.add_widget(next_btn)
        
        self.ui_layer.add_widget(top_bar)
        
        # ตัวแปรสถานะเกมแคมเปญ
        self.nodes_list = []

    def _update_top_bg(self, instance, value):
        self.top_bg.pos = instance.pos
        self.top_bg.size = instance.size

    def on_enter(self):
        app = App.get_running_app()
        app.current_map_turn = 'white'
        app.turn_number = 1
        # เริ่มต้นที่ 0 แต้ม ค่อยกด End Turn เก็บภาษี
        app.tax_points = {'white': 0, 'black': 0} 
        
        Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)

    def go_back(self, instance):
        self.manager.current = 'setup'

    def end_turn(self, instance):
        app = App.get_running_app()
        app.play_click_sound()
        
        # จบเทิร์น เก็บภาษีให้ฝั่งปัจจุบัน
        tax_collected = 0
        for node in self.nodes_list:
            if node.faction == app.current_map_turn:
                if node.node_type == 'village': tax_collected += 3
                elif node.node_type == 'castle': tax_collected += 6
                
        app.tax_points[app.current_map_turn] += tax_collected
        print(f"{app.current_map_turn.upper()} collected {tax_collected} Tax Points.")
        
        # สลับฝั่ง
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
        
        if size_val == 'Size_S': num_castles, num_villages = 1, 2
        elif size_val == 'Size_M': num_castles, num_villages = 2, 3
        elif size_val == 'Size_L': num_castles, num_villages = 3, 4
        else: num_castles, num_villages = 1, 2
        
        total_nodes = num_castles + num_villages
        map_w, map_h = 9600, 5400
        water_rects, forest_rects, nodes_data = [], [], []

        with self.map_content.canvas.before:
            Color(0.12, 0.18, 0.12, 1)
            Rectangle(pos=(0, 0), size=(map_w, map_h))
            
            Color(0.1, 0.4, 0.6, 0.6)
            for _ in range(150):
                for attempt in range(50):
                    w, h = random.randint(200, 700), random.randint(200, 700)
                    x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                    rect = (x, y, w, h)
                    if not is_overlapping_any(rect, water_rects):
                        water_rects.append(rect)
                        Rectangle(pos=(x, y), size=(w, h))
                        break
                        
            Color(0.08, 0.35, 0.15, 0.7)
            for _ in range(300):
                for attempt in range(50):
                    w, h = random.randint(150, 400), random.randint(150, 400)
                    x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                    rect = (x, y, w, h)
                    if not is_overlapping_any(rect, water_rects):
                        forest_rects.append(rect)
                        Rectangle(pos=(x, y), size=(w, h))
                        break

        def generate_nodes_for_faction(base_faction, count_castles, count_villages, min_x, max_x):
            faction_nodes = []
            types_to_spawn = ['castle'] * count_castles + ['village'] * count_villages
            
            for i, n_type in enumerate(types_to_spawn):
                placed = False
                for attempt in range(500):
                    nx = random.randint(min_x, max_x)
                    ny = random.randint(300, map_h - 300)
                    
                    if is_overlapping_any((nx-80, ny-80, 160, 160), water_rects): continue
                    
                    too_close = False
                    for existing in nodes_data + faction_nodes:
                        if get_distance((nx, ny), existing['pos']) < dp(200):
                            too_close = True
                            break
                    
                    if not too_close:
                        # ✨ ปราสาทแรกเป็นของสีนั้น (is_main_base=True) ส่วนที่เหลือเป็น Red (Neutral)
                        is_main = (i == 0)
                        actual_faction = base_faction if is_main else 'red'
                        faction_nodes.append({'pos': (nx, ny), 'faction': actual_faction, 'type': n_type, 'id': f"{base_faction[0].upper()}{i}", 'main': is_main})
                        placed = True
                        break
            return faction_nodes

        w_nodes = generate_nodes_for_faction('white', num_castles, num_villages, 500, 4000)
        b_nodes = generate_nodes_for_faction('black', num_castles, num_villages, 5600, 9100)
        nodes_data = w_nodes + b_nodes

        def create_connections(nodes):
            edges = []
            if not nodes: return edges
            visited = [nodes[0]]
            unvisited = nodes[1:]
            
            while unvisited:
                min_dist, best_edge, best_u = float('inf'), None, None
                for v in visited:
                    for u in unvisited:
                        dist = get_distance(v['pos'], u['pos'])
                        if dist < min_dist:
                            min_dist, best_edge, best_u = dist, (v, u), u
                edges.append(best_edge)
                visited.append(best_u)
                unvisited.remove(best_u)
                
            extra_edges_count = len(nodes) // 2
            for _ in range(extra_edges_count):
                u, v = random.sample(nodes, 2)
                if (u, v) not in edges and (v, u) not in edges:
                    edges.append((u, v))
            return edges

        white_edges = create_connections(w_nodes)
        black_edges = create_connections(b_nodes)
        
        min_cross, cross_edge = float('inf'), None
        for w in w_nodes:
            for b in b_nodes:
                d = get_distance(w['pos'], b['pos'])
                if d < min_cross:
                    min_cross, cross_edge = d, (w, b)

        with self.map_content.canvas.before:
            Color(0.85, 0.75, 0.3, 0.8)
            for u, v in white_edges + black_edges:
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4)
            
            if cross_edge:
                Color(0.9, 0.4, 0.2, 0.9)
                Line(points=[cross_edge[0]['pos'][0], cross_edge[0]['pos'][1], 
                             cross_edge[1]['pos'][0], cross_edge[1]['pos'][1]], width=8)

        for data in nodes_data:
            node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'], is_main_base=data['main'])
            node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
            self.map_content.add_widget(node)
            self.nodes_list.append(node)
            
        self.scroll_view.scroll_x = 0.5
        self.scroll_view.scroll_y = 0.5