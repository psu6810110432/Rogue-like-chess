# components/board_3d.py
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext, Mesh, PushMatrix, PopMatrix, Callback, InstructionGroup, Translate, Rotate, BindTexture, Color, Rectangle
from kivy.graphics.transformation import Matrix
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.core.window import Window
import math
import os

class Board3D(Widget):
    def __init__(self, map_name='Classic Board', on_square_click=None, **kwargs):
        super().__init__(**kwargs)
        self.canvas = RenderContext(compute_normal_mat=True)
        
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
        
        self.rot_x = math.radians(45) 
        self.rot_y = math.radians(45) 
        self.cam_dist = 12.0 # ระยะซูมกล้องเริ่มต้น
        
        self.map_name = map_name
        self.touch_start = None
        self.piece_rotations = []
        self.on_square_click = on_square_click
        self._debug_rect_shown = False

        with self.canvas:
            PushMatrix()
            self.setup_scene()
            self.pieces_group = InstructionGroup()
            self.canvas.add(self.pieces_group)
            PopMatrix()
            
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def setup_scene(self):
        vertex_format = [(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')]
        vertices, indices = [], []
        
        if self.map_name == 'Enchanted Forest': color_light, color_dark = (0.55, 0.65, 0.55, 1), (0.35, 0.45, 0.35, 1)
        elif self.map_name == 'Desert Ruins': color_light, color_dark = (0.9, 0.65, 0.2, 1), (0.7, 0.45, 0.1, 1)
        elif self.map_name == 'Frozen Tundra': color_light, color_dark = (0.5, 0.8, 0.95, 1), (0.15, 0.4, 0.75, 1)
        else: color_light, color_dark = (0.8, 0.8, 0.8, 1), (0.4, 0.4, 0.4, 1)

        tile_size = 1.0
        offset = 4.0 
        

        idx = 0
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0: r, g, b, a = color_light
                else: r, g, b, a = color_dark
                    
                x0 = col * tile_size - offset
                z0 = row * tile_size - offset
                x1 = x0 + tile_size
                z1 = z0 + tile_size
                y = 0.0
                
                vertices.extend([x0, y, z0, r, g, b, a, -1.0, -1.0]) 
                vertices.extend([x0, y, z1, r, g, b, a, -1.0, -1.0]) 
                vertices.extend([x1, y, z1, r, g, b, a, -1.0, -1.0]) 
                vertices.extend([x1, y, z0, r, g, b, a, -1.0, -1.0]) 
                indices.extend([idx, idx+1, idx+2, idx, idx+2, idx+3])
                idx += 4
                
        self.board_mesh = Mesh(fmt=vertex_format, mode='triangles', vertices=vertices, indices=indices)

    
    def draw_pieces(self, board_data, image_path_resolver, selected=None, legal_moves=None):
        self.pieces_group.clear()
        self.piece_rotations.clear()

        tile_size = 1.0
        offset = 4.0

        for row in range(8):
            for col in range(8):
                is_selected = (selected == (row, col))
                is_legal = ((row, col) in legal_moves)
                
                if is_selected or is_legal:
                    # สีเขียวสำหรับตัวที่เลือก, สีฟ้าสำหรับช่องที่เดินได้ (RGBA)
                    color = (0.2, 0.8, 0.2, 0.6) if is_selected else (0.2, 0.5, 0.8, 0.6)
                    
                    group = InstructionGroup()
                    group.add(PushMatrix())
                    # ยกแผ่นสีขึ้นมาจากพื้นเล็กน้อย (y=0.01) เพื่อไม่ให้สีจมหรือกระพริบสลับกับพื้นกระดาน
                    group.add(Translate(col * tile_size - offset, 0.01, row * tile_size - offset))
                    
                    # สร้างแผ่นสี่เหลี่ยมขนาดเท่า 1 ช่องตาราง
                    # ส่ง UV เป็น -1.0 เพื่อบอก Shader ให้ใช้สีทึบ ไม่ใช้รูปภาพ
                    v_highlight = [
                        0, 0, 0,  *color,  -1.0, -1.0,
                        0, 0, 1,  *color,  -1.0, -1.0,
                        1, 0, 1,  *color,  -1.0, -1.0,
                        1, 0, 0,  *color,  -1.0, -1.0
                    ]
                    i_highlight = [0, 1, 2, 0, 2, 3]
                    
                    group.add(Mesh(
                        fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                        mode='triangles', vertices=v_highlight, indices=i_highlight
                    ))
                    group.add(PopMatrix())
                    self.pieces_group.add(group)

        for row in range(8):
            for col in range(8):
                piece = board_data[row][col]
                if not piece:
                    continue

                img_path = image_path_resolver(piece)
                if not img_path or not os.path.exists(img_path):
                    continue

                try:
                    tex = CoreImage(img_path).texture
                    if not tex: 
                        continue
                    tex.mag_filter = 'nearest'
                    tex.min_filter = 'nearest'
                except Exception as e:
                    print(f"Load error: {e}")
                    continue

                group = InstructionGroup()
                group.add(PushMatrix())
                group.add(Translate(col * tile_size - offset + 0.5, 0, row * tile_size - offset + 0.5))
                
                # ให้หมากหันหน้าเข้าหากล้องเสมอ
                rot = Rotate(angle=math.degrees(self.rot_y), axis=(0, 1, 0))
                self.piece_rotations.append(rot)
                group.add(rot)
                
                # ขนาดตัวหมาก
                w, h = 1.0, 1.5
                
                # พิกัด Vertex และ UV แบบพลิกแกน Y ด้วยตัวเอง (0=บน, 1=ล่าง)
                v_piece = [
                    -w/2, h, 0,  1,1,1,1,  0, 0, # มุมซ้ายบน
                    -w/2, 0, 0,  1,1,1,1,  0, 1, # มุมซ้ายล่าง
                     w/2, 0, 0,  1,1,1,1,  1, 1, # มุมขวาล่าง
                     w/2, h, 0,  1,1,1,1,  1, 0  # มุมขวาบน
                ]
                i_piece = [0, 1, 2, 0, 2, 3]
                
                # ✨ หัวใจหลักของความคลีน: ส่ง texture เข้า Mesh โดยตรง
                group.add(Mesh(
                    fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                    mode='triangles',
                    vertices=v_piece,
                    indices=i_piece,
                    texture=tex
                ))
                
                group.add(PopMatrix())
                self.pieces_group.add(group)


    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return super().on_touch_down(touch)

        # ระบบซูมเข้า-ออก (Scroll)
        if touch.button == 'scrollup':
            self.cam_dist = min(22.0, self.cam_dist + 0.8)
            return True
        elif touch.button == 'scrolldown':
            self.cam_dist = max(6.0, self.cam_dist - 0.8)
            return True

        # ระบบหมุนมุมกล้อง (คลิกขวา)
        if touch.button == 'right':
            touch.grab(self)
            self.touch_start = touch.pos
            return True
            
        # ❌ ลบระบบคลิกซ้าย (Raycast) ออกทั้งหมด ❌
        
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.touch_start:
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            
            # ✨ แก้ไขทิศทางหมุนซ้าย-ขวา: เปลี่ยนจาก + เป็น - เพื่อให้หมุนตามทิศทางเมาส์ที่ลากจริง
            self.rot_y -= dx * 0.005 
            
            self.rot_x -= dy * 0.005 
            self.rot_x = max(0.1, min(math.pi / 2.2, self.rot_x))
            self.touch_start = touch.pos
            return True
        if not touch.button == 'right':
            # ใช้สมการแปลงพิกัดเมาส์แบบเดียวกับตอนคลิกเป๊ะๆ
            aspect_ratio = float(self.width) / float(self.height) if self.height else 1.0
            local_x = touch.x - self.x
            local_y = touch.y - self.y
            
            nx = ((2.0 * local_x) / self.width - 1.0)
            ny = (2.0 * local_y) / self.height - 1.0
            
            # คำนวณรังสี (Ray) ...
            cam_y = self.cam_dist * math.sin(self.rot_x)
            cam_x = self.cam_dist * math.cos(self.rot_x) * math.sin(self.rot_y)
            cam_z = self.cam_dist * math.cos(self.rot_x) * math.cos(self.rot_y)

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touch_start = None
            return True
        return super().on_touch_up(touch)

    def update_glsl(self, dt):
        aspect_ratio = float(self.width) / float(self.height) if self.height else 1.0
        self.proj_mat.view_clip(-aspect_ratio, aspect_ratio, -1, 1, 1, 100, 1)
        
        cam_y = self.cam_dist * math.sin(self.rot_x)
        cam_x = self.cam_dist * math.cos(self.rot_x) * math.sin(self.rot_y)
        cam_z = self.cam_dist * math.cos(self.rot_x) * math.cos(self.rot_y)
        self.camera_mat = Matrix().look_at(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
        self.canvas['projection_mat'] = self.proj_mat
        self.canvas['modelview_mat'] = self.camera_mat.multiply(self.model_mat)
        self.canvas['texture0'] = 0

        degree_y = math.degrees(self.rot_y)
        for rot_instruction in self.piece_rotations:
            rot_instruction.angle = degree_y