# components/sidebar_ui.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
# ✨ นำเข้าปุ่มแบบ 3D จากหน้า Main Menu
from screens.main_menu import RoundedButton 

class SidebarUI(BoxLayout):
    # ✨ รับค่า game_mode เข้ามาเพื่อใช้เช็คว่าจะแสดงปุ่มอะไร
    def __init__(self, on_undo_callback, on_quit_callback, game_mode='Classic', **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        
        # 1. หัวข้อ Move History (✨ เปลี่ยนเป็นสีทอง #d4af37)
        title = Label(
            text="[b]Move History[/b]", 
            markup=True,
            color=(0.83, 0.68, 0.21, 1), 
            size_hint_y=None, 
            height=dp(30), 
            font_size='18sp'
        )
        self.add_widget(title)
        
        # 2. หัวตาราง (ล็อค 3 ช่องให้ตรงกันเป๊ะ)
        header_layout = GridLayout(cols=3, size_hint_y=None, height=dp(25))
        header_layout.add_widget(Label(text="[b]Turn[/b]", markup=True, color=(0.7, 0.8, 1, 1), size_hint_x=0.2))
        
        w_head = Label(text="[b]White[/b]", markup=True, color=(0.7, 0.8, 1, 1), size_hint_x=0.4, halign='left')
        w_head.bind(size=w_head.setter('text_size'))
        header_layout.add_widget(w_head)
        
        b_head = Label(text="[b]Black[/b]", markup=True, color=(0.7, 0.8, 1, 1), size_hint_x=0.4, halign='left')
        b_head.bind(size=b_head.setter('text_size'))
        header_layout.add_widget(b_head)
        
        self.add_widget(header_layout)
        
        # เส้นประใต้หัวตาราง
        self.add_widget(Label(text="-"*50, size_hint_y=None, height=dp(10), color=(0.4, 0.4, 0.4, 1)))
        
        # 3. พื้นที่ประวัติการเดิน (มี ScrollView)
        self.scroll = ScrollView(
            size_hint_y=1, 
            do_scroll_x=False,
            bar_width=dp(12), 
            bar_color=[0.6, 0.6, 0.6, 0.9], 
            bar_inactive_color=[0.4, 0.4, 0.4, 0.6],
            scroll_type=['bars', 'content'] 
        )
        
        self.history_wrapper = BoxLayout(orientation='vertical', size_hint_y=None)
        
        self.history_grid = GridLayout(cols=3, size_hint_y=None, spacing=[0, dp(5)])
        self.history_grid.bind(minimum_height=self.history_grid.setter('height'))
        
        def update_wrapper_height(*args):
            self.history_wrapper.height = max(self.history_grid.minimum_height, self.scroll.height)
            
        self.history_grid.bind(minimum_height=update_wrapper_height)
        self.scroll.bind(height=update_wrapper_height)
        
        self.history_wrapper.add_widget(self.history_grid)
        self.history_wrapper.add_widget(Widget()) 
        
        self.scroll.add_widget(self.history_wrapper)
        self.add_widget(self.scroll)
        
        # 4. โซนปุ่มกด (✨ สลับปุ่มตามโหมดเกม)
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(110), spacing=10, padding=[0, 10, 0, 0])
        
        if game_mode == 'Divide_Conquer':
            btn_layout.add_widget(Widget()) # ดันปุ่มลง
            retreat_btn = RoundedButton(text="Retreat", bold=True, font_size='18sp', normal_color=(0.8, 0.4, 0.1, 0.95))
            retreat_btn.bind(on_release=lambda x: on_quit_callback())
            btn_layout.add_widget(retreat_btn)
        else:
            undo_btn = RoundedButton(text="Undo Move", bold=True, font_size='18sp', normal_color=(0.55, 0.15, 0.15, 0.95))
            undo_btn.bind(on_release=lambda x: on_undo_callback())
            
            quit_btn = RoundedButton(text="Quit Match", bold=True, font_size='18sp', normal_color=(0.35, 0.05, 0.05, 0.95))
            quit_btn.bind(on_release=lambda x: on_quit_callback())
            
            btn_layout.add_widget(undo_btn)
            btn_layout.add_widget(quit_btn)
        
        self.add_widget(btn_layout)

    def update_history_text(self, text_list):
        self.history_grid.clear_widgets()
        
        if not isinstance(text_list, list): 
            return

        turn = 1
        for i in range(0, len(text_list), 2):
            white_move = text_list[i]
            black_move = text_list[i+1] if i+1 < len(text_list) else ""
            
            self.history_grid.add_widget(Label(text=f"{turn}.", size_hint_y=None, height=dp(24), size_hint_x=0.2, color=(0.8,0.8,0.8,1)))
            
            w_lbl = Label(text=white_move, size_hint_y=None, height=dp(24), size_hint_x=0.4, halign='left', shorten=True, shorten_from='right', color=(1,1,1,1))
            w_lbl.bind(size=w_lbl.setter('text_size'))
            self.history_grid.add_widget(w_lbl)
            
            b_lbl = Label(text=black_move, size_hint_y=None, height=dp(24), size_hint_x=0.4, halign='left', shorten=True, shorten_from='right', color=(0.7,0.7,0.7,1))
            b_lbl.bind(size=b_lbl.setter('text_size'))
            self.history_grid.add_widget(b_lbl)
            
            turn += 1
            
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)