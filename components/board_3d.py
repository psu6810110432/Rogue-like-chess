# components/board_3d.py
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext, Mesh, PushMatrix, PopMatrix, Callback, InstructionGroup, Translate, Rotate, BindTexture, Color, Rectangle
from kivy.graphics.transformation import Matrix
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.core.window import Window
# ✨ เพิ่มบรรทัดนี้ลงไปใต้ CoreImage
from kivy.core.text import Label as CoreLabel
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

    # ✨ เพิ่มพารามิเตอร์ game_mode, phase และ current_player
    def draw_pieces(self, board_data, image_path_resolver, selected=None, legal_moves=None, last_move=None, game_mode='classic', phase='battle', current_player='white'):
        self.pieces_group.clear()
        self.piece_rotations.clear()

        if legal_moves is None: legal_moves = []
        if last_move is None: last_move = []

        tile_size = 1.0
        offset = 4.0

        # ==========================================
        # 1. วาดไฮไลต์ช่องบนพื้นกระดาน + ตัวอักษรพิกัด
        # ==========================================
        for row in range(8):
            for col in range(8):
                is_selected = (selected == (row, col))
                is_legal = ((row, col) in legal_moves)
                is_last = ((row, col) in last_move) 
                
                # ✨ เช็คว่าเป็นโซนจัดทัพหรือไม่ และให้ไฮไลต์เรืองแสงอ่อนๆ
                is_deploy_zone = False
                if game_mode == 'Divide_Conquer':
                    if phase == 'deployment_arrange_atk' and row >= 5:
                        is_deploy_zone = True
                    elif phase == 'deployment_arrange_def' and row <= 2:
                        is_deploy_zone = True
                
                if is_selected or is_legal or is_last or is_deploy_zone:
                    # ลำดับความสำคัญของสี: เขียว(เลือก) > ฟ้า(เดินได้/วางได้) > เหลือง(ตาที่แล้ว) > เขียวจาง(โซนจัดทัพ)
                    if is_selected: color = (0.2, 0.8, 0.2, 0.6) 
                    elif is_legal: color = (0.2, 0.5, 0.8, 0.6)
                    elif is_last: color = (0.8, 0.8, 0.2, 0.6)
                    elif is_deploy_zone: color = (0.2, 0.8, 0.2, 0.15)
                    
                    group = InstructionGroup()
                    
                    group.add(PushMatrix())
                    group.add(Translate(col * tile_size - offset, 0.01, row * tile_size - offset))
                    v_highlight = [
                        0, 0, 0,  *color,  -1.0, -1.0,  0, 0, 1,  *color,  -1.0, -1.0,
                        1, 0, 1,  *color,  -1.0, -1.0,  1, 0, 0,  *color,  -1.0, -1.0
                    ]
                    group.add(Mesh(
                        fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                        mode='triangles', vertices=v_highlight, indices=[0, 1, 2, 0, 2, 3]
                    ))
                    group.add(PopMatrix())
                    
                    # ตัวอักษรพิกัด
                    if is_legal:
                        notation = f"{chr(65+col)}{row+1}"
                        lbl = CoreLabel(text=notation, font_size=40, color=(1, 1, 1, 1), bold=True)
                        lbl.refresh()
                        text_tex = lbl.texture
                        
                        if text_tex:
                            group.add(PushMatrix())
                            group.add(Translate(col * tile_size - offset + 0.5, 0.05, row * tile_size - offset + 0.5))
                            rot = Rotate(angle=math.degrees(self.rot_y), axis=(0, 1, 0))
                            self.piece_rotations.append(rot)
                            group.add(rot)
                            tw, th = 0.6, 0.6
                            v_text = [
                                -tw/2, th/2, 0,  1,1,1,1,  0, 0,  -tw/2, -th/2, 0,  1,1,1,1,  0, 1,
                                 tw/2, -th/2, 0,  1,1,1,1,  1, 1,   tw/2, th/2, 0,  1,1,1,1,  1, 0 
                            ]
                            group.add(Mesh(
                                fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                                mode='triangles', vertices=v_text, indices=[0, 1, 2, 0, 2, 3], texture=text_tex
                            ))
                            group.add(PopMatrix())
                            
                    self.pieces_group.add(group)

        # ==========================================
        # 2. วาดตัวหมาก + Icon 
        # ==========================================
        for row in range(8):
            for col in range(8):
                piece = board_data[row][col]

                # ✨ 1. กำหนดว่าแถวไหนคือโซนศัตรู
                is_enemy_zone = False
                if game_mode == 'Divide_Conquer':
                    if phase == 'deployment_arrange_atk' and row <= 2:
                        is_enemy_zone = True
                    elif phase == 'deployment_arrange_def' and row >= 5:
                        is_enemy_zone = True

                img_path = None
                icons_to_draw = []

                # ✨ 2. กำหนดรูปภาพและไอคอน
                if is_enemy_zone:
                    # โซนศัตรู: บังคับวาดรูปเงาดำทั้งหมด ไม่ต้องสนใจว่ามีหมากจริงไหม (Fake Enemy)
                    img_path = 'assets/ui/hidden_enemy.png'
                else:
                    # โซนเรา: ถ้าไม่มีหมาก ให้ข้ามช่องนี้ไปเลย
                    if not piece: continue

                    # ถ้ามีหมาก ให้โหลดรูปและเก็บไอคอน (ทำแค่รอบเดียวจบ)
                    img_path = image_path_resolver(piece)
                    
                    if getattr(piece, 'passive_icon', None): 
                        icons_to_draw.append(piece.passive_icon)
                        
                    hp = getattr(piece, 'hidden_passive', None)
                    if hp and getattr(hp, 'passive_type', None):
                        hp_icon = f"assets/icon_effect/{hp.description.lower().replace(' ', '_')}.png"
                        icons_to_draw.append(hp_icon)
                        
                    it = getattr(piece, 'item', None)
                    if it and hasattr(it, 'image_path'): 
                        icons_to_draw.append(it.image_path)

                # ✨ 3. ตรวจสอบว่ามีไฟล์รูปไหม
                if not img_path or not os.path.exists(img_path): continue
                
                try:
                    tex = CoreImage(img_path).texture
                    if not tex: continue
                    tex.mag_filter = 'nearest'
                    tex.min_filter = 'nearest'
                except Exception: continue

                # ✨ 4. เริ่มวาด 3D Mesh
                group = InstructionGroup()
                group.add(PushMatrix())
                group.add(Translate(col * tile_size - offset + 0.5, 0, row * tile_size - offset + 0.5))
                rot = Rotate(angle=math.degrees(self.rot_y), axis=(0, 1, 0))
                self.piece_rotations.append(rot)
                group.add(rot)
                
                w, h = 1.0, 1.5
                v_piece = [
                    -w/2, h, 0, 1,1,1,1, 0,0,  -w/2, 0, 0, 1,1,1,1, 0,1,
                     w/2, 0, 0, 1,1,1,1, 1,1,   w/2, h, 0, 1,1,1,1, 1,0 
                ]
                group.add(Mesh(
                    fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                    mode='triangles', vertices=v_piece, indices=[0, 1, 2, 0, 2, 3], texture=tex
                ))
                
                # วาดไอคอน
                start_y = 1.2 
                for icon_path in icons_to_draw:
                    if icon_path and os.path.exists(icon_path):
                        try:
                            icon_tex = CoreImage(icon_path).texture
                            if icon_tex:
                                icon_tex.mag_filter, icon_tex.min_filter = 'nearest', 'nearest'
                                group.add(PushMatrix())
                                group.add(Translate(0.35, start_y, 0)) 
                                iw, ih = 0.4, 0.4
                                v_icon = [
                                    -iw/2, ih, 0, 1,1,1,1, 0,0,  -iw/2, 0, 0, 1,1,1,1, 0,1,
                                     iw/2, 0, 0, 1,1,1,1, 1,1,   iw/2, ih, 0, 1,1,1,1, 1,0 
                                ]
                                group.add(Mesh(
                                    fmt=[(b'v_pos', 3, 'float'), (b'v_color', 4, 'float'), (b'v_tc0', 2, 'float')],
                                    mode='triangles', vertices=v_icon, indices=[0, 1, 2, 0, 2, 3], texture=icon_tex
                                ))
                                group.add(PopMatrix())
                                start_y -= 0.45 
                        except Exception: pass
                
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