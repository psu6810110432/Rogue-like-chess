# logic/ai_controller.py
import random
from kivy.app import App
from kivy.clock import Clock

class AIController:
    def __init__(self, screen):
        self.screen = screen

    # ------------------------------------------------------------------
    # Helper: is this a DnC PVE auto-battle (AI vs AI)?
    # ------------------------------------------------------------------
    def _is_dnc_pve(self):
        """Return True when both sides are driven by AI in DnC mode."""
        return (
            getattr(self.screen, 'game_mode', '') == 'Divide_Conquer'
            and getattr(self.screen, 'is_pve_auto_battle', False)
        )

    # ------------------------------------------------------------------
    # Turn gating
    # ------------------------------------------------------------------
    def check_ai_turn(self):
        app = App.get_running_app()
        is_bot_turn = False
        game_mode = getattr(self.screen, 'game_mode', 'PVP')

        # ── Branch 1: DnC PVE (match_type == 'PVE') ─────────────────────
        # is_pve_auto_battle is True → every turn is an AI turn.
        # The human player is a spectator; no human controller is ever given.
        if self._is_dnc_pve():
            is_bot_turn = True

        # ── Branch 2: Standard non-DnC PVE ──────────────────────────────
        # AI controls black; human controls white.
        elif game_mode == 'PVE' and self.screen.game.current_turn == 'black':
            is_bot_turn = True

        # ── Branch 3: DnC LOCAL_PVP (match_type == 'LOCAL_PVP') ─────────
        # Human plays their own faction (white/black based on which node
        # they own). Only red-faction (bandit) nodes are bot-driven.
        # is_pve_auto_battle is False in this branch so _is_dnc_pve() above
        # did NOT match — this branch only fires for LOCAL_PVP DnC combats.
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

    # ------------------------------------------------------------------
    # AI move execution
    # ------------------------------------------------------------------
    def trigger_ai_move(self, dt):
        if self.screen.game.game_result:
            return

        game_mode = getattr(self.screen, 'game_mode', 'PVP')
        difficulty = getattr(App.get_running_app(), 'ai_difficulty', 'normal')
        ai_color = self.screen.game.current_turn

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

                # ── Visual engagement cue (no icon changes) ─────────────────
                # Highlight the two squares so the spectator knows what is
                # attacking what, WITHOUT overwriting any piece icons.
                # Both pieces remain fully visible on the board.
                #   Yellow / "selected"  = attacker's current square (origin)
                #   Red    / "check"     = defender's square (about to be hit)
                if hasattr(self.screen, 'squares'):
                    sq_a = self.screen.squares.get((sr, sc))
                    sq_d = self.screen.squares.get((er, ec))
                    if sq_a: sq_a.update_square_style(highlight=True)
                    if sq_d: sq_d.update_square_style(is_check=True)
                App.get_running_app().play_move_sound()

                if getattr(df, 'item', None) and df.item.id == 4:
                    # Shield block: highlights already set; resolve after a
                    # short pause so the spectator can see the attempt.
                    def _do_shield_block(dt):
                        self.screen.controller.submit_shield_block((sr, sc), (er, ec))
                        self.screen.init_board_ui()
                        self.screen.ai_event = None
                        self.screen.trigger_end_turn_logic(ai_color)
                    Clock.schedule_once(_do_shield_block, 0.5)
                    return

                # ── After 0.5s, open the crash overlay ──────────────────────
                # Both pieces are still on the board; the spectator has had
                # time to register who is fighting whom.
                Clock.schedule_once(
                    lambda dt, a=atk, d=df, s=(sr, sc), e=(er, ec):
                        self.screen.show_crash_overlay(a, d, s, e),
                    0.5
                )
                return

            if res == "promote":
                from logic.pieces import Queen
                self.screen.controller.submit_promotion(er, ec, Queen)

            if res in [True, "promote", "died"]:
                App.get_running_app().play_move_sound()

            self.screen.init_board_ui()

        self.screen.ai_event = None

        # 4. Schedule the next AI turn after a short delay so the board
        #    has time to render and the player can follow the action.
        Clock.schedule_once(self._schedule_next_ai_turn, 0.8)

    # ------------------------------------------------------------------
    # Continuous loop helper
    # ------------------------------------------------------------------
    def _schedule_next_ai_turn(self, dt):
        """Called after each AI move to continue the auto-battle loop."""
        if not self.screen.game.game_result:
            self.check_ai_turn()