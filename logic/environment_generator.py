import random
import math
from kivy.lang import Builder
from kivy.uix.image import Image

# 1. เขียน KV เพื่อตั้งค่า UI พื้นฐาน
Builder.load_string("""
<EnvTile>:
    allow_stretch: True
    keep_ratio: False

<EnvProp>:
    allow_stretch: True
    keep_ratio: True
""")

# 2. คลาสสำหรับปรับความคมชัด (Nearest Filter) อัตโนมัติเมื่อ Texture โหลดเสร็จ
class EnvTile(Image):
    def on_texture(self, instance, value):
        if self.texture:
            self.texture.mag_filter = 'nearest'
            self.texture.min_filter = 'nearest'

class EnvProp(Image):
    def on_texture(self, instance, value):
        if self.texture:
            self.texture.mag_filter = 'nearest'
            self.texture.min_filter = 'nearest'

# 3. ระบบคำนวณและ Generate สภาพแวดล้อม
class EnvironmentGenerator:
    @staticmethod
    def generate_environment(map_w, map_h, nodes_data, edges_data):
        # ปรับขนาดให้เล็กลงมาก (เพื่อใช้จำนวนแผ่นเยอะขึ้น เบลนขอบได้เนียนขึ้น)
        tile_size = 100
        cols = int(math.ceil(map_w / tile_size))
        rows = int(math.ceil(map_h / tile_size))
        
        # 1. สุ่มแบบหยาบๆ ก่อน (ให้ Plain มีโอกาสเกิดเยอะกว่าเพื่อเป็นพื้นหลัก)
        raw_grid = {}
        for cx in range(cols):
            for cy in range(rows):
                raw_grid[(cx, cy)] = random.choice(['plain', 'plain', 'tundra', 'dessert'])
                
        # 2. เกลี่ยให้เป็นกลุ่มก้อนธรรมชาติ (Cellular Automata Smoothing) 2 รอบ
        for pass_num in range(2):
            temp_grid = {}
            for cx in range(cols):
                for cy in range(rows):
                    neighbors = []
                    # ดึงข้อมูลช่องรอบๆ ตัวเองแบบ 3x3
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = cx + dx, cy + dy
                            if (nx, ny) in raw_grid:
                                neighbors.append(raw_grid[(nx, ny)])
                    
                    # เลือกสภาพแวดล้อมที่เยอะที่สุดในรอบข้างมาเป็นของตัวเอง
                    most_common = max(set(neighbors), key=neighbors.count)
                    temp_grid[(cx, cy)] = most_common
            raw_grid = temp_grid.copy()
            
        biome_grid = raw_grid
        
        # 3. แปลงเป็นรายการ Tiles
        tiles = []
        for cx in range(cols):
            for cy in range(rows):
                tiles.append({
                    'biome': biome_grid[(cx, cy)],
                    'x': cx * tile_size,
                    'y': cy * tile_size,
                    # +2 เผื่อขอบไว้เหลื่อมทับกันนิดหน่อย ป้องกันเกิดเส้นขอบดำ (Seam gap)
                    'w': tile_size + 2,
                    'h': tile_size + 2 
                })

        # ฟังก์ชันค้นหาว่าพิกัดนั้นอยู่บน Biome อะไร
        def get_biome(px, py):
            bx = int(px // tile_size)
            by = int(py // tile_size)
            return biome_grid.get((bx, by), 'plain')

        # ฟังก์ชันเช็คว่าจุดนั้นทับกับโหนดหรือเส้นทางไหม
        def is_overlapping_path(px, py, safe_radius=250):
            for node in nodes_data:
                nx, ny = node['pos']
                if math.hypot(px - nx, py - ny) < safe_radius:
                    return True
            for u, v in edges_data:
                x1, y1 = u['pos']
                x2, y2 = v['pos']
                l2 = (x1 - x2)**2 + (y1 - y2)**2
                if l2 == 0:
                    dist = math.hypot(px - x1, py - y1)
                else:
                    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
                    proj_x = x1 + t * (x2 - x1)
                    proj_y = y1 + t * (y2 - y1)
                    dist = math.hypot(px - proj_x, py - proj_y)
                if dist < safe_radius:
                    return True
            return False

        props = []

        # --- Generate Mountains & Peaks (ไม่เกิดใน Dessert) ---
        num_mountain_chains = int((map_w * map_h) / 3000000)
        for _ in range(num_mountain_chains):
            cx, cy = random.randint(0, map_w), random.randint(0, map_h)
            angle = random.uniform(0, 2 * math.pi) 
            chain_length = random.randint(5, 12)
            
            for _ in range(chain_length):
                biome = get_biome(cx, cy)
                if biome != 'dessert' and not is_overlapping_path(cx, cy, safe_radius=300):
                    prop_type = random.choice(['mountain', 'peak'])
                    props.append({'type': prop_type, 'x': cx, 'y': cy, 'size': random.randint(250, 400)})
                cx += math.cos(angle) * random.randint(150, 250)
                cy += math.sin(angle) * random.randint(150, 250)

        # --- Generate Forests (กระจุกหนาแน่น, Plain=forest, Tundra=tundra_forest) ---
        num_forest_clusters = int((map_w * map_h) / 2000000)
        for _ in range(num_forest_clusters):
            cx, cy = random.randint(0, map_w), random.randint(0, map_h)
            cluster_biome = get_biome(cx, cy)
            
            if cluster_biome == 'dessert': continue # ทะเลทรายไม่มีป่า
            
            cluster_density = random.randint(15, 30)
            for _ in range(cluster_density):
                fx = cx + random.uniform(-400, 400)
                fy = cy + random.uniform(-400, 400)
                fx_biome = get_biome(fx, fy)
                
                if fx_biome == 'dessert': continue
                
                prop_type = 'forest' if fx_biome == 'plain' else 'tundra_forest'
                
                if not is_overlapping_path(fx, fy, safe_radius=150):
                    props.append({'type': prop_type, 'x': fx, 'y': fy, 'size': random.randint(200, 350)})

        # --- Generate Trees (เกิดห่างๆ, Plain=tree, Dessert=die_tree1/2) ---
        num_trees = int((map_w * map_h) / 1000000)
        tree_positions = []
        for _ in range(num_trees * 2):
            tx, ty = random.randint(0, map_w), random.randint(0, map_h)
            biome = get_biome(tx, ty)
            
            if biome == 'tundra': continue # Tundra มีแค่ป่าสน ไม่มีต้นไม้เดี่ยว
            
            prop_type = 'tree' if biome == 'plain' else random.choice(['die_tree1', 'die_tree2'])
            too_close = any(math.hypot(tx - ex, ty - ey) < 300 for ex, ey in tree_positions)
            
            if not too_close and not is_overlapping_path(tx, ty, safe_radius=150):
                tree_positions.append((tx, ty))
                props.append({'type': prop_type, 'x': tx, 'y': ty, 'size': random.randint(150, 250)})

        # --- Generate Lakes (เฉพาะ Plain) ---
        num_lakes = int((map_w * map_h) / 4000000)
        plain_tiles = [t for t in tiles if t['biome'] == 'plain']
        if plain_tiles:
            for _ in range(num_lakes):
                target_tile = random.choice(plain_tiles)
                lx = target_tile['x'] + random.randint(20, tile_size - 1)
                ly = target_tile['y'] + random.randint(20, tile_size - 1)
                if not is_overlapping_path(lx, ly, safe_radius=300):
                    props.append({'type': 'lake', 'x': lx, 'y': ly, 'size': random.randint(300, 500)})

        # เรียงลำดับจาก Y เพื่อให้ภาพซ้อนทับกันอย่างถูกต้อง (Fake 3D Depth)
        props.sort(key=lambda p: p['y'], reverse=True)

        return tiles, props