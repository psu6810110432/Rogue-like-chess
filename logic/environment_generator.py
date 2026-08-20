import random
import math
from kivy.lang import Builder
from kivy.uix.image import Image

# 1. เอา EnvTile ออกไป เพราะเราจะวาดสี (Procedural Canvas) แทน
Builder.load_string("""
<EnvProp>:
    allow_stretch: True
    keep_ratio: True
""")

class EnvProp(Image):
    def on_texture(self, instance, value):
        if self.texture:
            self.texture.mag_filter = 'nearest'
            self.texture.min_filter = 'nearest'

class EnvironmentGenerator:
    @staticmethod
    def generate_environment(map_w, map_h, nodes_data, edges_data):
        # ขยายแผ่นให้ใหญ่ขึ้นนิดหน่อยเพื่อลดภาระ Canvas
        tile_size = 150 
        cols = int(math.ceil(map_w / tile_size))
        rows = int(math.ceil(map_h / tile_size))
        
        # ===================================================
        # 1. จำลองศูนย์กลาง Biome หิมะและทะเลทราย (แบบเดียวกับ 3D)
        # ===================================================
        total_area = rows * cols
        r_snow = math.sqrt((0.18 * total_area) / (2 * math.pi))
        r_desert = math.sqrt((0.18 * total_area) / (3 * math.pi))
        
        snow_centers = []
        for _ in range(2):
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            margin = 5 
            if edge == 'top': pt = (random.uniform(0, cols), random.uniform(rows - margin, rows))
            elif edge == 'bottom': pt = (random.uniform(0, cols), random.uniform(0, margin))
            elif edge == 'left': pt = (random.uniform(0, margin), random.uniform(0, rows))
            else: pt = (random.uniform(cols - margin, cols), random.uniform(0, rows))
            snow_centers.append(pt)
        
        desert_centers = []
        for _ in range(3):
            for _ in range(100):
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                margin = 5 
                if edge == 'top': pt = (random.uniform(0, cols), random.uniform(rows - margin, rows))
                elif edge == 'bottom': pt = (random.uniform(0, cols), random.uniform(0, margin))
                elif edge == 'left': pt = (random.uniform(0, margin), random.uniform(0, rows))
                else: pt = (random.uniform(cols - margin, cols), random.uniform(0, rows))
                
                # ทะเลทรายต้องห่างจากหิมะ
                if all(math.hypot(pt[0] - sx, pt[1] - sy) > (cols * 0.3) for sx, sy in snow_centers):
                    desert_centers.append(pt)
                    break
            else:
                desert_centers.append(pt)

        # ===================================================
        # 2. คำนวณสีและการเปลี่ยนผ่าน (Smooth Blending)
        # ===================================================
        biome_grid = {}
        tiles = []
        
        c_snow = (0.85, 0.85, 0.9, 1)
        c_desert = (0.76, 0.7, 0.5, 1)
        c_forest_base = (0.35, 0.55, 0.3, 1)     
        c_forest_warm = (0.45, 0.55, 0.2, 1)    
        c_forest_cool = (0.25, 0.55, 0.4, 1)  
        inf_radius = 8.0

        for cx in range(cols):
            for cy in range(rows):
                s_val = min([math.hypot(cx - sx, cy - sy) for sx, sy in snow_centers])
                d_val = min([math.hypot(cx - dx, cy - dy) for dx, dy in desert_centers])
                
                # กำหนดชนิด Biome เพื่อให้ Props ไปเกิดถูกที่
                if s_val < r_snow + (inf_radius/2): biome_grid[(cx, cy)] = 'tundra'
                elif d_val < r_desert + (inf_radius/2): biome_grid[(cx, cy)] = 'dessert'
                else: biome_grid[(cx, cy)] = 'plain'
                
                # ผสมสี
                base_grass_color = list(c_forest_base)
                if s_val < r_snow + inf_radius:
                    t_inf = max(0, min(1, (r_snow + inf_radius - s_val) / inf_radius))
                    base_grass_color = [c_forest_base[i] + (c_forest_cool[i] - c_forest_base[i]) * t_inf for i in range(4)]
                elif d_val < r_desert + inf_radius:
                    t_inf = max(0, min(1, (r_desert + inf_radius - d_val) / inf_radius))
                    base_grass_color = [c_forest_base[i] + (c_forest_warm[i] - c_forest_base[i]) * t_inf for i in range(4)]

                color = list(base_grass_color)
                if s_val < r_snow:
                    t = max(0, min(1, (r_snow - s_val) / 5.0))
                    color = [base_grass_color[i] + (c_snow[i] - base_grass_color[i]) * t for i in range(4)]
                elif d_val < r_desert:
                    t = max(0, min(1, (r_desert - d_val) / 5.0))
                    color = [base_grass_color[i] + (c_desert[i] - base_grass_color[i]) * t for i in range(4)]

                tiles.append({
                    'color': color,
                    'x': cx * tile_size,
                    'y': cy * tile_size,
                    'w': tile_size + 2, # +2 เผื่อขอบไว้เหลื่อมทับกันนิดหน่อย
                    'h': tile_size + 2 
                })

        # ===================================================
        # 3. วาง Props ลงบน Biome (โค้ดเดิมของคุณ แต่ทำงานแม่นยำขึ้น)
        # ===================================================
        def get_biome(px, py):
            bx = int(px // tile_size)
            by = int(py // tile_size)
            return biome_grid.get((bx, by), 'plain')

        def is_overlapping_path(px, py, safe_radius=250):
            for node in nodes_data:
                nx, ny = node['pos']
                if math.hypot(px - nx, py - ny) < safe_radius: return True
            for u, v in edges_data:
                x1, y1 = u['pos']
                x2, y2 = v['pos']
                l2 = (x1 - x2)**2 + (y1 - y2)**2
                if l2 == 0:
                    dist = math.hypot(px - x1, py - y1)
                else:
                    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
                    proj_x, proj_y = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                    dist = math.hypot(px - proj_x, py - proj_y)
                if dist < safe_radius: return True
            return False

        props = []
        num_mountain_chains = int((map_w * map_h) / 3000000)
        for _ in range(num_mountain_chains):
            cx, cy = random.randint(0, map_w), random.randint(0, map_h)
            angle = random.uniform(0, 2 * math.pi) 
            chain_length = random.randint(5, 12)
            
            for _ in range(chain_length):
                biome = get_biome(cx, cy)
                if biome != 'dessert' and not is_overlapping_path(cx, cy, safe_radius=300):
                    props.append({'type': random.choice(['mountain', 'peak']), 'x': cx, 'y': cy, 'size': random.randint(250, 400)})
                cx += math.cos(angle) * random.randint(150, 250)
                cy += math.sin(angle) * random.randint(150, 250)

        num_forest_clusters = int((map_w * map_h) / 2000000)
        for _ in range(num_forest_clusters):
            cx, cy = random.randint(0, map_w), random.randint(0, map_h)
            if get_biome(cx, cy) == 'dessert': continue
            
            for _ in range(random.randint(15, 30)):
                fx, fy = cx + random.uniform(-400, 400), cy + random.uniform(-400, 400)
                fx_biome = get_biome(fx, fy)
                if fx_biome == 'dessert': continue
                
                prop_type = 'forest' if fx_biome == 'plain' else 'tundra_forest'
                if not is_overlapping_path(fx, fy, safe_radius=150):
                    props.append({'type': prop_type, 'x': fx, 'y': fy, 'size': random.randint(200, 350)})

        num_trees = int((map_w * map_h) / 1000000)
        tree_positions = []
        for _ in range(num_trees * 2):
            tx, ty = random.randint(0, map_w), random.randint(0, map_h)
            biome = get_biome(tx, ty)
            if biome == 'tundra': continue 
            
            prop_type = 'tree' if biome == 'plain' else random.choice(['die_tree1', 'die_tree2'])
            if not any(math.hypot(tx - ex, ty - ey) < 300 for ex, ey in tree_positions) and not is_overlapping_path(tx, ty, safe_radius=150):
                tree_positions.append((tx, ty))
                props.append({'type': prop_type, 'x': tx, 'y': ty, 'size': random.randint(150, 250)})

        props.sort(key=lambda p: p['y'], reverse=True)
        return tiles, props