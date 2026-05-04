# logic/ai_controller.py
import random
from kivy.app import App
from kivy.clock import Clock

class AIController:
    def __init__(self, screen):
        self.screen = screen

    def check_ai_turn(self):
        app = App.get_running_app()
        is_bot_turn = False
        game_mode = getattr(self.screen, 'game_mode', 'PVP')
        
        # ถอด PVAI ออกจากเงื่อนไข
        if game_mode == 'PVE' and self.screen.game.current_turn == 'black': 
            is_bot_turn = True
        elif game_mode == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'red') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            if self.screen.game.current_turn == 'white' and attacker_faction == 'red':
                is_bot_turn = True
            elif self.screen.game.current_turn == 'black' and defender_faction == 'red':
                is_bot_turn = True
                
        if is_bot_turn and not self.screen.game.game_result: 
            self.screen.is_input_locked = True 
            self.screen.ai_event = Clock.schedule_once(self.trigger_ai_move, 0.8)
        else:
            self.screen.is_input_locked = False 

    def trigger_ai_move(self, dt):
        if self.screen.game.game_result: return
        
        game_mode = getattr(self.screen, 'game_mode', 'PVP')
        difficulty = getattr(App.get_running_app(), 'ai_difficulty', 'normal')
        ai_color = self.screen.game.current_turn
        
        # 1. การใช้งานไอเท็มของ AI
        inv = getattr(self.screen.game, f'inventory_{ai_color}', [])
        if inv:
            use_chance = 0.6 if difficulty == 'hard' else 0.4 if difficulty == 'normal' else 0.25
            if len(inv) >= 5 or random.random() < use_chance:
                item_to_use = random.choice(inv)
                valid_pieces = [p for row in self.screen.game.board for p in row if p and p.color == ai_color and getattr(p, 'item', None) is None]
                if valid_pieces:
                    chosen_piece = random.choice(valid_pieces)
                    chosen_piece.item = item_to_use
                    if item_to_use.id == 6: 
                        chosen_piece.coins += 1; chosen_piece.base_points = max(0, chosen_piece.base_points - 1)
                    elif item_to_use.id == 10 and chosen_piece.__class__.__name__.lower() == 'pawn': 
                        chosen_piece.base_points = 5; chosen_piece.coins = 3
                    inv.remove(item_to_use)
                    App.get_running_app().play_click_sound()
                    self.screen.init_board_ui()
                    self.screen.update_inventory_ui()
                    
        # 2. การตัดสินใจเดินหมาก (เหลือเฉพาะ PVE ธรรมดา)
        from logic.ai_logic import ChessAI
        move = ChessAI.get_best_move(self.screen.game, ai_color=ai_color)

        # 3. จัดการขยับหมากและ Crash
        if move:
            (sr, sc), (er, ec) = move
            res = self.screen.game.move_piece(sr, sc, er, ec)
            
            if isinstance(res, tuple) and res[0] == "crash":
                atk, df = res[1], res[2]
                if not atk or not df: return
                if getattr(df, 'item', None) and df.item.id == 4:
                    df.item = None; atk.has_moved = True
                    self.screen.game.history.save_state(self.screen.game, "Shield Blocked!")
                    self.screen.game.complete_turn()
                    self.screen.init_board_ui()
                    return 
                self.screen.show_crash_overlay(atk, df, (sr, sc), (er, ec))
                return
                
            if res == "promote":
                from logic.pieces import Queen
                self.screen.game.promote_pawn(er, ec, Queen)
                
            if res in [True, "promote", "died"]: 
                App.get_running_app().play_move_sound()
            self.screen.init_board_ui()
            
        self.screen.ai_event = None
        self.check_ai_turn()