# components/board_3d_macro.py
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext, Mesh, PushMatrix, PopMatrix, InstructionGroup, Translate, Rotate
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.graphics import RenderContext, Mesh, PushMatrix, PopMatrix, InstructionGroup, Translate, Rotate, ClearBuffers
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
        self.canvas['DEPTH_TEST'] = 1 # ✨ 1. เปิดระบบคำนวณความลึกหน้า/หลัง
        
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
        self.cam_dist = 40.0 # ✨ ปรับซูมเริ่มต้นให้กว้างขึ้น
        
        self.map_size = map_size
        self.seed = seed if seed else random.randint(1, 9999)
        self.touch_start = None

        with self.canvas:
            ClearBuffers(clear_depth=True) # ✨ 2. ล้างระยะความลึกใหม่ทุกเฟรม
            PushMatrix()
            self.terrain_group = InstructionGroup()
            self.generate_terrain()
            self.canvas.add(self.terrain_group)
            PopMatrix()
            
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def generate_terrain(self):
        self.terrain_group.clear()
        noise_gen = SimpleNoise(self.seed)

        padding = 40
        base_rows, base_cols = self.map_size
        rows = base_rows + (padding * 2)
        cols = base_cols + (padding * 2)

        offset_x = cols / 2.0
        offset_z = rows / 2.0
        
        # สเกลของ Noise (ค่ายิ่งน้อย แผนที่ยิ่งสมูทและเนินเขาใหญ่ขึ้น)
        scale = 0.15 
        
        vertices = []
        indices = []
        
    def generate_terrain(self):
        self.terrain_group.clear()
        noise_gen = SimpleNoise(self.seed)

        padding = 40
        base_rows, base_cols = self.map_size
        rows = base_rows + (padding * 2)
        cols = base_cols + (padding * 2)
        
        offset_x = cols / 2.0
        offset_z = rows / 2.0
        
        scale = 0.15 
        temp_scale = scale * 0.4
        
        # ===================================================
        # 1. กำหนดจุดศูนย์กลาง (Centers)
        # ===================================================
        random.seed(self.seed)
        
        total_area = rows * cols
        r_snow = math.sqrt((0.18 * total_area) / (2 * math.pi))
        r_desert = math.sqrt((0.18 * total_area) / (3 * math.pi))
        
        safe_distance = r_snow + r_desert + 15.0 
        
        snow_centers = [(random.uniform(40, cols - 40), random.uniform(40, rows - 40)) for _ in range(2)]
        
        desert_centers = []
        for _ in range(3):
            for _ in range(100):
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                margin = 35 
                if edge == 'top':
                    pt = (random.uniform(0, cols), random.uniform(rows - margin, rows))
                elif edge == 'bottom':
                    pt = (random.uniform(0, cols), random.uniform(0, margin))
                elif edge == 'left':
                    pt = (random.uniform(0, margin), random.uniform(0, rows))
                else: 
                    pt = (random.uniform(cols - margin, cols), random.uniform(0, rows))
                    
                if all(math.hypot(pt[0] - sx, pt[1] - sy) > safe_distance for sx, sy in snow_centers):
                    desert_centers.append(pt)
                    break
            else:
                desert_centers.append(pt)

        # ===================================================
        # 2. สร้าง 2D Array เก็บค่าดิบล่วงหน้า (Pre-calculation)
        # ===================================================
        raw_data = [[{} for _ in range(cols + 1)] for _ in range(rows + 1)]
        for r in range(rows + 1):
            for c in range(cols + 1):
                s_dist = min([math.hypot(c - cx, r - cy) for cx, cy in snow_centers])
                d_dist = min([math.hypot(c - cx, r - cy) for cx, cy in desert_centers])
                shape_noise = (noise_gen.noise2d(c * 0.2, r * 0.2) - 0.5) * 20.0 
                
                raw_data[r][c] = {
                    'e': noise_gen.noise2d(c * scale, r * scale) + 0.15,
                    's': s_dist + shape_noise, 
                    'd': d_dist + shape_noise, 
                    'r': noise_gen.noise2d(c * temp_scale + 200, r * temp_scale + 200)
                }

        # ===================================================
        # 3. ระบบ Neighbor Smoothing 8 ทิศ
        # ===================================================
        smooth_data = [[{} for _ in range(cols + 1)] for _ in range(rows + 1)]
        for r in range(rows + 1):
            for c in range(cols + 1):
                sum_e, sum_s, sum_d, sum_r, count = 0, 0, 0, 0, 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr <= rows and 0 <= nc <= cols:
                            sum_e += raw_data[nr][nc]['e']
                            sum_s += raw_data[nr][nc]['s']
                            sum_d += raw_data[nr][nc]['d']
                            sum_r += raw_data[nr][nc]['r']
                            count += 1
                            
                smooth_data[r][c] = {
                    'e': sum_e / count,
                    's': sum_s / count,
                    'd': sum_d / count,
                    'r': sum_r / count
                }

        # ===================================================
        # 4. กำหนดสี (Smooth Blending)
        # ===================================================
        def get_terrain_data(c, r):
            data = smooth_data[r][c]
            elevation = data['e']
            s_val = data['s']
            d_val = data['d']
            river_dist = abs(data['r'] - 0.5)
            
            c_snow = (0.85, 0.85, 0.9, 1)
            c_desert = (0.76, 0.7, 0.5, 1)
            c_water = (0.2, 0.5, 0.8, 1)
            
            c_forest_base = (0.35, 0.55, 0.3, 1)     
            c_forest_warm = (0.45, 0.55, 0.2, 1)     
            c_forest_cool = (0.25, 0.55, 0.4, 1)     
            
            inf_radius = 12.0
            base_grass_color = list(c_forest_base)
            
            if s_val < r_snow + inf_radius:
                t_inf = max(0, min(1, (r_snow + inf_radius - s_val) / inf_radius))
                base_grass_color = [c_forest_base[i] + (c_forest_cool[i] - c_forest_base[i]) * t_inf for i in range(4)]
            elif d_val < r_desert + inf_radius:
                t_inf = max(0, min(1, (r_desert + inf_radius - d_val) / inf_radius))
                base_grass_color = [c_forest_base[i] + (c_forest_warm[i] - c_forest_base[i]) * t_inf for i in range(4)]

            color = [1, 1, 1, 1]
            height = elevation * 1.5 + 0.2
            
            if s_val < r_snow:
                t = max(0, min(1, (r_snow - s_val) / 5.0))
                color = [base_grass_color[i] + (c_snow[i] - base_grass_color[i]) * t for i in range(4)]
            elif d_val < r_desert:
                t = max(0, min(1, (r_desert - d_val) / 5.0))
                color = [base_grass_color[i] + (c_desert[i] - base_grass_color[i]) * t for i in range(4)]
            else:
                color = list(base_grass_color)
                
            if river_dist < 0.015:
                color = list(c_water)
                height = 0.2
            elif river_dist < 0.035:
                t = max(0, min(1, (river_dist - 0.015) / 0.02))
                color = [c_water[i] + (color[i] - c_water[i]) * t for i in range(4)]
                height = 0.2 + (height - 0.2) * t
                
            if elevation < 0.12:
                color = list(c_water)
                height = 0.2
            elif elevation < 0.18:
                t = max(0, min(1, (elevation - 0.12) / 0.06))
                color = [c_water[i] + (color[i] - c_water[i]) * t for i in range(4)]
                height = 0.2 + (height - 0.2) * t
                    
            return height, color

        # ===================================================
        # 5. ถักทอตาข่ายพื้นดิน (Terrain Mesh) 
        # ===================================================
        terrain_vertices = []
        terrain_indices = []
        
        for r in range(rows + 1):
            for c in range(cols + 1):
                y, color = get_terrain_data(c, r)
                x = c - offset_x
                z = r - offset_z
                terrain_vertices.extend([x, y, z, *color, -1.0, -1.0])

        for r in range(rows):
            for c in range(cols):
                p0 = r * (cols + 1) + c
                p1 = p0 + 1
                p2 = (r + 1) * (cols + 1) + c
                p3 = p2 + 1
                terrain_indices.extend([p0, p2, p1, p1, p2, p3])

        fmt = [(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')]
        self.terrain_group.add(Mesh(fmt=fmt, mode='triangles', vertices=terrain_vertices, indices=terrain_indices))

        # ===================================================
        # ✨ 6. สร้างพืชพรรณและต้นไม้ตามสภาพแวดล้อม (Biome Foliage)
        # ===================================================
        foliage_vertices = []
        foliage_indices = []
        foliage_idx = 0
        
        def add_foliage(tx, ty, tz, obj_type):
            nonlocal foliage_idx
            
            if obj_type == 'cactus':
                # กระบองเพชร: เป็นทรง 4 เหลี่ยม (Box) สีเขียวอ่อน
                w = random.uniform(0.06, 0.1) 
                h = random.uniform(0.4, 0.7)   
                shade = random.uniform(0.8, 1.1)
                col = [0.45 * shade, 0.8 * shade, 0.35 * shade, 1.0] # สีเขียวอ่อน
                
                base = foliage_idx
                # สร้างจุดยอด 8 จุด สำหรับทรงลูกบาศก์
                # ด้านบน 4 มุม
                foliage_vertices.extend([tx - w, ty + h, tz - w, *col, -1.0, -1.0]) # 0
                foliage_vertices.extend([tx + w, ty + h, tz - w, *col, -1.0, -1.0]) # 1
                foliage_vertices.extend([tx + w, ty + h, tz + w, *col, -1.0, -1.0]) # 2
                foliage_vertices.extend([tx - w, ty + h, tz + w, *col, -1.0, -1.0]) # 3
                # ฐานด้านล่าง 4 มุม
                foliage_vertices.extend([tx - w, ty, tz - w, *col, -1.0, -1.0]) # 4
                foliage_vertices.extend([tx + w, ty, tz - w, *col, -1.0, -1.0]) # 5
                foliage_vertices.extend([tx + w, ty, tz + w, *col, -1.0, -1.0]) # 6
                foliage_vertices.extend([tx - w, ty, tz + w, *col, -1.0, -1.0]) # 7
                
                # โยงสามเหลี่ยม 5 ด้าน (บน, หน้า, ขวา, หลัง, ซ้าย)
                foliage_indices.extend([
                    base, base+1, base+2, base, base+2, base+3,       # Top
                    base+3, base+2, base+6, base+3, base+6, base+7,   # Front
                    base+2, base+1, base+5, base+2, base+5, base+6,   # Right
                    base+1, base, base+4, base+1, base+4, base+5,     # Back
                    base, base+3, base+7, base, base+7, base+4        # Left
                ])
                foliage_idx += 8
                return # จบการสร้างกระบองเพชรทรงสี่เหลี่ยม
                
            elif obj_type == 'snow_tree':
                # ต้นไม้หิมะ: พีระมิดสีเทา (ไม่มีสีขาว)
                w = random.uniform(0.12, 0.25)
                h = random.uniform(0.6, 1.2)
                gray_shade = random.uniform(0.4, 0.7) # สุ่มความเข้มสีเทา
                col = [gray_shade, gray_shade, gray_shade, 1.0] 
            else: 
                # ต้นไม้ป่า: พีระมิด สีเขียว
                w = random.uniform(0.12, 0.25)
                h = random.uniform(0.6, 1.2)
                shade = random.uniform(0.7, 1.1)
                col = [0.15 * shade, 0.45 * shade, 0.15 * shade, 1.0]
                
            # สร้าง Low-Poly พีระมิด สำหรับต้นไม้ทั่วไปและต้นไม้หิมะ
            foliage_vertices.extend([tx, ty + h, tz, *col, -1.0, -1.0]) # ยอดบนสุด
            foliage_vertices.extend([tx - w, ty, tz - w, *col, -1.0, -1.0])
            foliage_vertices.extend([tx + w, ty, tz - w, *col, -1.0, -1.0])
            foliage_vertices.extend([tx + w, ty, tz + w, *col, -1.0, -1.0])
            foliage_vertices.extend([tx - w, ty, tz + w, *col, -1.0, -1.0])
            
            base = foliage_idx
            foliage_indices.extend([
                base, base+1, base+2, 
                base, base+2, base+3, 
                base, base+3, base+4, 
                base, base+4, base+1  
            ])
            foliage_idx += 5

        # สแกนพื้นที่เพื่อสุ่มปลูกต้นไม้แยกตาม Biome
        for r in range(rows):
            for c in range(cols):
                data = smooth_data[r][c]
                s_val = data['s']
                d_val = data['d']
                river_dist = abs(data['r'] - 0.5)
                elevation = data['e']
                
                # ปลูกเฉพาะบนบกเท่านั้น
                is_land = (river_dist > 0.04) and (elevation > 0.2)
                
                if is_land:
                    rx = (c - offset_x) + random.uniform(-0.4, 0.4)
                    rz = (r - offset_z) + random.uniform(-0.4, 0.4)
                    ry, _ = get_terrain_data(c, r) 
                    
                    if s_val < r_snow:
                        # โซนหิมะ (40%)
                        if random.random() < 0.40:
                            add_foliage(rx, ry, rz, 'snow_tree')
                    elif d_val < r_desert:
                        # โซนทะเลทราย (2%)
                        if random.random() < 0.02:
                            add_foliage(rx, ry, rz, 'cactus')
                    else:
                        # โซนป่า (15%)
                        if s_val > r_snow + 2 and d_val > r_desert + 2:
                            if random.random() < 0.15:
                                add_foliage(rx, ry, rz, 'forest_tree')
                            
        # ถ่ายทอดลงจอรวมเป็น Mesh เดียว
        if foliage_indices:
            self.terrain_group.add(Mesh(fmt=fmt, mode='triangles', vertices=foliage_vertices, indices=foliage_indices))

    # ระบบกล้องใช้พื้นฐานเดียวกับ Board3D Classic
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return super().on_touch_down(touch)

        if touch.button == 'scrollup':
            self.cam_dist = min(250.0, self.cam_dist + 5.0)
            return True
        elif touch.button == 'scrolldown':
            self.cam_dist = max(10.0, self.cam_dist - 5.0)
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
        self.proj_mat.view_clip(-aspect_ratio, aspect_ratio, -1, 1, 1, 1500, 1)
        
        cam_y = self.cam_dist * math.sin(self.rot_x)
        cam_x = self.cam_dist * math.cos(self.rot_x) * math.sin(self.rot_y)
        cam_z = self.cam_dist * math.cos(self.rot_x) * math.cos(self.rot_y)
        self.camera_mat = Matrix().look_at(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
        self.canvas['projection_mat'] = self.proj_mat
        self.canvas['modelview_mat'] = self.camera_mat.multiply(self.model_mat)
        self.canvas['texture0'] = 0