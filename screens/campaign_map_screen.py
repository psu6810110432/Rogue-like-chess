# screens/campaign_map_screen.py
import random
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock

class MapNode(Button):
    def __init__(self, node_type, faction, node_id, **kwargs):
        super().__init__(**kwargs)
        self.node_type = node_type # 'village' or 'castle'
        self.faction = faction     # 'white', 'black', or 'neutral'
        self.node_id = node_id
        
        self.size_hint = (None, None)
        self.size = (dp(40), dp(40))
        self.background_color = (0, 0, 0, 0) # ซ่อนปุ่มจริงเพื่อวาดกราฟิกเอง
        
        with self.canvas.before:
            if self.node_type == 'castle':
                self.color_inst = Color(0.5, 0.5, 0.5, 1) # ปราสาทสีเทา
                self.shape = Rectangle(pos=self.pos, size=self.size)
            else:
                self.color_inst = Color(0.9, 0.9, 0.9, 1) # หมู่บ้านสีขาว
                self.shape = Ellipse(pos=self.pos, size=self.size)
                
            # กรอบสีบอกฝ่าย (ขาว หรือ ดำ)
            fac_color = (1, 1, 1, 1) if faction == 'white' else (0.2, 0.2, 0.2, 1) if faction == 'black' else (0.5, 0.5, 0.5, 0)
            Color(*fac_color)
            # ✨ เปลี่ยนชื่อตัวแปรจาก self.border (ซึ่งซ้ำกับ Property เดิมของ Button) เป็น self.border_line
            self.border_line = Line(circle=(self.center_x, self.center_y, dp(22)), width=2)
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size
        # ✨ อัปเดตด้วยชื่อใหม่
        self.border_line.circle = (self.center_x, self.center_y, dp(22))

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'):
            app.play_click_sound()
        print(f"Node Clicked: {self.faction} {self.node_type} (ID: {self.node_id})")
        # TODO: เปิดหน้าต่างจัดทัพ หรือสั่งเข้าตีที่นี่

class CampaignMapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.map_layer = FloatLayout()
        self.ui_layer = FloatLayout()
        
        self.add_widget(self.map_layer)
        self.add_widget(self.ui_layer)
        
        # UI ชั่วคราว
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0, 0, 0, 0.7)
            Rectangle(pos=top_bar.pos, size=top_bar.size)
            
        back_btn = Button(text="< BACK TO MENU", size_hint_x=0.2, background_color=(0.5, 0.1, 0.1, 1))
        back_btn.bind(on_release=self.go_back)
        top_bar.add_widget(back_btn)
        
        self.status_lbl = Label(text="DIVINE ORDER (WHITE) - MARCHING PHASE", bold=True, color=(1, 0.8, 0.2, 1))
        top_bar.add_widget(self.status_lbl)
        self.ui_layer.add_widget(top_bar)

    def on_enter(self):
        # หน่วงเวลาเล็กน้อยเพื่อให้หน้าจอโหลดขนาดเสร็จก่อนวาด
        Clock.schedule_once(lambda dt: self.generate_procedural_map(), 0.1)

    def go_back(self, instance):
        self.manager.current = 'setup'

    def generate_procedural_map(self):
        self.map_layer.clear_widgets()
        self.map_layer.canvas.before.clear()
        
        app = App.get_running_app()
        size_val = getattr(app, 'selected_board', 'Size_S')
        
        # จำนวนฟาร์ม/ฐาน ต่อฝ่าย
        if size_val == 'Size_S': num_nodes = 3
        elif size_val == 'Size_M': num_nodes = 5
        elif size_val == 'Size_L': num_nodes = 7
        else: num_nodes = 3
        
        w_width, w_height = self.width, self.height
        
        with self.map_layer.canvas.before:
            # พื้นหลังหญ้า/ดินสีเข้ม
            Color(0.1, 0.15, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # สุ่มวาดแม่น้ำ/ทะเล (บล็อกสีฟ้า)
            for _ in range(num_nodes * 2):
                Color(0.1, 0.4, 0.6, 0.5) 
                Rectangle(pos=(random.randint(0, int(w_width)), random.randint(0, int(w_height))), 
                          size=(random.randint(dp(80), dp(150)), random.randint(dp(80), dp(150))))
                
            # สุ่มวาดป่า (บล็อกสีเขียว)
            for _ in range(num_nodes * 3):
                Color(0.1, 0.5, 0.2, 0.5) 
                Rectangle(pos=(random.randint(0, int(w_width)), random.randint(0, int(w_height))), 
                          size=(random.randint(dp(60), dp(120)), random.randint(dp(60), dp(120))))

        nodes_data = []
        
        # สุ่มจุดให้ฝ่าย White (ฝั่งซ้ายของจอ x=10% ถึง 45%)
        for i in range(num_nodes):
            x = random.randint(int(w_width * 0.1), int(w_width * 0.45))
            y = random.randint(int(w_height * 0.15), int(w_height * 0.85))
            node_type = 'castle' if i == 0 else 'village' # ให้ตัวแรกของฝ่ายเป็นปราสาท
            nodes_data.append({'pos': (x, y), 'faction': 'white', 'type': node_type, 'id': f"W{i}"})

        # สุ่มจุดให้ฝ่าย Black (ฝั่งขวาของจอ x=55% ถึง 90%)
        for i in range(num_nodes):
            x = random.randint(int(w_width * 0.55), int(w_width * 0.9))
            y = random.randint(int(w_height * 0.15), int(w_height * 0.85))
            node_type = 'castle' if i == 0 else 'village'
            nodes_data.append({'pos': (x, y), 'faction': 'black', 'type': node_type, 'id': f"B{i}"})

        # วาดเส้นทาง (สีเหลือง) เชื่อมต่อจุดต่างๆ
        with self.map_layer.canvas.before:
            Color(0.8, 0.8, 0.2, 0.7) # สีเหลือง
            # เชื่อมแบบง่ายๆ : ตัวที่ i เชื่อมกับตัวที่ i+1 ภายในฝ่ายเดียวกัน
            for i in range(num_nodes - 1):
                w_start = nodes_data[i]['pos']
                w_end = nodes_data[i+1]['pos']
                Line(points=[w_start[0], w_start[1], w_end[0], w_end[1]], width=2)
                
                b_start = nodes_data[num_nodes + i]['pos']
                b_end = nodes_data[num_nodes + i + 1]['pos']
                Line(points=[b_start[0], b_start[1], b_end[0], b_end[1]], width=2)
                
            # เชื่อมข้ามฝั่งตรงกลางเพื่อให้รบกันได้
            mid_w = nodes_data[num_nodes - 1]['pos']
            mid_b = nodes_data[num_nodes]['pos']
            Line(points=[mid_w[0], mid_w[1], mid_b[0], mid_b[1]], width=3) # เส้นทางหลักที่ต้องปะทะ

        # สร้างปุ่มลงบนจอ
        for data in nodes_data:
            node = MapNode(node_type=data['type'], faction=data['faction'], node_id=data['id'])
            # จัดให้อยู่ตรงกลางพิกัด
            node.pos = (data['pos'][0] - node.width/2, data['pos'][1] - node.height/2)
            self.map_layer.add_widget(node)