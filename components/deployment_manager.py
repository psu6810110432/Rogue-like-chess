# components/deployment_manager.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.app import App

class DeploymentManager:
    def __init__(self, screen):
        self.screen = screen
        self.deployment_layer = None
        self.black_mask = None
        self.deploy_lbl = None
        self.deployment_btn_box = None
        self.mask_rect = None

    def setup_deployment_ui(self):
        self.remove_layer() # เคลียร์ของเก่าถ้ามี
        
        self.screen.battle_phase = 'deployment_arrange_atk'
        self.deployment_layer = FloatLayout()
        self.screen.root_layout.add_widget(self.deployment_layer)
        
        if hasattr(self.screen.sidebar, 'hide_buttons'):
            self.screen.sidebar.hide_buttons()
            
        self.black_mask = Widget()
        with self.black_mask.canvas.before:
            # ✨ ให้โปร่งใสทั้งโหมด 2D iso และ 2.5D
            current_dim = getattr(self.screen, 'current_dimension', '2D')
            if current_dim in ['2D iso', '2.5D']:
                Color(0, 0, 0, 0)  # โปร่งใส 100%
            else:
                Color(0, 0, 0, 1)  # สีดำทึบ สำหรับโหมด 2D Classic
                
            self.mask_rect = Rectangle()
            
        def update_mask(*args):
            if hasattr(self.screen, 'grid') and self.screen.grid:
                self.mask_rect.pos = (self.screen.grid.x, self.screen.grid.y + self.screen.grid.height * 3 / 8)
                self.mask_rect.size = (self.screen.grid.width, self.screen.grid.height * 5 / 8)
                
        if hasattr(self.screen, 'grid'):
            self.screen.grid.bind(pos=update_mask, size=update_mask)
            update_mask()
            
        self.deployment_layer.add_widget(self.black_mask)
        
        self.deploy_lbl = Label(
            text="[b]PHASE 1: ATTACKER DEPLOYMENT[/b]\nArrange your units (Bottom 3 rows)", 
            markup=True, halign='center', pos_hint={'center_x': 0.5, 'center_y': 0.7}, 
            font_size='24sp', color=(1, 0.8, 0, 1)
        )
        self.deployment_layer.add_widget(self.deploy_lbl)
        
        self.deployment_btn_box = BoxLayout(
            orientation='horizontal', size_hint=(None, None), 
            size=(dp(400), dp(60)), pos_hint={'center_x': 0.5, 'y': 0.1}, spacing=dp(20)
        )
        
        app = App.get_running_app()
        attacker_faction = getattr(app.combat_source, 'faction', 'red') if hasattr(app, 'combat_source') else 'white'
        match_type = getattr(app, 'match_type', 'PVE')
        # สีดำจะเป็น AI แค่ในโหมด PVE เท่านั้น ส่วนสีแดงเป็น AI เสมอ
        is_ai_attacker = (attacker_faction == 'black' and match_type == 'PVE') or (attacker_faction == 'red')
        
        if not is_ai_attacker:
            btn_retreat = Button(text="[b]RETREAT[/b]", markup=True, background_color=(0.8, 0.2, 0.2, 1), font_size='18sp')
            btn_retreat.bind(on_release=self.deployment_retreat) 
            
            btn_confirm = Button(text="[b]CONFIRM SETUP[/b]", markup=True, background_color=(0.2, 0.6, 0.8, 1), font_size='18sp')
            btn_confirm.bind(on_release=self.check_next_deployment_phase)
            
            self.deployment_btn_box.add_widget(btn_retreat)
            self.deployment_btn_box.add_widget(btn_confirm)
            
        self.deployment_layer.add_widget(self.deployment_btn_box)
        
        self.screen.refresh_ui()

        if is_ai_attacker:
            self.deploy_lbl.text = "[color=ffaa00]PHASE 1: AI IS DEPLOYING...[/color]"
            from logic.deployment_ai import arrange_army
            from kivy.clock import Clock
            arrange_army(self.screen.game.board, app.combat_marching_army, is_attacker=True)
            self.screen.init_board_ui()
            Clock.schedule_once(lambda dt: self.check_next_deployment_phase(None), 1.0)

    def check_next_deployment_phase(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        target_faction = getattr(app.combat_target, 'faction', 'black') if hasattr(app, 'combat_target') else 'black'
        match_type = getattr(app, 'match_type', 'PVE')
        # สีดำจะเป็น AI แค่ในโหมด PVE เท่านั้น ส่วนสีแดงเป็น AI เสมอ
        is_ai_defender = (target_faction == 'black' and match_type == 'PVE') or (target_faction == 'red')
        
        if target_faction in ['white', 'black', 'red'] and getattr(self.screen, 'game_mode', '') == 'Divide_Conquer':
            self.screen.battle_phase = 'deployment_arrange_def'
            self.screen.selected = None
            if self.black_mask in self.deployment_layer.children:
                self.deployment_layer.remove_widget(self.black_mask)
            self.deploy_lbl.text = "[b]PHASE 2: DEFENDER DEPLOYMENT[/b]\nArrange your units (Top 3 rows)\nEnemy is revealed!"
            self.deploy_lbl.color = (1, 0.4, 0.4, 1)
            self.deployment_btn_box.clear_widgets()
            
            if not is_ai_defender:
                btn_confirm = Button(text="[b]CONFIRM DEFENSE[/b]", markup=True, background_color=(0.2, 0.6, 0.8, 1), font_size='18sp')
                btn_confirm.bind(on_release=self.start_battle_phase)
                self.deployment_btn_box.add_widget(btn_confirm)
                
            self.screen.init_board_ui() 
            self.screen.refresh_ui()

            if is_ai_defender:
                self.deploy_lbl.text = "[color=ffaa00]PHASE 2: AI IS DEPLOYING...[/color]"
                from logic.deployment_ai import arrange_army
                from kivy.clock import Clock
                arrange_army(self.screen.game.board, app.combat_target_army, is_attacker=False)
                self.screen.init_board_ui()
                # Next phase after AI deploys its defense is the Reveal phase,
                # so the human attacker can see the AI's formulation before starting.
                Clock.schedule_once(lambda dt: self.show_reveal_phase(None), 1.0)
        else:
            self.show_reveal_phase(instance)

    def deployment_retreat(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        app.battle_finished = True
        app.battle_winner = 'draw'
        app.survivors_atk = app.combat_marching_army
        app.survivors_def = app.combat_target_army
        self.remove_layer()
        if hasattr(self.screen, 'battle_phase'):
            self.screen.battle_phase = 'playing'
        self.screen.manager.current = 'campaign_map'

    def show_reveal_phase(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        self.screen.battle_phase = 'deployment_reveal'
        self.screen.selected = None
        if hasattr(self.screen.sidebar, 'show_buttons'):
            self.screen.sidebar.show_buttons()
        if self.black_mask in self.deployment_layer.children:
            self.deployment_layer.remove_widget(self.black_mask)
            
        self.deploy_lbl.text = "[b]PHASE 2: ENEMY REVEALED[/b]\nObserve the enemy Commander's position!"
        self.deploy_lbl.color = (1, 0.4, 0.4, 1)
        self.deployment_btn_box.clear_widgets()
        self.screen.refresh_ui()

        attacker_faction = getattr(app.combat_source, 'faction', 'red') if hasattr(app, 'combat_source') else 'white'
        defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
        player_involved = (attacker_faction == 'white' or defender_faction == 'white')
        
        if not player_involved:
            from kivy.clock import Clock
            self.deploy_lbl.text = "[b]AI SPECTATOR MATCH BEGINS...[/b]"
            self.deploy_lbl.color = (0.4, 1, 0.4, 1)
            Clock.schedule_once(lambda dt: self.start_battle_phase(None), 2.0)
            return

        btn_ready = Button(text="[b]READY TO BATTLE[/b]", markup=True, background_color=(0.2, 0.8, 0.2, 1), font_size='18sp')
        btn_ready.bind(on_release=self.start_battle_phase)
        self.deployment_btn_box.add_widget(btn_ready)

    def start_battle_phase(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'play_click_sound'): app.play_click_sound()
        self.screen.battle_phase = 'playing'
        self.screen.selected = None
        self.remove_layer()
        if hasattr(self.screen.sidebar, 'show_buttons'):
            self.screen.sidebar.show_buttons()
        self.screen.init_board_ui()
        self.screen.refresh_ui()
        # Delay the first AI turn slightly so the board is fully rendered
        # before any piece moves.  1.0s gives a clean visual transition.
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.screen.ai_controller.check_ai_turn(), 1.0)

    def remove_layer(self):
        if self.deployment_layer and self.deployment_layer in self.screen.root_layout.children:
            self.screen.root_layout.remove_widget(self.deployment_layer)
            self.deployment_layer = None