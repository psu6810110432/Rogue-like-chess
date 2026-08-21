# components/crash_overlay.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.app import App
from kivy.metrics import dp
from logic.image_utils import safe_char_crash_path
from logic.crash_logic import calculate_total_points
from kivy.animation import Animation

# คลาสรูปภาพ Python สำหรับปรับ Pixel Art ให้คมชัด
class PixelImage(Image):
    def on_texture(self, instance, value):
        if self.texture:
            self.texture.mag_filter = 'nearest'

# KV Language รวม Layout การจัดวางและ Animation
KV = '''
<FlippedPixelImage@PixelImage>:
    canvas.before:
        PushMatrix
        Scale:
            x: -1
            y: 1
            origin: self.center
    canvas.after:
        PopMatrix

<CrashOverlay>:
    # 1. ฉากหลัง (เลื่อนเข้ามาเกยกัน)
    PixelImage:
        id: bg1
        source: 'assets/crash_background/background-1.png'
        size_hint: 1.0, 1.0
        pos_hint: {'right': 0, 'y': 0}
        allow_stretch: True
        keep_ratio: False
        
    PixelImage:
        id: bg2
        source: 'assets/crash_background/background-2.png'
        size_hint: 1.0, 1.0
        pos_hint: {'x': 1, 'y': 0}
        allow_stretch: True
        keep_ratio: False

    # 2. ป้ายแสดงผลสถานะ (BREAKING, DRAW, STAGGER, DISTORTION)
    Label:
        id: status_lbl
        text: ""
        font_size: '60sp'
        bold: True
        color: (1, 1, 1, 1)
        pos_hint: {'center_x': 0.5, 'center_y': 0.85}
        opacity: 0

    # 3. หน้าต่างฝ่ายบุก (ซ้าย) 
    # เรียงลำดับ: 1 เหรียญ -> 2 Total -> 3 ตัวละคร -> 4 Base
    BoxLayout:
        id: left_ui
        orientation: 'vertical'
        size_hint: 0.38, 0.9
        pos_hint: {'x': -0.5, 'center_y': 0.5}
        spacing: dp(5)
        opacity: 0
        
        GridLayout:
            id: left_coins
            cols: 5
            size_hint_y: 0.15
            spacing: dp(2)
            
        Label:
            id: left_total
            text: ""
            size_hint_y: 0.15
            font_size: '54sp'
            bold: True
        
        PixelImage:
            id: left_char
            size_hint_y: 0.6
            allow_stretch: True
            
        Label:
            id: left_base
            text: ""
            size_hint_y: 0.1
            font_size: '22sp'
            bold: True
            color: (1, 0.85, 0.4, 1)

    # 4. หน้าต่างฝ่ายรับ (ขวา)
    BoxLayout:
        id: right_ui
        orientation: 'vertical'
        size_hint: 0.38, 0.9
        pos_hint: {'right': 1.5, 'center_y': 0.5}
        spacing: dp(5)
        opacity: 0
        
        GridLayout:
            id: right_coins
            cols: 5
            size_hint_y: 0.15
            spacing: dp(2)
            
        Label:
            id: right_total
            text: ""
            size_hint_y: 0.15
            font_size: '54sp'
            bold: True
        
        FlippedPixelImage:
            id: right_char
            size_hint_y: 0.6
            allow_stretch: True
            
        Label:
            id: right_base
            text: ""
            size_hint_y: 0.1
            font_size: '22sp'
            bold: True
            color: (1, 0.85, 0.4, 1)

    # 5. ฉากตัวละครต่อสู้ (ซ่อนไว้ก่อน และมีขนาดใหญ่เต็มหน้าจอ)
    PixelImage:
        id: fighter_left
        size_hint: 1.0, 1.0
        pos_hint: {'x': -0.11, 'y': 0}
        allow_stretch: True
        opacity: 0
        
    FlippedPixelImage:
        id: fighter_right
        size_hint: 1.0, 1.0
        pos_hint: {'right': 1.07, 'y': 0}
        allow_stretch: True
        opacity: 0
'''
Builder.load_string(KV)

