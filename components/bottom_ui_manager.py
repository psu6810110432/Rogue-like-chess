# components/bottom_ui_manager.py
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.app import App
from components.piece_card import PieceCard

class BottomUIManager:
    def __init__(self, gameplay_screen):
        self.screen = gameplay_screen

    def open_bag_popup(self, instance):
        current_color = self.screen.game.current_turn
        inv = getattr(self.screen.game, f'inventory_{current_color}', [])
        
        content = BoxLayout(orientation='horizontal', spacing=dp(10), padding=dp(10))
        if not inv:
            content.add_widget(Label(text="Your bag is empty.", font_size='18sp'))
        else:
            for item in inv:
                ibox = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(100))
                
                # ✨ เปลี่ยนจากแค่โชว์รูป เป็นปุ่มให้กดเลือกไอเทมได้เลย
                btn = Button(background_normal=item.image_path, size_hint_y=0.7)
                btn.bind(on_release=lambda x, i=item: self._select_item_from_bag(i, pop))
                
                ibox.add_widget(btn)
                ibox.add_widget(Label(text=item.name, font_size='12sp', size_hint_y=0.3, halign='center'))
                content.add_widget(ibox)
                
        close_btn = Button(text="Close Bag", size_hint_y=0.2, background_color=(0.3, 0.3, 0.3, 1))
        
        main_box = BoxLayout(orientation='vertical', spacing=dp(10))
        main_box.add_widget(content)
        main_box.add_widget(close_btn)
        
        pop = Popup(title=f"🎒 {current_color.upper()}'S INVENTORY BAG", content=main_box, size_hint=(0.6, 0.4))
        close_btn.bind(on_release=pop.dismiss)
        pop.open()

    def _select_item_from_bag(self, item, popup):
        popup.dismiss()
        App.get_running_app().play_click_sound()
        
        # ✨ บันทึกไอเทมที่ผู้เล่นเลือกลงในระบบ
        self.screen.selected_item = item
        
        # เคลียร์เมนูเดินทิ้ง (ถ้าเปิดค้างไว้)
        if hasattr(self.screen, 'action_menu_layout'):
            self.screen.action_menu_layout.clear_widgets()
            
        # เปลี่ยนข้อความด้านบนเพื่อบอกให้ผู้เล่นรู้ว่าต้องทำอะไรต่อ
        self.screen.info_label.text = f"[color=00ffff]SELECT A CARD TO EQUIP: {item.name}[/color]"


    def show_equip_popup(self, piece, card_instance, r, c):
        current_color = self.screen.game.current_turn
        inv = getattr(self.screen.game, f'inventory_{current_color}', [])
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=f"Would you like to equip an item to {piece.__class__.__name__}?", size_hint_y=0.2, font_size='16sp'))
        
        item_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.5)
        
        pop = Popup(title="✨ EQUIP ITEM", content=content, size_hint=(0.6, 0.45), auto_dismiss=False)
        
        for item in inv:
            btn = Button(background_normal=item.image_path)
            btn.bind(on_release=lambda x, i=item: self._equip_item_from_popup(i, piece, pop, r, c))
            item_box.add_widget(btn)
        content.add_widget(item_box)
        
        skip_btn = Button(text="Don't Equip (Just Move)", size_hint_y=0.3, background_color=(0.6, 0.2, 0.2, 1))
        skip_btn.bind(on_release=lambda x: self._skip_equip_from_popup(pop, r, c))
        content.add_widget(skip_btn)
        
        pop.open()

    def _equip_item_from_popup(self, item, piece, popup, r, c):
        popup.dismiss()
        App.get_running_app().play_click_sound()
        self.screen.controller.submit_item_use(item, piece, self.screen.game.current_turn)
        self.screen.update_hand_ui() 
        self.screen.show_piece_status(piece)
        self.screen.refresh_ui(self.screen.game.get_legal_moves((r, c)))
        # ✨ ใส่ไอเทมเสร็จ เรียกเมนูเป้าหมายขึ้นมาเลย
        self.show_move_options(piece, r, c)

    def _skip_equip_from_popup(self, popup, r, c):
        popup.dismiss()
        App.get_running_app().play_click_sound()
        self.screen.refresh_ui(self.screen.game.get_legal_moves((r, c)))
        # ✨ ไม่ใส่ไอเทม ก็เรียกเมนูเป้าหมายขึ้นมาเช่นกัน
        piece = self.screen.game.board[r][c]
        self.show_move_options(piece, r, c)

    def on_card_selected(self, card_instance, r, c):
        App.get_running_app().play_click_sound()
        piece = card_instance.piece
        
        # 🟢 1. โหมดสวมใส่ไอเทม (ถ้าผู้เล่นเพิ่งไปกดไอเทมมาจากกระเป๋า)
        if getattr(self.screen, 'selected_item', None):
            item = self.screen.selected_item
            # เช็คว่าตัวนี้รับไอเทมได้ไหม และ ยังไม่มีไอเทมใช่ไหม
            can_equip = not getattr(piece, 'cannot_get_items', False) and getattr(piece, 'item', None) is None
            
            if can_equip:
                # สวมใส่สำเร็จ!
                self.screen.controller.submit_item_use(item, piece, self.screen.game.current_turn)
                self.screen.selected_item = None # ล้างไอเทมในมือทิ้ง
                self.screen.update_hand_ui() 
                self.screen.show_piece_status(piece)
                self.screen.refresh_ui()
            else:
                # สวมใส่ไม่ได้ (มีของอยู่แล้ว หรือห้ามใส่) -> ให้ยกเลิกการถือไอเทมไปเลย
                self.screen.selected_item = None
                self.screen.refresh_ui()
                
            return # จบการทำงาน ไม่ต้องไปเปิดหน้าเดินต่อ

        # 🟢 2. โหมดคลิกเพื่อเดินหมาก (ปกติ)
        if hasattr(self.screen, 'action_menu_layout'):
            self.screen.action_menu_layout.clear_widgets()
        
        # เคลียร์แสงสว่างของการ์ดใบอื่นที่ไม่ได้เลือก
        for child in self.screen.hand_layout.children:
            if isinstance(child, PieceCard) and child != card_instance:
                child.deselect()
                
        self.screen.selected = (r, c)
        self.screen.show_piece_status(piece)
        
        # ✨ เพิ่ม 2 บรรทัดนี้ เพื่อสั่งกระดาน 3D ให้วาดแสงสีเขียวและสีฟ้า!
        legal_moves = self.screen.game.get_legal_moves((r, c))
        self.screen.refresh_ui(legal_moves)
        
        # โชว์เมนูเลือกทิศทางการเดิน
        self.show_move_options(piece, r, c)

    # ==========================================
    # ระบบ Action Menu (ปุ่มแกนเดิน & เป้าหมาย)
    # ==========================================
    def categorize_moves(self, r, c, moves):
        groups = {"Vertical": [], "Horizontal": [], "Diagonal": [], "Knight Jump": [], "Others": []}
        for tr, tc in moves:
            if tr == r: groups["Horizontal"].append((tr, tc))
            elif tc == c: groups["Vertical"].append((tr, tc))
            elif abs(tr - r) == abs(tc - c): groups["Diagonal"].append((tr, tc))
            elif (abs(tr - r) == 2 and abs(tc - c) == 1) or (abs(tr - r) == 1 and abs(tc - c) == 2): groups["Knight Jump"].append((tr, tc))
            else: groups["Others"].append((tr, tc))
        return {k: v for k, v in groups.items() if v}

    def show_move_options(self, piece, r, c):
        if not hasattr(self.screen, 'action_menu_layout'): return
        self.screen.action_menu_layout.clear_widgets()
        
        legal_moves = self.screen.game.get_legal_moves((r, c))
        if not legal_moves:
            self.screen.action_menu_layout.add_widget(Label(text="[color=ff3333][b]No Valid Moves[/b][/color]", markup=True))
            return
            
        name = piece.__class__.__name__.lower()
        # ถ้าเป็นหมากเดินง่าย (Pawn, King) จะขึ้นพิกัดปลายทางให้เลยไม่ต้องผ่านกลุ่ม
        if name in ['pawn', 'king', 'levies']:
            self.show_targets(r, c, legal_moves)
        else:
            groups = self.categorize_moves(r, c, legal_moves)
            if len(groups) > 1:
                for group_name, moves in groups.items():
                    btn = Button(
                        text=f"[b]{group_name}[/b]", markup=True, 
                        size_hint=(None, 1), width=dp(120), 
                        background_color=(0.8, 0.6, 0.2, 1)
                    )
                    btn.bind(on_release=lambda inst, m=moves: self.show_targets(r, c, m))
                    self.screen.action_menu_layout.add_widget(btn)
            else:
                self.show_targets(r, c, legal_moves)

    def show_targets(self, r, c, target_moves):
        self.screen.action_menu_layout.clear_widgets()
        for tr, tc in target_moves:
            # แปลงพิกัดเป็นแบบสากล เช่น B2, A3
            notation = f"{chr(65+tc)}{tr+1}"
            btn = Button(
                text=f"[b]{notation}[/b]", markup=True, 
                size_hint=(None, 1), width=dp(60), 
                background_color=(0.2, 0.6, 0.8, 1)
            )
            # เมื่อกดยืนยันปลายทาง
            btn.bind(on_release=lambda inst, target_r=tr, target_c=tc: self.execute_move(target_r, target_c))
            self.screen.action_menu_layout.add_widget(btn)

    def execute_move(self, target_r, target_c):
        self.screen.action_menu_layout.clear_widgets()
        
        # ปั้นพารามิเตอร์จำลองหลอกระบบเก่า ว่ามีการ "คลิกที่ช่องปลายทาง"
        class DummyInstance:
            def __init__(self, row, col):
                self.row = row
                self.col = col
                
        # ส่งค่าให้ระบบดั้งเดิมจัดการเดิน กิน หรือโปรโมทได้ตามปกติเลย 100%
        self.screen.on_square_tap(DummyInstance(target_r, target_c))