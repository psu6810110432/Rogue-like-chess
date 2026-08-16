# components/board_3d_macro.py
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext, Mesh, PushMatrix, PopMatrix, InstructionGroup, Translate, Rotate
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
import math
import random
import os

# ==========================================
# 1. ระบบ Perlin Noise สำหรับสุ่มภูมิประเทศ
# ==========================================
class SimpleNoise:
    def __init__(self, seed=None):
        if seed: random.seed(seed)
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p += self.p

    def fade(self, t): return t * t * t * (t * (t * 6 - 15) + 10)
    def lerp(self, t, a, b): return a + t * (b - a)
    def grad(self, hash, x, y):
        h = hash & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else 0)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def noise2d(self, x, y):
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        x -= math.floor(x)
        y -= math.floor(y)
        u = self.fade(x)
        v = self.fade(y)
        A = self.p[X] + Y
        B = self.p[X + 1] + Y
        # ให้ค่าผลลัพธ์อยู่ในช่วง 0.0 ถึง 1.0 (โดยประมาณ)
        res = self.lerp(v, self.lerp(u, self.grad(self.p[A], x, y), self.grad(self.p[B], x, y)),
                       self.lerp(u, self.grad(self.p[A + 1], x - 1, y), self.grad(self.p[B + 1], x - 1, y)))
        return (res + 1.0) / 2.0

