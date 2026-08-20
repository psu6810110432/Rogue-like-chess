# logic/ai_controller.py
import random
from kivy.app import App
from kivy.clock import Clock

class AIController:
    def __init__(self, screen):
        self.screen = screen

    def check_ai_turn(self):
        if getattr(self.screen, 'battle_phase', 'playing') != 'playing':
            self.screen.is_input_locked = False
            return
        app = App.get_running_app()
        is_bot_turn = False
        game_mode = getattr(self.screen, 'game_mode', 'PVP')
        match_type = getattr(app, 'match_type', 'PVE')

        # Player involvement check for D&C spectator matches
        if game_mode == 'Divide_Conquer':
            attacker_faction = getattr(app.combat_source, 'faction', 'white') if hasattr(app, 'combat_source') else 'white'
            defender_faction = getattr(app.combat_target, 'faction', 'red') if hasattr(app, 'combat_target') else 'black'
            
            # Identify the macro faction for the current turn
            current_faction = attacker_faction if self.screen.game.current_turn == 'white' else defender_faction
            
            if match_type == 'PVE':
                player_involved = (attacker_faction == 'white' or defender_faction == 'white')
                if not player_involved:
                    # Both sides are AI (e.g., black vs red)
                    is_bot_turn = True
                elif current_faction != 'white':
                    is_bot_turn = True
            elif match_type == 'LOCAL_PVP':
                if current_faction == 'red':
                    is_bot_turn = True
        else:
            if match_type == 'PVE' and self.screen.game.current_turn == 'black':
                is_bot_turn = True

        if is_bot_turn and not self.screen.game.game_result:
            self.screen.is_input_locked = True
            # ✨ เช็คสถานะ FF: ถ้าเปิดอยู่ให้ลดดีเลย์เหลือ 0.05 วินาที
            ff_mode = getattr(self.screen, 'fast_forward_ai', False)
            delay = 0.05 if ff_mode else 0.8
            
            # ✨ เปลี่ยนจาก 0.8 เป็น delay
            self.screen.ai_event = Clock.schedule_once(self.trigger_ai_move, delay)
        else:
            self.screen.is_input_locked = False

    # ------------------------------------------------------------------
    # AI move execution
    # ------------------------------------------------------------------
    def trigger_ai_move(self, dt):
        if self.screen.game.game_result:
            return
        # เพิ่มบรรทัดนี้ดักไว้
        if getattr(self.screen, 'battle_phase', 'playing') != 'playing': return

        game_mode = getattr(self.screen, 'game_mode', 'PVP')
        difficulty = getattr(App.get_running_app(), 'ai_difficulty', 'normal')
        ai_color = self.screen.game.current_turn

        # ✨ กำหนดความเร็วของแอนิเมชันในตานี้
        ff_mode = getattr(self.screen, 'fast_forward_ai', False)
        delay_short = 0.05 if ff_mode else 0.5
        delay_long = 0.05 if ff_mode else 0.8

        # 1. Item usage by AI
        inv = getattr(self.screen.game, f'inventory_{ai_color}', [])
        if inv:
            use_chance = 0.6 if difficulty == 'hard' else 0.4 if difficulty == 'normal' else 0.25
            if len(inv) >= 5 or random.random() < use_chance:
                item_to_use = random.choice(inv)
                valid_pieces = [
                    p for row in self.screen.game.board
                    for p in row
                    if p and p.color == ai_color and getattr(p, 'item', None) is None
                ]
                if valid_pieces:
                    chosen_piece = random.choice(valid_pieces)
                    chosen_piece.item = item_to_use
                    if item_to_use.id == 6:
                        chosen_piece.coins += 1
                        chosen_piece.base_points = max(0, chosen_piece.base_points - 1)
                    elif item_to_use.id == 10 and chosen_piece.__class__.__name__.lower() == 'pawn':
                        chosen_piece.base_points = 5
                        chosen_piece.coins = 3
                    inv.remove(item_to_use)
                    App.get_running_app().play_click_sound()
                    self.screen.init_board_ui()
                    self.screen.update_inventory_ui()

        # 2. Pick and execute the best move
        from logic.ai_logic import ChessAI
        move = ChessAI.get_best_move(self.screen.game, ai_color=ai_color, game_mode=game_mode)

        # 3. Apply move and handle special results
        if move:
            (sr, sc), (er, ec) = move
            res = self.screen.controller.submit_move(sr, sc, er, ec)

            if isinstance(res, tuple) and res[0] == "crash":
                atk, df = res[1], res[2]
                if not atk or not df:
                    return

                if hasattr(self.screen, 'squares'):
                    sq_a = self.screen.squares.get((sr, sc))
                    sq_d = self.screen.squares.get((er, ec))
                    if sq_a: sq_a.update_square_style(highlight=True)
                    if sq_d: sq_d.update_square_style(is_check=True)
                App.get_running_app().play_move_sound()

                if getattr(df, 'item', None) and df.item.id == 4:
                    def _do_shield_block(dt):
                        self.screen.controller.submit_shield_block((sr, sc), (er, ec))
                        self.screen.init_board_ui()
                        self.screen.ai_event = None
                        self.screen.trigger_end_turn_logic(ai_color)
                    # ✨ ใช้ delay_short
                    Clock.schedule_once(_do_shield_block, delay_short)
                    return

                # ✨ ลอจิกข้ามหน้าจอแอนิเมชันปะทะ (Auto-Resolve) เมื่อกด FF
                if ff_mode:
                    # ❌ ลบ import random บรรทัดนี้ทิ้งไปเลยครับ!
                    # สุ่มผลแพ้ชนะคร่าวๆ (ถ้ามีสูตรคำนวณ ATK/DEF อยู่แล้ว สามารถใส่แทนตรงนี้ได้)
                    auto_result = random.choices(["won", "died", "draw"], weights=[45, 45, 10])[0]
                    self.screen.execute_board_move((sr, sc), (er, ec), auto_result)
                    Clock.schedule_once(self._schedule_next_ai_turn, delay_long)
                    return

                # ── After 0.5s, open the crash overlay ──────────────────────
                Clock.schedule_once(
                    lambda dt, a=atk, d=df, s=(sr, sc), e=(er, ec):
                        self.screen.show_crash_overlay(a, d, s, e),
                    delay_short # ✨ ใช้ delay_short
                )
                return

            if res == "promote":
                from logic.pieces import Queen
                self.screen.controller.submit_promotion(er, ec, Queen)

            if res in [True, "promote", "died"]:
                App.get_running_app().play_move_sound()

            self.screen.init_board_ui()

        self.screen.ai_event = None

        # ✨ ใช้ delay_long สำหรับการเดินตาถัดไป
        Clock.schedule_once(self._schedule_next_ai_turn, delay_long)

    # ------------------------------------------------------------------
    # Continuous loop helper
    # ------------------------------------------------------------------
    def _schedule_next_ai_turn(self, dt):
        """Called after each AI move to continue the auto-battle loop."""
        if not self.screen.game.game_result:
            self.check_ai_turn()