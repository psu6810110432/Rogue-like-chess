# components/unit_card.py
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.app import App # นำเข้า App เพื่อเช็คโหมด

class UnitCard(ButtonBehavior, BoxLayout):
    def __init__(self, piece=None, img_path=None, **kwargs):
        text_to_show = kwargs.pop('text', '') 
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(orientation='vertical', padding=15, spacing=5, **kwargs)
        
        
        with self.canvas.before:
            self.bg_color = Color(0.1, 0.1, 0.12, 1) 
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        if piece is None:
            lbl = Label(text=text_to_show, color=(1, 1, 1, 1), font_size='20sp', markup=True, halign='center')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)
            return
            
        app = App.get_running_app()
        is_dnc_mode = getattr(app, 'sub_mode', 'Classic') == 'Divide_Conquer'
            
        # ชื่อตัวละคร
        self.add_widget(Label(text=piece.__class__.__name__.upper(), bold=True, font_size='22sp', color=(1,1,1,1), size_hint_y=0.15))
        
        # ---------------------------------------------------------
        # ส่วนแสดงรูปภาพหมากและค่า Status พื้นฐาน (ตรงกลาง)
        # ---------------------------------------------------------
        mid = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.3)
        piece_img = Image(source=img_path, size_hint_x=0.4)
        piece_img.bind(texture=self._set_nearest_filter)
        mid.add_widget(piece_img)
        
        # กล่องสำหรับใส่ข้อมูลค่า Status (แทนที่ตัวหนังสือเดิมด้วย Icon)
        status_box = BoxLayout(orientation='vertical', spacing=2, size_hint_x=0.6)
        
        if is_dnc_mode:
            # โหมด Divide and Conquer: แสดง ATK, DEF, Coins
            atk_row = BoxLayout(orientation='horizontal', spacing=5)
            atk_img = Image(source='assets/icon_effect/base_atk.png', size_hint_x=None, width=24)
            atk_img.bind(texture=self._set_nearest_filter)
            atk_row.add_widget(atk_img)
            atk_row.add_widget(Label(text=f"{getattr(piece, 'base_atk', getattr(piece, 'base_points', 5))}", font_size='18sp', halign='left', color=(1, 0.2, 0.2, 1)))
            status_box.add_widget(atk_row)
            
            def_row = BoxLayout(orientation='horizontal', spacing=5)
            def_img = Image(source='assets/icon_effect/base_def.png', size_hint_x=None, width=24)
            def_img.bind(texture=self._set_nearest_filter)
            def_row.add_widget(def_img)
            def_row.add_widget(Label(text=f"{getattr(piece, 'base_def', 0)}", font_size='18sp', halign='left', color=(0.2, 0.6, 1, 1)))
            status_box.add_widget(def_row)
        else:
            # โหมด Classic: แสดงเฉพาะ Point
            pts_row = BoxLayout(orientation='horizontal', spacing=5)
            pts_img = Image(source='assets/icon_effect/base_point.png', size_hint_x=None, width=24)
            pts_img.bind(texture=self._set_nearest_filter)
            pts_row.add_widget(pts_img)
            pts_row.add_widget(Label(text=f"{getattr(piece, 'base_points', 5)}", font_size='18sp', halign='left', color=(1, 0.8, 0.2, 1)))
            status_box.add_widget(pts_row)
            
        mid.add_widget(status_box)
        self.add_widget(mid)
        
        # ---------------------------------------------------------
        # ข้อมูลเหรียญ (Coins) และไอเทมสวมใส่
        # ---------------------------------------------------------
        stats_row = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=5)
        
        # แทนที่คำว่า Coins: ด้วย Icon base_coin
        coin_box = BoxLayout(orientation='horizontal', size_hint_x=0.5)
        coin_img = Image(source='assets/icon_effect/base_coin.png', size_hint_x=None, width=20)
        coin_img.bind(texture=self._set_nearest_filter)
        coin_box.add_widget(coin_img)
        coin_box.add_widget(Label(text=f"{getattr(piece, 'coins', 3)}", font_size='14sp', color=(0.7, 0.8, 1, 1), halign='left'))
        stats_row.add_widget(coin_box)
        
        p_item = getattr(piece, 'item', None)
        stats_row.add_widget(Label(text=f"Eqp: {p_item.name if p_item else 'None'}", font_size='13sp', color=(0.5, 0.5, 0.5, 1), size_hint_x=0.5))
        self.add_widget(stats_row)
        
        # คำอธิบายสกิลติดตัวพื้นฐาน
        desc = getattr(piece, 'passive_desc', 'No special ability')
        
        # คำอธิบาย Hidden Passive
        hidden_passive_text = ""
        hp_obj = getattr(piece, 'hidden_passive', None)
        if hp_obj:
            hp_info = hp_obj.get_passive_info()
            hp_type = hp_info.get('type')
            if hp_type:
                hp_desc = hp_info.get('description', '')
                hp_mod = hp_info.get('modifier', '')
                color_hex = "44FF44" if hp_type in ['buff1', 'buff2'] else "FF4444"
                hidden_passive_text = f"\n[color={color_hex}]Hidden Passive: {hp_desc} ({hp_mod})[/color]"

        full_desc = f"[i]{desc}[/i]{hidden_passive_text}"
        
        passive_lbl = Label(text=full_desc, font_size='13sp', color=(0.8, 0.9, 1, 1), size_hint_y=0.2, markup=True, halign='center', valign='top')
        passive_lbl.bind(size=passive_lbl.setter('text_size'))
        self.add_widget(passive_lbl)
        
        # ---------------------------------------------------------
        # Dynamic Stats with Icons (Menatarm, Hastati, Praetorian, Royal Guard)
        # ---------------------------------------------------------
        p_class = piece.__class__.__name__.lower()
        
        if p_class == 'menatarm' and hasattr(piece, 'charge_stacks'):
            # Menatarm: Charge Stacks with charge.png icon
            charge_box = BoxLayout(orientation='horizontal', size_hint_y=0.05, spacing=5)
            charge_img = Image(source='assets/icon_effect/charge.png', size_hint_x=None, width=20)
            charge_img.bind(texture=self._set_nearest_filter)
            charge_box.add_widget(charge_img)
            charge_box.add_widget(Label(text=f"{piece.charge_stacks}/3", font_size='12sp', halign='center', color=(0, 1, 1, 1)))
            self.add_widget(charge_box)
            
        elif p_class == 'hastati' and hasattr(piece, 'def_stacks'):
            # Hastati: Defense Stacks with buff_def.png icon
            def_box = BoxLayout(orientation='horizontal', size_hint_y=0.05, spacing=5)
            def_img = Image(source='assets/icon_effect/buff_def.png', size_hint_x=None, width=20)
            def_img.bind(texture=self._set_nearest_filter)
            def_box.add_widget(def_img)
            def_box.add_widget(Label(text=f"{piece.def_stacks}/5", font_size='12sp', halign='center', color=(0, 1, 0, 1)))
            self.add_widget(def_box)
            
        elif p_class == 'praetorian' and hasattr(piece, 'active_buffs'):
            # Praetorian: Win Streaks with buff_atk_def.png icon
            win_box = BoxLayout(orientation='horizontal', size_hint_y=0.05, spacing=5)
            win_img = Image(source='assets/icon_effect/buff_atk_def.png', size_hint_x=None, width=20)
            win_img.bind(texture=self._set_nearest_filter)
            win_box.add_widget(win_img)
            win_box.add_widget(Label(text=f"{len(piece.active_buffs)}/5", font_size='12sp', halign='center', color=(1, 0.6, 0, 1)))
            self.add_widget(win_box)
            
        elif p_class == 'royalguard' and hasattr(piece, 'rg_atk_buffs'):
            # Royal Guard: Separate ATK and DEF buffs with respective icons
            rg_box = BoxLayout(orientation='horizontal', size_hint_y=0.05, spacing=10)
            
            # ATK buffs
            atk_buff_box = BoxLayout(orientation='horizontal', size_hint_x=None, width=60, spacing=3)
            atk_buff_img = Image(source='assets/icon_effect/buff_atk.png', size_hint_x=None, width=18)
            atk_buff_img.bind(texture=self._set_nearest_filter)
            atk_buff_box.add_widget(atk_buff_img)
            atk_buff_box.add_widget(Label(text=f"{piece.rg_atk_buffs}", font_size='11sp', halign='left', color=(1, 0.2, 0.2, 1)))
            rg_box.add_widget(atk_buff_box)
            
            # DEF buffs
            def_buff_box = BoxLayout(orientation='horizontal', size_hint_x=None, width=60, spacing=3)
            def_buff_img = Image(source='assets/icon_effect/buff_def.png', size_hint_x=None, width=18)
            def_buff_img.bind(texture=self._set_nearest_filter)
            def_buff_box.add_widget(def_buff_img)
            def_buff_box.add_widget(Label(text=f"{piece.rg_def_buffs}", font_size='11sp', halign='left', color=(0.2, 0.6, 1, 1)))
            rg_box.add_widget(def_buff_box)
            
            rg_box.add_widget(Label(text=f"({piece.rg_atk_buffs + piece.rg_def_buffs}/8)", font_size='10sp', halign='center', color=(1, 0.7, 1, 1)))
            self.add_widget(rg_box)

    def _set_nearest_filter(self, widget, texture):
        """Set texture mag_filter to nearest for pixel-perfect rendering"""
        if texture:
            texture.mag_filter = 'nearest'

    def _update_bg(self, instance, value):
        self.bg_rect.pos, self.bg_rect.size = instance.pos, instance.size

    def set_selected(self, is_selected):
        self.bg_color.rgba = (0.2, 0.45, 0.2, 1) if is_selected else (0.1, 0.1, 0.12, 1)