# ==========================================
# 2. คลาสกระดาน Macro Map 3D
# ==========================================
class MacroBoard3D(Widget):
    def __init__(self, map_size=(16, 16), seed=None, **kwargs):
        super().__init__(**kwargs)
        self.canvas = RenderContext(compute_normal_mat=True)
        
        # ใช้ Shader พื้นฐานเหมือนของเดิม
        shader_path = os.path.join(os.path.dirname(__file__), '..', 'simple3d.glsl')
        try:
            with open(shader_path, 'r', encoding='utf-8') as f:
                shader_content = f.read()
            parts = shader_content.split('---FRAGMENT SHADER---')
            self.canvas.shader.vs = parts[0].replace('---VERTEX SHADER---', '').strip()
            self.canvas.shader.fs = parts[1].strip()
        except Exception as e:
            print(f"Error loading shader: {e}")
            
        self.proj_mat = Matrix()
        self.model_mat = Matrix()
        self.camera_mat = Matrix()
        
        self.rot_x = math.radians(35) 
        self.rot_y = math.radians(45) 
        self.cam_dist = 20.0 # ซูมออกกว้างกว่ากระดานปกติ
        
        self.map_size = map_size
        self.seed = seed if seed else random.randint(1, 9999)
        self.touch_start = None

        with self.canvas:
            PushMatrix()
            self.terrain_group = InstructionGroup()
            self.generate_terrain()
            self.canvas.add(self.terrain_group)
            PopMatrix()
            
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def generate_terrain(self):
        self.terrain_group.clear()
        noise_gen = SimpleNoise(self.seed)
        
        rows, cols = self.map_size
        offset_x = cols / 2.0
        offset_z = rows / 2.0
        
        # สเกลของ Noise (ค่ายิ่งน้อย แผนที่ยิ่งสมูทและเนินเขาใหญ่ขึ้น)
        scale = 0.15 
        
        vertices = []
        indices = []
        
        # ฟังก์ชันย่อยสำหรับคำนวณความสูงและสีของแต่ละ "จุดยอด (Vertex)"
        def get_terrain_data(c, r):
            elevation = noise_gen.noise2d(c * scale, r * scale)
            moisture = noise_gen.noise2d(c * scale + 100, r * scale + 100)
            
            height = 0.0
            color = (1, 1, 1, 1)
            
            if elevation < 0.35:
                # แม่น้ำ/ทะเลสาบ (บังคับความสูงให้เท่ากันหมด น้ำจะได้ดูเรียบแบน)
                color = (0.2, 0.5, 0.8, 1) # สีฟ้า
                height = 0.2
            elif elevation > 0.75:
                # หิมะยอดเขา 
                color = (0.85, 0.85, 0.9, 1) # ขาวอมเทา
                height = elevation * 3.5
            elif elevation > 0.6:
                # ภูเขา 
                color = (0.5, 0.5, 0.5, 1) # สีเทา
                height = elevation * 3.0
            else:
                # ที่ราบ
                height = elevation * 1.5 + 0.2
                if moisture > 0.5:
                    color = (0.1, 0.4, 0.1, 1) # ป่า (สีเขียวเข้ม)
                else:
                    color = (0.76, 0.7, 0.5, 1) # ทะเลทราย (สีเหลืองมน)
                    
            return height, color

        # ===================================================
        # 1. สร้างจุดยอด (Vertices) ของตาข่ายทั้งหมด
        # ===================================================
        # เราบวก 1 เข้าไปเพราะตารางขนาด 16x16 ช่อง จะต้องใช้จุดมุม 17x17 จุด
        for r in range(rows + 1):
            for c in range(cols + 1):
                y, color = get_terrain_data(c, r)
                
                # --- ลูกเล่นพิเศษ: ดัดให้ขอบแมพจมน้ำกลายเป็นเกาะ ---
                # dist_to_center = math.sqrt((c - offset_x)**2 + (r - offset_z)**2)
                # max_dist = min(offset_x, offset_z)
                # if dist_to_center > max_dist * 0.9:
                #     y = 0.2
                #     color = (0.2, 0.5, 0.8, 1)
                # ----------------------------------------------
                
                x = c - offset_x
                z = r - offset_z
                
                # โครงสร้าง: x, y, z, r, g, b, a, u, v
                vertices.extend([x, y, z, *color, -1.0, -1.0])

        # ===================================================
        # 2. ถักทอจุดยอดให้กลายเป็นตาข่ายสามเหลี่ยม (Triangles)
        # ===================================================
        for r in range(rows):
            for c in range(cols):
                # หาเลข Index ของมุมทั้ง 4 ใน 1 ช่องสี่เหลี่ยม
                p0 = r * (cols + 1) + c
                p1 = p0 + 1
                p2 = (r + 1) * (cols + 1) + c
                p3 = p2 + 1
                
                # ถักสามเหลี่ยม 2 รูป เพื่อประกอบเป็น 1 ช่องตาราง
                indices.extend([p0, p2, p1, p1, p2, p3])

        # ===================================================
        # 3. วาด Mesh แผ่นดินขึ้นมาผืนเดียวจบ (ประหยัดสเปคเครื่องมาก)
        # ===================================================
        fmt = [(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')]
        self.terrain_group.add(Mesh(fmt=fmt, mode='triangles', vertices=vertices, indices=indices))

    # ระบบกล้องใช้พื้นฐานเดียวกับ Board3D Classic
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return super().on_touch_down(touch)

        if touch.button == 'scrollup':
            self.cam_dist = min(40.0, self.cam_dist + 1.0)
            return True
        elif touch.button == 'scrolldown':
            self.cam_dist = max(10.0, self.cam_dist - 1.0)
            return True

        if touch.button == 'right':
            touch.grab(self)
            self.touch_start = touch.pos
            return True
        
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.touch_start:
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            
            self.rot_y -= dx * 0.005 
            self.rot_x -= dy * 0.005 
            self.rot_x = max(0.1, min(math.pi / 2.2, self.rot_x))
            self.touch_start = touch.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touch_start = None
            return True
        return super().on_touch_up(touch)

    def update_glsl(self, dt):
        aspect_ratio = float(self.width) / float(self.height) if self.height else 1.0
        self.proj_mat.view_clip(-aspect_ratio, aspect_ratio, -1, 1, 1, 200, 1)
        
        cam_y = self.cam_dist * math.sin(self.rot_x)
        cam_x = self.cam_dist * math.cos(self.rot_x) * math.sin(self.rot_y)
        cam_z = self.cam_dist * math.cos(self.rot_x) * math.cos(self.rot_y)
        self.camera_mat = Matrix().look_at(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
        self.canvas['projection_mat'] = self.proj_mat
        self.canvas['modelview_mat'] = self.camera_mat.multiply(self.model_mat)
        self.canvas['texture0'] = 0