class CrashOverlay(FloatLayout):
    def __init__(self, attacker, defender, start_pos, end_pos, a_faction, d_faction, get_img_path_func, on_finish, on_cancel, game_mode="PVP", **kwargs):
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(**kwargs)
        
        self.attacker, self.defender = attacker, defender
        self.start_pos, self.end_pos = start_pos, end_pos
        self.a_faction, self.d_faction = a_faction, d_faction
        self.on_finish = on_finish
        self.on_cancel = on_cancel
        self.game_mode = game_mode
        self.crash_stagger_count = 0

        # พื้นหลังทับกระดานหลักให้มืดลงนิดหน่อย (เพื่อให้เน้นหน้าจอ Crash)
        with self.canvas.before:
            Color(0.12, 0.08, 0.08, 0.98)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # จัดเตรียมข้อมูล Base Point
        if self.game_mode == "Divide_Conquer":
            self.a_base = getattr(self.attacker, 'base_atk', getattr(self.attacker, 'base_points', 5))
            self.d_base = getattr(self.defender, 'base_def', getattr(self.defender, 'base_points', 5))
            self.ids.left_base.text = f"Base ATK: {self.a_base}"
            self.ids.right_base.text = f"Base DEF: {self.d_base}"
        else:
            self.a_base = getattr(self.attacker, 'base_points', 5)
            self.d_base = getattr(self.defender, 'base_points', 5)
            self.ids.left_base.text = f"Base PTS: {self.a_base}"
            self.ids.right_base.text = f"Base PTS: {self.d_base}"

        self.ids.left_total.text = f"{self.a_base}"
        self.ids.right_total.text = f"{self.d_base}"
        self.ids.left_total.color = (1, 1, 1, 1)
        self.ids.right_total.color = (1, 1, 1, 1)

        # Portrait images — use safe helper so missing upgrade folders
        # never produce an "[ERROR] [Image] Not found" log line.
        a_folder = self._get_level_folder(self.attacker, self.a_faction)
        a_name = self._get_piece_filename(self.attacker)
        self.ids.left_char.source = safe_char_crash_path(self.attacker, self.a_faction)

        d_folder = self._get_level_folder(self.defender, self.d_faction)
        d_name = self._get_piece_filename(self.defender)
        self.ids.right_char.source = safe_char_crash_path(self.defender, self.d_faction)

        # ข้ามปุ่มและเริ่มทำงานทันทีหลังจากโหลด UI เสร็จเล็กน้อย
        Clock.schedule_once(self.start_crash_sequence, 0.4)

    def _update_bg(self, instance, value):
        self.bg_rect.pos, self.bg_rect.size = instance.pos, instance.size

    def _get_level_folder(self, piece, faction):
        lvl = getattr(piece, 'upgrade_level', 0)
        path = getattr(piece, 'upgrade_path', 'standard')
        
        if lvl == 0: return "1base"
        
        # Fallback: บังคับให้โจร (red) ใช้ภาพ 2upATK เสมอถ้าอัปเกรดเกิน
        if faction == 'red' and lvl >= 1:
            return "2upATK"
            
        if path == 'standard': return "2upATK" if lvl == 1 else "3upDEF"
        if path == 'special': return "4up_rehidden" if lvl == 1 else "5up_reroll_ATK_DEF"
        return "1base"

    def _get_piece_filename(self, piece):
        p_name = piece.__class__.__name__.lower()
        if getattr(piece, 'name', '') == 'Prince': return 'prince'
        if p_name in ['pawn', 'hastati', 'levies']:
            num = getattr(piece, 'variant', 1)
            return f"{p_name}{num}"
        return p_name

    def start_crash_sequence(self, *args):
        # เช็คไอเทมบล็อกดาเมจ
        if getattr(self.defender, 'item', None) and self.defender.item.id == 4:
            self.on_finish(self.start_pos, self.end_pos, "blocked")
            return

        # เริ่มอนิเมชั่นเลื่อนฉากหลัง
        anim_bg1 = Animation(pos_hint={'right': 1.0, 'y': 0}, duration=0.8, t='out_quad')
        anim_bg2 = Animation(pos_hint={'x': 0.04, 'y': 0}, duration=0.8, t='out_quad')
        
        anim_bg1.bind(on_complete=self.slide_ui_in)
        anim_bg1.start(self.ids.bg1)
        anim_bg2.start(self.ids.bg2)

    def slide_ui_in(self, *args):
        # เริ่มอนิเมชั่นเลื่อน UI ของตัวละครและค่าพลังเข้ามา
        anim_left = Animation(pos_hint={'x': 0.05, 'center_y': 0.5}, opacity=1, duration=1.2, t='out_cubic')
        anim_right = Animation(pos_hint={'right': 0.95, 'center_y': 0.5}, opacity=1, duration=1.2, t='out_cubic')
        
        anim_left.bind(on_complete=self.setup_coins_and_toss)
        anim_left.start(self.ids.left_ui)
        anim_right.start(self.ids.right_ui)

    def setup_coins_and_toss(self, *args):
        self.ids.status_lbl.opacity = 0
        
        a_coins = getattr(self.attacker, 'coins', 3)
        d_coins = getattr(self.defender, 'coins', 3)

        if getattr(self.defender, 'item', None) and self.defender.item.id == 8: a_coins = max(0, a_coins - 1)
        if getattr(self.attacker, 'item', None) and self.attacker.item.id == 8: d_coins = max(0, d_coins - 1)
        if getattr(self.defender, 'item', None) and self.defender.item.id == 2: a_coins = 0

        self.a_final_total, self.a_results = calculate_total_points(self.a_base, a_coins, self.a_faction)
        self.d_final_total, self.d_results = calculate_total_points(self.d_base, d_coins, self.d_faction)

        self.ids.left_total.text = f"{self.a_base}"
        self.ids.right_total.text = f"{self.d_base}"

        self.ids.left_coins.clear_widgets()
        self.ids.right_coins.clear_widgets()
        self.a_coin_widgets = []
        self.d_coin_widgets = []

        # สร้างเหรียญว่างรอเปิด
        for _ in range(a_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(dp(35), dp(35)))
            self.a_coin_widgets.append(img)
            self.ids.left_coins.add_widget(img)

        for _ in range(d_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(dp(35), dp(35)))
            self.d_coin_widgets.append(img)
            self.ids.right_coins.add_widget(img)

        def get_pt(res_str, faction):
            if "Green" in res_str: return 100
            if "Cyan" in res_str: return 10
            if "Purple" in res_str: return 6
            if "Orange" in res_str: return 4
            if "Blue" in res_str: return 3
            if "Red" in res_str: return 2
            if "Yellow" in res_str: return 1
            if "Tails" in res_str and faction == "the deep anomaly": return -3
            return 0

        self.a_pts_array = [get_pt(r, self.a_faction) for r in self.a_results]
        self.d_pts_array = [get_pt(r, self.d_faction) for r in self.d_results]

        self.anim_state = {
            'side': 'atk', 'coin_idx': 0, 'ticks': 0, 'max_ticks': 10,
            'a_current_total': self.a_base, 'd_current_total': self.d_base,
            'a_heads': 0, 'd_heads': 0,
            'a_demon_minus': 0, 'd_demon_minus': 0 
        }
        
        self.spin_event = Clock.schedule_interval(self.animate_coin_step, 0.08)

    def _get_coin_img(self, res_str, faction):
        mapping = {"Green": "coin9", "Cyan": "coin8", "Purple": "coin7", "Orange": "coin6", "Blue": "coin5", "Red": "coin4", "Yellow": "coin3"}
        for key, val in mapping.items():
            if key in res_str: return f"assets/coin/{val}.png"
        if "Tails" in res_str: return "assets/coin/coin1.png" if faction == "the deep anomaly" else "assets/coin/coin2.png"
        return "assets/coin/coin10.png"

    def animate_coin_step(self, dt):
        s = self.anim_state
        side = s['side']
        if side == 'atk': pts, res, fac, widgets, lbl, key = self.a_pts_array, self.a_results, self.a_faction, self.a_coin_widgets, self.ids.left_total, 'a_current_total'
        else: pts, res, fac, widgets, lbl, key = self.d_pts_array, self.d_results, self.d_faction, self.d_coin_widgets, self.ids.right_total, 'd_current_total'
        
        if s['coin_idx'] >= len(pts):
            if side == 'atk': s['side'], s['coin_idx'], s['ticks'] = 'def', 0, 0
            else: 
                self.spin_event.cancel()
                self.evaluate_winner()
            return
            
        s['ticks'] += 1
        if s['coin_idx'] < len(widgets):
            w = widgets[s['coin_idx']]
            w.opacity = 1.0 if (s['ticks'] % 4) < 2 else 0.3
            
            if s['ticks'] == 1:
                App.get_running_app().play_coin_sound()
            
            if s['ticks'] >= s['max_ticks']:
                w.opacity = 1.0
                w.source = self._get_coin_img(res[s['coin_idx']], fac)
                
                import time
                if not hasattr(self, 'last_coin_sound_time'): 
                    self.last_coin_sound_time = 0
                if time.time() - self.last_coin_sound_time > 0.08:
                    App.get_running_app().play_coin_sound()
                    self.last_coin_sound_time = time.time()
                    
                s[key] += pts[s['coin_idx']]
                
                heads_key = 'a_heads' if side == 'atk' else 'd_heads'
                demon_key = 'a_demon_minus' if side == 'atk' else 'd_demon_minus'

                if "Heads" in res[s['coin_idx']]:
                    s[heads_key] += 1
                    if fac == "the ancient runes":
                        if s[heads_key] == 3: s[key] += 3
                        elif s[heads_key] == 6: s[key] += 3
                elif "Tails" in res[s['coin_idx']] and fac == "the deep anomaly":
                    s[demon_key] += 1
                    demon_count = s[demon_key]
                    
                    # ลอจิกใหม่ของ Demon: คู่ = บวก / คี่ = ติดลบ
                    if demon_count % 2 == 0:
                        # ออกก้อยเลขคู่ (2, 4, 6, ...) พลิกผลลัพธ์จากลบให้กลายเป็นบวก
                        # ชดเชยค่าที่ติดลบไปในตาก่อนหน้า และบวกค่าของตาปัจจุบัน
                        s[key] += (demon_count * 6)
                    else:
                        # ออกก้อยเลขคี่ตั้งแต่ 3 ขึ้นไป (3, 5, 7, ...) ดึงผลลัพธ์กลับไปติดลบตามเดิม
                        if demon_count > 1:
                            s[key] -= ((demon_count - 1) * 6)
                            
                lbl.text = f"{s[key]}"
                s['coin_idx'] += 1
                s['ticks'] = 0
        else: 
            s['coin_idx'] += 1
            s['ticks'] = 0

        # ใส่สีตัวหนังสือแสดงคนนำแบบ Real-time ระหว่างทอย
        a_curr = s['a_current_total']
        d_curr = s['d_current_total']
        if a_curr > d_curr:
            self.ids.left_total.color = (0, 1, 0, 1)
            self.ids.right_total.color = (1, 1, 1, 1)
        elif d_curr > a_curr:
            self.ids.left_total.color = (1, 1, 1, 1)
            self.ids.right_total.color = (0, 1, 0, 1)
        else:
            self.ids.left_total.color = (1, 1, 1, 1)
            self.ids.right_total.color = (1, 1, 1, 1)

    def evaluate_winner(self):
        a_tot, d_tot = self.anim_state['a_current_total'], self.anim_state['d_current_total']
        lbl = self.ids.status_lbl
        lbl.opacity = 1
        
        # ใส่สีสรุปผลสุดท้าย (เขียว = ชนะ, แดง = แพ้, เหลือง = เสมอ)
        if a_tot > d_tot:
            lbl.text = "BREAKING!"
            lbl.color = (0, 0.8, 0, 1)
            self.ids.left_total.color = (0, 1, 0, 1)
            self.ids.right_total.color = (1, 0, 0, 1)
            Clock.schedule_once(lambda dt: self.prepare_attack("left"), 1.2)
            
        elif a_tot == d_tot:
            lbl.text = "DRAW!"
            lbl.color = (1, 1, 0, 1)
            self.ids.left_total.color = (1, 1, 0, 1)
            self.ids.right_total.color = (1, 1, 0, 1)
            App.get_running_app().play_draw_sound()
            Clock.schedule_once(lambda dt: self.setup_coins_and_toss(), 1.2)
            
        else:
            self.crash_stagger_count += 1
            if self.crash_stagger_count < 2:
                lbl.text = "STAGGER!"
                lbl.color = (1, 0.5, 0, 1)
                Clock.schedule_once(lambda dt: self.setup_coins_and_toss(), 1.2)
            else:
                lbl.text = "DISTORTION!"
                lbl.color = (1, 0, 0, 1)
                self.ids.left_total.color = (1, 0, 0, 1)
                self.ids.right_total.color = (0, 1, 0, 1)
                App.get_running_app().play_distortion_sound()
                Clock.schedule_once(lambda dt: self.prepare_attack("right"), 1.2)

    def prepare_attack(self, winner_side):
        self.winner_side = winner_side
        self.ids.status_lbl.opacity = 0
        
        # ปิดหน้าต่าง UI ด้านข้างทิ้งไป
        self.ids.left_ui.opacity = 0
        self.ids.right_ui.opacity = 0
        
        # จัดเตรียมภาพยืนนิ่ง (Frame 1) ให้ทั้งคู่แสดงขึ้นมาก่อนเพื่อป้องกันภาพแหว่ง
        a_folder = self._get_level_folder(self.attacker, self.a_faction)
        a_name = self._get_piece_filename(self.attacker)
        a_base_name = self.attacker.__class__.__name__.lower()
        if getattr(self.attacker, 'name', '') == 'Prince': a_base_name = 'prince'
        
        d_folder = self._get_level_folder(self.defender, self.d_faction)
        d_name = self._get_piece_filename(self.defender)
        d_base_name = self.defender.__class__.__name__.lower()
        if getattr(self.defender, 'name', '') == 'Prince': d_base_name = 'prince'
        
        self.ids.fighter_left.source = f'assets/animation/{self.a_faction}/{a_folder}/{a_name}/{a_base_name}1.png'
        self.ids.fighter_right.source = f'assets/animation/{self.d_faction}/{d_folder}/{d_name}/{d_base_name}1.png'
        
        # เปิดให้เห็นตัวละครต่อสู้แบบเต็มหน้าจอ (แสดงทั้งสองคนรอไว้เลย)
        self.ids.fighter_left.opacity = 1
        self.ids.fighter_right.opacity = 1

        # คำนวณหา Frame สูงสุดตามคลาสตัวละคร (แก้บัค Not Found)
        winner_piece = self.attacker if winner_side == 'left' else self.defender
        base_name = winner_piece.__class__.__name__.lower()
        if base_name in ['pawn', 'hastati', 'levies']:
            self.max_attack_frames = 5
        else:
            self.max_attack_frames = 7

        # ดึงตัวผู้ชนะมาไว้ Layer หน้าสุด จะได้โจมตีทับตัวที่แพ้
        winner_widget = self.ids.fighter_left if winner_side == 'left' else self.ids.fighter_right
        self.remove_widget(winner_widget)
        self.add_widget(winner_widget)
        
        self.attack_frame = 1
        Clock.schedule_interval(self.play_attack_anim, 1.0 / 6.0)

    def play_attack_anim(self, dt):
        if self.attack_frame <= self.max_attack_frames:
            if self.winner_side == 'left':
                piece = self.attacker
                faction = self.a_faction
                img_widget = self.ids.fighter_left
            else:
                piece = self.defender
                faction = self.d_faction
                img_widget = self.ids.fighter_right
                
            folder = self._get_level_folder(piece, faction)
            name = self._get_piece_filename(piece) # e.g., pawn3
            
            # ดึงชื่อ Base Class มาเป็นคำนำหน้าไฟล์รูปเฟรม (แก้บัค Not found)
            base_name = piece.__class__.__name__.lower()
            if getattr(piece, 'name', '') == 'Prince':
                base_name = 'prince'
                
            img_widget.source = f'assets/animation/{faction}/{folder}/{name}/{base_name}{self.attack_frame}.png'
            self.attack_frame += 1
        else:
            Clock.unschedule(self.play_attack_anim)
            Clock.schedule_once(self.fade_loser, 0.5)

    def fade_loser(self, dt):
        loser_widget = self.ids.fighter_right if self.winner_side == 'left' else self.ids.fighter_left
        anim = Animation(opacity=0, duration=1.0)
        anim.bind(on_complete=self.finish_crash)
        anim.start(loser_widget)
        
    def finish_crash(self, *args):
        result = "won" if self.winner_side == 'left' else "died"
        self.on_finish(self.start_pos, self.end_pos, result)

    def force_cancel(self):
        if hasattr(self, 'spin_event') and self.spin_event: 
            self.spin_event.cancel()