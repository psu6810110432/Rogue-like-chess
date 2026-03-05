# components/crash_overlay.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from logic.crash_logic import calculate_total_points
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.core.audio import SoundLoader

class CrashOverlay(BoxLayout):
    def __init__(self, attacker, defender, start_pos, end_pos, a_faction, d_faction, get_img_path_func, on_finish, on_cancel, **kwargs):
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(orientation='vertical', padding=5, spacing=5, **kwargs)
        
        self.attacker, self.defender = attacker, defender
        self.start_pos, self.end_pos = start_pos, end_pos
        self.a_faction, self.d_faction = a_faction, d_faction
        self.get_img_path_func = get_img_path_func
        self.on_finish = on_finish
        self.on_cancel = on_cancel
        self.crash_stagger_count = 0
        
        with self.canvas.before:
            Color(0.15, 0.05, 0.05, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self._setup_ui()

    def _update_bg(self, instance, value):
        self.bg_rect.pos, self.bg_rect.size = instance.pos, instance.size

    def _setup_ui(self):
        self.add_widget(Label(text="CRASH!", bold=True, font_size='28sp', color=(1, 0.2, 0.2, 1), size_hint_y=0.15))
        vs_box = BoxLayout(orientation='horizontal', size_hint_y=0.55)
        
        # ATK
        atk = BoxLayout(orientation='vertical')
        atk.add_widget(Image(source=self.get_img_path_func(self.attacker), size_hint_y=0.4))
        self.a_coins_layout = GridLayout(cols=3, spacing=2, size_hint_y=0.3)
        atk.add_widget(self.a_coins_layout)
        self.a_val_lbl = Label(text=f"ATK: {getattr(self.attacker, 'base_points', 5)}", bold=True, size_hint_y=0.3)
        atk.add_widget(self.a_val_lbl)
        vs_box.add_widget(atk)
        
        vs_box.add_widget(Label(text="VS", size_hint_x=0.2, bold=True))
        
        # DEF
        dfn = BoxLayout(orientation='vertical')
        dfn.add_widget(Image(source=self.get_img_path_func(self.defender), size_hint_y=0.4))
        self.d_coins_layout = GridLayout(cols=3, spacing=2, size_hint_y=0.3)
        dfn.add_widget(self.d_coins_layout)
        self.d_val_lbl = Label(text=f"DEF: {getattr(self.defender, 'base_points', 5)}", bold=True, size_hint_y=0.3)
        dfn.add_widget(self.d_val_lbl)
        vs_box.add_widget(dfn)
        
        self.add_widget(vs_box)
        
        self.crash_btn = Button(text="START!", bold=True, font_size='20sp', size_hint_y=0.3, background_color=(0.8, 0.2, 0.2, 1))
        self.crash_btn.bind(on_release=self.start_crash_animation)
        self.add_widget(self.crash_btn)

    # ✨ FIX: นำระบบแอนิเมชันทอยเหรียญทั้งหมดกลับมา
    def start_crash_animation(self, *args):
        self.crash_btn.disabled = True
        if getattr(self.defender, 'item', None) and self.defender.item.id == 4:
            self.on_finish(self.start_pos, self.end_pos, "blocked")
            return 

        a_base = getattr(self.attacker, 'base_points', 5)
        a_coins = getattr(self.attacker, 'coins', 3)
        d_base = getattr(self.defender, 'base_points', 5)
        d_coins = getattr(self.defender, 'coins', 3)

        if getattr(self.defender, 'item', None) and self.defender.item.id == 8: a_coins = max(0, a_coins - 1)
        if getattr(self.attacker, 'item', None) and self.attacker.item.id == 8: d_coins = max(0, d_coins - 1)
        if getattr(self.defender, 'item', None) and self.defender.item.id == 2: a_coins = 0

        self.a_final_total, self.a_results = calculate_total_points(a_base, a_coins, self.a_faction)
        self.d_final_total, self.d_results = calculate_total_points(d_base, d_coins, self.d_faction)

        self.a_val_lbl.text = f"{a_base}"
        self.d_val_lbl.text = f"{d_base}"

        self.a_coins_layout.clear_widgets()
        self.d_coins_layout.clear_widgets()
        self.a_coin_widgets = []
        self.d_coin_widgets = []

        for _ in range(a_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(20, 20))
            self.a_coin_widgets.append(img)
            self.a_coins_layout.add_widget(img)

        for _ in range(d_coins):
            img = Image(source='assets/coin/coin10.png', size_hint=(None, None), size=(20, 20))
            self.d_coin_widgets.append(img)
            self.d_coins_layout.add_widget(img)

        def get_pt(res_str, faction):
            if "Green" in res_str: return 100
            if "Cyan" in res_str: return 10
            if "Purple" in res_str: return 6
            if "Orange" in res_str: return 4
            if "Blue" in res_str: return 3
            if "Red" in res_str: return 2
            if "Yellow" in res_str: return 1
            if "Tails" in res_str and faction == "demon": return -3
            return 0

        self.a_pts_array = [get_pt(r, self.a_faction) for r in self.a_results]
        self.d_pts_array = [get_pt(r, self.d_faction) for r in self.d_results]

        self.anim_state = {
            'side': 'atk', 'coin_idx': 0, 'ticks': 0, 'max_ticks': 10,
            'a_current_total': a_base, 'd_current_total': d_base,
            'a_heads': 0, 'd_heads': 0
        }
        self.spin_event = Clock.schedule_interval(self.animate_coin_step, 0.08)

    def _get_coin_img(self, res_str, faction):
        mapping = {"Green": "coin9", "Cyan": "coin8", "Purple": "coin7", "Orange": "coin6", "Blue": "coin5", "Red": "coin4", "Yellow": "coin3"}
        for key, val in mapping.items():
            if key in res_str: return f"assets/coin/{val}.png"
        if "Tails" in res_str: return "assets/coin/coin1.png" if faction == "demon" else "assets/coin/coin2.png"
        return "assets/coin/coin10.png"

    def animate_coin_step(self, dt):
        s = self.anim_state
        side = s['side']
        if side == 'atk': pts, res, fac, widgets, lbl, key = self.a_pts_array, self.a_results, self.a_faction, self.a_coin_widgets, self.a_val_lbl, 'a_current_total'
        else: pts, res, fac, widgets, lbl, key = self.d_pts_array, self.d_results, self.d_faction, self.d_coin_widgets, self.d_val_lbl, 'd_current_total'
        
        if s['coin_idx'] >= len(pts):
            if side == 'atk': s['side'], s['coin_idx'], s['ticks'] = 'def', 0, 0
            else: self.spin_event.cancel(); self.finish_crash_animation()
            return
            
        s['ticks'] += 1
        if s['coin_idx'] < len(widgets):
            w = widgets[s['coin_idx']]
            w.opacity = 1.0 if (s['ticks'] % 4) < 2 else 0.3
            
            # Play coin sound when coin starts spinning (first tick)
            if s['ticks'] == 1:
                App.get_running_app().play_coin_sound()
            
            if s['ticks'] >= s['max_ticks']:
                w.opacity = 1.0; w.source = self._get_coin_img(res[s['coin_idx']], fac)
                
                # 1. บวกแต้มหน้าเหรียญปกติ
                s[key] += pts[s['coin_idx']]
                
                # 2. ✨ FIX: ระบบนับจำนวนหัวและโบนัสเผ่า Heaven
                heads_key = 'a_heads' if side == 'atk' else 'd_heads'
                if "Heads" in res[s['coin_idx']]:
                    s[heads_key] += 1
                    if fac == "heaven":
                        if s[heads_key] == 3:  # ครบ 3 หัวแรก บวก 3 แต้ม
                            s[key] += 3
                        elif s[heads_key] == 6: # ครบ 6 หัว บวกอีก 3 แต้ม
                            s[key] += 3
                            
                # 3. อัปเดตตัวเลขขึ้นหน้าจอ
                lbl.text = f"{s[key]}"
                s['coin_idx'] += 1
                s['ticks'] = 0
        else: 
            s['coin_idx'] += 1
            s['ticks'] = 0

    def finish_crash_animation(self):
        a_tot, d_tot = self.anim_state['a_current_total'], self.anim_state['d_current_total']
        if a_tot > d_tot:
            self.crash_btn.text = "BREAKING!"
            self.crash_btn.font_size = '24sp'
            self.crash_btn.background_color = (0, 0.8, 0, 1)  # เขียว
            Clock.schedule_once(lambda dt: self.on_finish(self.start_pos, self.end_pos, "won"), 1.2)
        elif a_tot == d_tot:
            self.crash_btn.text = "DRAW!"
            self.crash_btn.font_size = '24sp'
            self.crash_btn.background_color = (1, 1, 0, 1)  # เหลือง
            App.get_running_app().play_draw_sound()
            Clock.schedule_once(lambda dt: self.start_crash_animation(), 1.2)
        else:
            self.crash_stagger_count += 1
            if self.crash_stagger_count < 2:
                self.crash_btn.text = "STAGGER!"
                self.crash_btn.font_size = '24sp'
                self.crash_btn.background_color = (1, 0.5, 0, 1)  # ส้ม
                Clock.schedule_once(lambda dt: self.start_crash_animation(), 1.2)
            else:
                self.crash_btn.text = "DISTORTION!"
                self.crash_btn.font_size = '24sp'
                self.crash_btn.background_color = (1, 0, 0, 1)  # แดง
                App.get_running_app().play_distortion_sound()
                Clock.schedule_once(lambda dt: self.on_finish(self.start_pos, self.end_pos, "died"), 1.2)

    def force_cancel(self):
        if hasattr(self, 'spin_event') and self.spin_event: self.spin_event.cancel()