# components/campaign_panel.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.animation import Animation

from components.campaign_cards import PieceCard, RecruitCard
from components.campaign_popups import ArmyStatusPopup
from logic.campaign_helpers import generate_piece

class CampaignArmyPanel(FloatLayout):
    def __init__(self, map_screen, app, **kwargs):
        super().__init__(size_hint=(0.85, None), height=dp(200), pos_hint={'x': 0.02, 'y': -0.5}, **kwargs) 
        self.map_screen = map_screen
        self.app = app
        self.current_node = None
        self.current_tab = 'army'
        self.is_upgrade_mode = False 

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 0.9)
            self.bg = RoundedRectangle(radius=[dp(12)])
            self.border_color = Color(0.5, 0.5, 0.5, 1)
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=2)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.header_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), pos_hint={'top': 1, 'x': 0}, padding=[dp(10), dp(5)])
        
        self.header_lbl = Label(text="ARMY HQ", bold=True, font_size='18sp', size_hint_x=0.3, halign='left')
        self.status_lbl = Label(text="", markup=True, size_hint_x=0.2, font_size='14sp')
        
        self.btn_tab_army = Button(text="[b]ARMY[/b]", markup=True, size_hint_x=0.15, background_color=(0.3, 0.5, 0.8, 1))
        self.btn_tab_army.bind(on_release=lambda x: self.switch_tab('army'))
        self.btn_tab_recruit = Button(text="[b]RECRUIT[/b]", markup=True, size_hint_x=0.15, background_color=(0.2, 0.2, 0.2, 1))
        self.btn_tab_recruit.bind(on_release=lambda x: self.switch_tab('recruit'))
        
        btn_close = Button(text="CLOSE", size_hint_x=0.1, background_color=(0.5, 0.2, 0.2, 1))
        btn_close.bind(on_release=self.close_panel)
        
        self.header_box.add_widget(self.header_lbl)
        self.header_box.add_widget(self.status_lbl)
        self.header_box.add_widget(self.btn_tab_army)
        self.header_box.add_widget(self.btn_tab_recruit)
        self.header_box.add_widget(btn_close)
        self.add_widget(self.header_box)

        self.content_scroll = ScrollView(size_hint=(0.7, 0.7), pos_hint={'x': 0.02, 'y': 0.05}, do_scroll_x=True, do_scroll_y=False)
        self.content_grid = GridLayout(rows=1, spacing=dp(8), size_hint_x=None, padding=dp(5))
        self.content_grid.bind(minimum_width=self.content_grid.setter('width'))
        self.content_scroll.add_widget(self.content_grid)
        self.add_widget(self.content_scroll)

        self.action_box = BoxLayout(orientation='vertical', size_hint=(0.25, 0.7), pos_hint={'right': 0.98, 'y': 0.05}, spacing=dp(5))
        
        self.btn_action = Button(text="[b]MARCH / ATTACK[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1), size_hint_y=0.6)
        self.btn_action.bind(on_release=self.execute_action)
        self.action_box.add_widget(self.btn_action)
        
        self.sub_action_box = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=0.4)
        
        self.btn_status = Button(text="[b]STATUS[/b]", markup=True, background_color=(0.2, 0.6, 0.8, 1))
        self.btn_status.bind(on_release=self.show_army_status)
        self.sub_action_box.add_widget(self.btn_status)
        
        self.btn_upgrade = Button(text="[b]UPGRADE[/b]", markup=True, background_color=(0.6, 0.2, 0.8, 1))
        self.btn_upgrade.bind(on_release=self.toggle_upgrade_mode)
        self.sub_action_box.add_widget(self.btn_upgrade)
        
        self.action_box.add_widget(self.sub_action_box)
        self.add_widget(self.action_box)
        self.piece_cards = []

    def _update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size
        self.border_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(12))

    def open_for_node(self, node):
        self.current_node = node
        self.header_lbl.text = f"{node.faction.upper()} {node.node_type.upper()}"
        self.is_upgrade_mode = False
        
        for n in self.map_screen.nodes_list:
            n.is_selected_node = (n == node)
            n.update_graphics()
        
        if node.faction == 'white': self.border_color.rgba = (0.9, 0.9, 0.9, 1)
        elif node.faction == 'black': self.border_color.rgba = (0.3, 0.3, 0.4, 1)
        
        self.switch_tab('army')
        Animation(pos_hint={'y': 0.02}, duration=0.3, t='out_quad').start(self)

    def close_panel(self, *args):
        self.app.play_click_sound()
        for n in self.map_screen.nodes_list:
            n.is_selected_node = False
            n.update_graphics()
        Animation(pos_hint={'y': -0.5}, duration=0.2).start(self)

    def toggle_upgrade_mode(self, instance):
        self.app.play_click_sound()
        self.is_upgrade_mode = not self.is_upgrade_mode
        
        if self.is_upgrade_mode:
            self.btn_upgrade.background_color = (0.8, 0.8, 0.2, 1)
            self.map_screen.status_lbl.text = f"[color=ffff00]UPGRADE MODE: Tax {self.app.tax_points.get(self.current_node.faction, 0)} | Select a unit to open Tech Tree.[/color]"
            
            for card in self.piece_cards:
                card.is_selected = False
                card.border_color.rgba = (0.3, 0.3, 0.35, 1)
                card.border_line.width = 1.5
        else:
            self.switch_tab('army')

    def show_army_status(self, instance):
        self.app.play_click_sound()
        if not self.current_node or not self.current_node.army_pieces: return
        pop = ArmyStatusPopup(self.current_node.army_pieces)
        pop.open()

    def switch_tab(self, tab_name):
        self.app.play_click_sound()
        self.current_tab = tab_name
        self.is_upgrade_mode = False
        self.content_grid.clear_widgets()
        self.piece_cards.clear()

        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False))
        heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
        heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
        total = len(self.current_node.army_pieces)
        max_cap = 16 if headers > 0 else 8

        if tab_name == 'army':
            self.btn_tab_army.background_color = (0.3, 0.5, 0.8, 1)
            self.btn_tab_recruit.background_color = (0.2, 0.2, 0.2, 1)
            
            lylt = getattr(self.current_node, 'loyalty', 100)
            color_lylt = '00ff00' if lylt > 60 else ('ffcc00' if lylt > 20 else 'ff0000')
            
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            fatigue_color = '00ff00' if fatigue == 0 else ('ffaa00' if fatigue < 6 else 'ff0000')
            self.status_lbl.text = f"Loyalty: [color={color_lylt}]{lylt}%[/color] | Cap: [b]{total}/{max_cap}[/b] | Fatigue: [color={fatigue_color}]{fatigue}/6[/color]"
            
            self.btn_action.text = "[b]MARCH / ATTACK[/b]"
            self.btn_action.background_color = (0.8, 0.2, 0.2, 1)
            self.btn_action.opacity = 1
            self.btn_action.disabled = False
            
            self.sub_action_box.opacity = 1
            self.btn_status.disabled = False 
            self.btn_upgrade.disabled = False
            self.btn_upgrade.background_color = (0.6, 0.2, 0.8, 1)
            
            for p in self.current_node.army_pieces:
                card = PieceCard(p, map_screen_ref=self.map_screen) 
                self.piece_cards.append(card)
                self.content_grid.add_widget(card)
        else:
            self.btn_tab_army.background_color = (0.2, 0.2, 0.2, 1)
            self.btn_tab_recruit.background_color = (0.3, 0.8, 0.3, 1)
            self.status_lbl.text = f"Tax: [color=00ff00]{self.app.tax_points.get(self.current_node.faction, 0)}[/color] | Cap: {total}/{max_cap}"
            
            self.btn_action.text = "[b]QUICK RECRUIT\n(7 TAX)[/b]"
            self.btn_action.background_color = (0.8, 0.6, 0.1, 1)
            self.btn_action.opacity = 1
            self.btn_action.disabled = False
            
            self.sub_action_box.opacity = 0
            self.btn_status.disabled = True 
            self.btn_upgrade.disabled = True
            
            can_heavy = (self.current_node.node_type == 'castle')
            units_to_sell = [
                ('praetorian', 7), ('royalguard', 7), ('menatarm', 5),
                ('knight', 4), ('bishop', 4), ('rook', 4), 
                ('hastati', 3), ('levies', 2), ('pawn', 2)
            ]
            unlock_costs = {'praetorian': 14, 'royalguard': 14, 'hastati': 6}
            
            for p_name, cost in units_to_sell:
                if cost > 3 and not can_heavy: continue 
                
                is_locked = p_name not in self.app.unlocked_units.get(self.current_node.faction, set())
                ucost = unlock_costs.get(p_name, 0)
                card = RecruitCard(p_name, cost, self.current_node.faction, self.app, self.buy_piece, is_locked=is_locked, unlock_cost=ucost)
                self.content_grid.add_widget(card)

    def buy_piece(self, piece_name, cost, is_locked, unlock_cost):
        self.app.play_click_sound()
        faction = self.current_node.faction
        
        if is_locked:
            if self.app.tax_points.get(faction, 0) >= unlock_cost:
                self.app.tax_points[faction] -= unlock_cost
                self.app.unlocked_units[faction].add(piece_name)
                self.switch_tab('recruit')
            return
            
        tax = self.app.tax_points[faction]
        if tax < cost: return
        
        headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
        heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
        heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
        max_cap = 16 if headers > 0 else 8
        if len(self.current_node.army_pieces) >= max_cap: return
        
        if piece_name in ['pawn', 'hastati', 'levies'] and heavies > 9: return 
        
        self.app.tax_points[faction] -= cost
        new_p = generate_piece(piece_name, faction, self.app)
        self.current_node.army_pieces.append(new_p)
        self.switch_tab('recruit') 

    def execute_action(self, instance):
        self.app.play_click_sound()
        if self.current_tab == 'army':
            fatigue = self.app.army_fatigue.get(self.current_node.faction, 0)
            if fatigue >= 6:
                self.map_screen.status_lbl.text = "[color=ff0000]ARMY IS EXHAUSTED (FATIGUE = 6)! MUST REST.[/color]"
                return
                
            selected_pieces = [card.piece_obj for card in self.piece_cards if card.is_selected]
            if len(selected_pieces) == 0:
                selected_pieces = self.current_node.army_pieces.copy() 
            
            if len(selected_pieces) == 0: return 
            
            for p in selected_pieces:
                self.current_node.army_pieces.remove(p)
                
            self.app.combat_marching_army = selected_pieces
            self.close_panel()
            self.map_screen.start_marching(self.current_node)
        else:
            tax = self.app.tax_points[self.current_node.faction]
            if tax < 7: return
            self.app.tax_points[self.current_node.faction] -= 7
            
            targets = ['queen', 'rook', 'rook', 'bishop', 'bishop', 'knight', 'knight'] + ['pawn']*8
            for p_name in targets:
                headers = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince')
                heavy_names = ['queen', 'rook', 'bishop', 'knight', 'princess', 'menatarm', 'praetorian', 'royalguard']
                heavies = sum(1 for p in self.current_node.army_pieces if p.__class__.__name__.lower() in heavy_names)
                if len(self.current_node.army_pieces) >= (16 if headers > 0 else 8): break
                
                actual_p = p_name
                if p_name in ['queen', 'rook', 'bishop', 'knight'] and heavies >= 9:
                    actual_p = 'pawn'
                    
                self.current_node.army_pieces.append(generate_piece(actual_p, self.current_node.faction, self.app))
            self.switch_tab('recruit')