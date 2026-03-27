# screens/campaign_map_screen.py
import random
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock

# ----------------- ฟังก์ชันตัวช่วยสำหรับคำนวณการทับซ้อน -----------------
def check_rect_overlap(r1, r2):
    # r = (x, y, w, h)
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

def is_overlapping_any(rect, rect_list):
    for r in rect_list:
        if check_rect_overlap(rect, r): return True
    return False

def get_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


class MapNode(Button):
    def __init__(self, node_type, faction, node_id, **kwargs):
        super().__init__(**kwargs)
        self.node_type = node_type # 'village' or 'castle'
        self.faction = faction     # 'white', 'black', or 'neutral'
        self.node_id = node_id
        
        # ปรับขนาดปุ่มฐานให้ใหญ่ขึ้นเล็กน้อย เพื่อให้กดง่ายในด่านใหญ่
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        self.background_color = (0, 0, 0, 0) 
        
        with self.canvas.before:
            if self.node_type == 'castle':
                self.color_inst = Color(0.5, 0.5, 0.55, 1) # ปราสาทสีเทา
                self.shape = Rectangle(pos=self.pos, size=self.size)
            else:
                self.color_inst = Color(0.85, 0.85, 0.85, 1) # หมู่บ้านสีขาว
                self.shape = Ellipse(pos=self.pos, size=self.size)
                
            # กรอบสีบอกฝ่าย (ขาว หรือ ดำ)
            fac_color = (0.9, 0.9, 0.9, 1) if faction == 'white' else (0.1, 0.1, 0.1, 1)
            Color(*fac_color)
            self.border_line = Line(circle=(self.center_x, self.center_y, dp(28)), width=3)
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size
        self.border_line.circle = (self.center_x, self.center_y, dp(28))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()
        print(f"Node Clicked: [{self.faction.upper()}] {self.node_type.upper()} (ID: {self.node_id})")
        # TODO: เปิด UI จัดทัพตรงจุดนี้ (Army Management UI)


class CampaignMapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 1. เลเยอร์แผนที่ ที่เลื่อนไปมาได้ (Scrollable)
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        # ✨ ขยายขนาดโลกเป็น 5 เท่าของ HD = 9600 x 5400
        self.map_content = FloatLayout(size_hint=(None, None), size=(9600, 5400))
        self.scroll_view.add_widget(self.map_content)
        
        # 2. เลเยอร์ UI ที่ลอยอยู่ด้านบนตลอด (ติดจอ)
        self.ui_layer = FloatLayout()
        
        self.add_widget(self.scroll_view)
        self.add_widget(self.ui_layer)
        
        # --- UI ทั่วไปด้านบน ---
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.top_bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=self._update_top_bg, size=self._update_top_bg)
            
        back_btn = Button(text="< BACK TO SETUP", size_hint_x=0.2, background_color=(0.5, 0.1, 0.1, 1), font_size='14sp', bold=True)
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - MARCHING PHASE", bold=True, color=(1, 0.8, 0.2, 1), font_size='18sp')
        top_bar.add_widget(self.status_lbl)
        self.ui_layer.add_widget(top_bar)

    def _update_top_bg(self, instance, value):
        self.top_bg.pos = instance.pos
        self.top_bg.size = instance.size

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)

    def go_back(self, instance):
        self.manager.current = 'setup'

    def generate_procedural_map(self):
        self.map_content.clear_widgets()
        self.map_content.canvas.before.clear()
        
        app = App.get_running_app()
        size_val = getattr(app, 'selected_board', 'Size_S')
        
        # ตั้งค่าจำนวนปราสาท และ หมู่บ้าน ตามขนาด (ไม่เกิน 3 ปราสาท)
        if size_val == 'Size_S': num_castles, num_villages = 1, 2
        elif size_val == 'Size_M': num_castles, num_villages = 2, 3
        elif size_val == 'Size_L': num_castles, num_villages = 3, 4
        else: num_castles, num_villages = 1, 2
        
        total_nodes = num_castles + num_villages
        
        # ✨ แผนที่ขนาด 9600 x 5400
        map_w, map_h = 9600, 5400
        
        water_rects = []
        forest_rects = []
        nodes_data = []

        with self.map_content.canvas.before:
            # พื้นดิน
            Color(0.12, 0.18, 0.12, 1)
            Rectangle(pos=(0, 0), size=(map_w, map_h))
            
            # --- 1. สุ่มสร้างแม่น้ำ/ทะเล (สีฟ้า) ---
            # เพิ่มขนาดและจำนวนบล็อกน้ำให้เหมาะกับแมพใหญ่ยักษ์
            Color(0.1, 0.4, 0.6, 0.6)
            for _ in range(150):
                for attempt in range(50):
                    w, h = random.randint(200, 700), random.randint(200, 700)
                    x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                    rect = (x, y, w, h)
                    # น้ำห้ามทับกันเองเยอะเกินไป
                    if not is_overlapping_any(rect, water_rects):
                        water_rects.append(rect)
                        Rectangle(pos=(x, y), size=(w, h))
                        break
                        
            # --- 2. สุ่มสร้างป่า (สีเขียว) ---
            Color(0.08, 0.35, 0.15, 0.7)
            for _ in range(300):
                for attempt in range(50):
                    w, h = random.randint(150, 400), random.randint(150, 400)
                    x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
                    rect = (x, y, w, h)
                    # ป่าต้องไม่ทับน้ำ
                    if not is_overlapping_any(rect, water_rects):
                        forest_rects.append(rect)
                        Rectangle(pos=(x, y), size=(w, h))
                        break

        # --- 3. สุ่มหาพิกัดวาง ปราสาท และ หมู่บ้าน ---
        def generate_nodes_for_faction(faction, count_castles, count_villages, min_x, max_x):
            faction_nodes = []
            types_to_spawn = ['castle'] * count_castles + ['village'] * count_villages
            
            for i, n_type in enumerate(types_to_spawn):
                placed = False
                for attempt in range(500): # ลองสุ่ม 500 ครั้งในด่านใหญ่
                    nx = random.randint(min_x, max_x)
                    ny = random.randint(300, map_h - 300) # เว้นขอบบนล่างให้เยอะขึ้น
                    
                    # ตรวจสอบการทับซ้อนกับน้ำ (ให้พื้นที่จุดเป็นสี่เหลี่ยมกล่อง)
                    if is_overlapping_any((nx-80, ny-80, 160, 160), water_rects):
                        continue
                    
                    # ตรวจสอบระยะห่างจากทุกโหนด (ในด่านใหญ่นี้ต้องเว้นให้กว้างๆ เช่น 200 pixel)
                    too_close = False
                    for existing in nodes_data + faction_nodes:
                        if get_distance((nx, ny), existing['pos']) < dp(200):
                            too_close = True
                            break
                    
                    if not too_close:
                        faction_nodes.append({'pos': (nx, ny), 'faction': faction, 'type': n_type, 'id': f"{faction[0].upper()}{i}"})
                        placed = True
                        break
                        
                if not placed:
                    print(f"Warning: Could not place {n_type} for {faction}")
            return faction_nodes

        # ฝั่งซ้าย (White) กินพื้นที่ตั้งแต่ 500 ถึง 4000
        w_nodes = generate_nodes_for_faction('white', num_castles, num_villages, 500, 4000)
        # ฝั่งขวา (Black) กินพื้นที่ตั้งแต่ 5600 ถึง 9100
        b_nodes = generate_nodes_for_faction('black', num_castles, num_villages, 5600, 9100)
        
        nodes_data = w_nodes + b_nodes

        # --- 4. อัลกอริทึมเชื่อมเส้นทาง (ใยแมงมุม) ---
        def create_connections(nodes):
            edges = []
            if not nodes: return edges
            
            # Minimum Spanning Tree (เชื่อมทุกเมืองเข้าด้วยกัน)
            visited = [nodes[0]]
            unvisited = nodes[1:]
            
            while unvisited:
                min_dist = float('inf')
                best_edge = None
                best_u = None
                for v in visited:
                    for u in unvisited:
                        dist = get_distance(v['pos'], u['pos'])
                        if dist < min_dist:
                            min_dist = dist
                            best_edge = (v, u)
                            best_u = u
                edges.append(best_edge)
                visited.append(best_u)
                unvisited.remove(best_u)
                
            # สุ่มเพิ่มเส้นทางพิเศษ เพื่อให้ 1 ฐานมีทางไปได้หลายทาง
            extra_edges_count = len(nodes) // 2
            for _ in range(extra_edges_count):
                u, v = random.sample(nodes, 2)
                if (u, v) not in edges and (v, u) not in edges:
                    edges.append((u, v))
            return edges

        white_edges = create_connections(w_nodes)
        black_edges = create_connections(b_nodes)
        
        # หาจุดที่ใกล้กันที่สุดระหว่าง White และ Black เพื่อทำเป็นทางเชื่อมตรงกลาง
        min_cross = float('inf')
        cross_edge = None
        for w in w_nodes:
            for b in b_nodes:
                d = get_distance(w['pos'], b['pos'])
                if d < min_cross:
                    min_cross = d
                    cross_edge = (w, b)

        # วาดเส้นทางลงบนกระดาน
        with self.map_content.canvas.before:
            Color(0.85, 0.75, 0.3, 0.8) # สีเส้นทางดิน/เหลือง
            for u, v in white_edges + black_edges:
                Line(points=[u['pos'][0], u['pos'][1], v['pos'][0], v['pos'][1]], width=4) # เพิ่มความหนาเส้น
            
            # เส้นเชื่อมตรงกลางรบกัน (หนาพิเศษ สีแดงนิดๆ)
            if cross_edge:
                Color(0.9, 0.4, 0.2, 0.9)
                Line(points=[cross_edge[0]['pos'][0], cross_edge[0]['pos'][1], 
                             cross_edge[1]['pos'][0], cross_edge[1]['pos'][1]], width=8)

        # --- 5. นำปุ่ม (Nodes) ไปวางบนจุด ---
        for data in nodes_data:
            node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'])
            # หักลบครึ่งนึงความกว้างความสูงเพื่อให้จุดศูนย์กลางปุ่มตรงกับพิกัดเส้น
            node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
            self.map_content.add_widget(node)
            
        # ✨ เลื่อนกล้องไปตรงกลาง (โซนแนวหน้า) เมื่อแผนที่เริ่มทำงาน
        self.scroll_view.scroll_x = 0.5
        self.scroll_view.scroll_y = 0.5