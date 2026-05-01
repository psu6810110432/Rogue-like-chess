# logic/campaign_map_generator.py
import random
from kivy.metrics import dp
from logic.campaign_helpers import is_overlapping_any, get_distance

class MapGenerator:
    @staticmethod
    def generate_data(size_val, map_w=9600, map_h=5400):
        num_castles, num_villages = {'Size_S':(1,2), 'Size_M':(2,3), 'Size_L':(3,4)}.get(size_val, (1,2))
        water_rects = []
        
        # 1. คำนวณตำแหน่งแม่น้ำและทะเลสาบ
        for _ in range(150):
            w, h = random.randint(200, 700), random.randint(200, 700)
            x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
            if not is_overlapping_any((x, y, w, h), water_rects):
                water_rects.append((x, y, w, h))
                
        for _ in range(250):
            w, h = random.randint(150, 400), random.randint(150, 400)
            x, y = random.randint(0, map_w - w), random.randint(0, map_h - h)
            if not is_overlapping_any((x, y, w, h), water_rects):
                water_rects.append((x, y, w, h))

        # 2. ฟังก์ชันช่วยคำนวณหาจุดวางฐาน
        def generate_nodes(base_faction, count_castles, count_villages, min_x, max_x, existing_nodes):
            faction_nodes = []
            types_to_spawn = ['castle'] * count_castles + ['village'] * count_villages
            for i, n_type in enumerate(types_to_spawn):
                for _ in range(500):
                    nx, ny = random.randint(min_x, max_x), random.randint(300, map_h - 300)
                    if is_overlapping_any((nx-80, ny-80, 160, 160), water_rects): continue
                    too_close = any(get_distance((nx, ny), ex['pos']) < dp(200) for ex in existing_nodes + faction_nodes)
                    if not too_close:
                        is_main = (i == 0)
                        faction_nodes.append({'pos': (nx, ny), 'faction': base_faction if is_main else 'red', 'type': n_type, 'id': f"{base_faction[0].upper()}{i}", 'main': is_main})
                        break
            return faction_nodes

        w_nodes = generate_nodes('white', num_castles, num_villages, 500, 4000, [])
        b_nodes = generate_nodes('black', num_castles, num_villages, 5600, 9100, w_nodes)

        # 3. ฟังก์ชันคำนวณเส้นทางเชื่อมต่อ (ถนน)
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

        # 4. คำนวณเส้นเชื่อมระหว่างสองเผ่าพันธุ์ (พรมแดน)
        min_cross, cross_edge = float('inf'), None
        for w in w_nodes:
            for b in b_nodes:
                d = get_distance(w['pos'], b['pos'])
                if d < min_cross: min_cross, cross_edge = d, (w, b)

        return {
            'water_rects': water_rects,
            'w_nodes': w_nodes,
            'b_nodes': b_nodes,
            'white_edges': white_edges,
            'black_edges': black_edges,
            'cross_edge': cross_edge
        }