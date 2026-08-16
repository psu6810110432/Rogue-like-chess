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
                ibox.add_widget(Image(source=item.image_path))
                ibox.add_widget(Label(text=item.name, font_size='12sp', size_hint_y=0.3, halign='center'))
                content.add_widget(ibox)
                
        close_btn = Button(text="Close Bag", size_hint_y=0.2, background_color=(0.3, 0.3, 0.3, 1))
        
        main_box = BoxLayout(orientation='vertical', spacing=dp(10))
        main_box.add_widget(content)
        main_box.add_widget(close_btn)
        
        pop = Popup(title=f"🎒 {current_color.upper()}'S INVENTORY BAG", content=main_box, size_hint=(0.6, 0.4))
        close_btn.bind(on_release=pop.dismiss)
        pop.open()

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
        
        # เคลียร์เมนูเป้าหมายเก่าทิ้งก่อน
        if hasattr(self.screen, 'action_menu_layout'):
            self.screen.action_menu_layout.clear_widgets()
        
        for child in self.screen.hand_layout.children:
            if isinstance(child, PieceCard) and child != card_instance:
                child.deselect()
                
        self.screen.selected = (r, c)
        self.screen.show_piece_status(card_instance.piece)
        
        piece = card_instance.piece
        current_color = self.screen.game.current_turn
        inv = getattr(self.screen.game, f'inventory_{current_color}', [])
        
        can_equip = not getattr(piece, 'cannot_get_items', False) and getattr(piece, 'item', None) is None
        
        if inv and can_equip:
            self.show_equip_popup(piece, card_instance, r, c)
        else:
            self.screen.refresh_ui(self.screen.game.get_legal_moves((r, c)))
            # ✨ เมื่อคลิกการ์ด (และไม่ต้องใส่ไอเทม) ให้โชว์เมนูเดิน
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
        # ถ้าเป็นพวกตัวเดินง่าย (Pawn, King) โชว์จุดเป้าหมายเลยไม่ต้องแยกแกน
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