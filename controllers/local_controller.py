# controllers/local_controller.py
from controllers.base_controller import BaseGameController


class LocalGameController(BaseGameController):
    """Game controller for local play (PVE, LOCAL_PVP, Campaign).
    
    Directly calls game board methods. All mutations happen
    synchronously and results are returned immediately.
    """

    def __init__(self, game):
        self.game = game

    def submit_move(self, sr, sc, er, ec):
        """Execute a move directly on the local board."""
        return self.game.move_piece(sr, sc, er, ec)

    def submit_crash_resolve(self, sr, sc, er, ec, crash_won):
        """Resolve a crash outcome on the local board."""
        return self.game.move_piece(sr, sc, er, ec, resolve_crash=True, crash_won=crash_won)

    def submit_shield_block(self, start_pos, end_pos):
        """Handle a shield block locally."""
        atk = self.game.board[start_pos[0]][start_pos[1]]
        df = self.game.board[end_pos[0]][end_pos[1]]
        if df:
            df.item = None
        if atk:
            atk.has_moved = True
        self.game.en_passant_target = None
        self.game.history.save_state(self.game, "Shield Blocked!")
        self.game.complete_turn()

    def submit_promotion(self, r, c, piece_class):
        """Promote a pawn on the local board."""
        self.game.promote_pawn(r, c, piece_class)

    def submit_undo(self):
        """Undo the last move on the local board."""
        return self.game.undo_move()

    def submit_item_use(self, item, piece, turn_color):
        """Apply an item to a piece locally."""
        piece.item = item
        # Special item effects
        if item.id == 6:
            piece.coins += 1
            piece.base_points = max(0, piece.base_points - 1)
        elif item.id == 10 and piece.__class__.__name__.lower() == 'pawn':
            piece.base_points = 5
            piece.coins = 3
        # Remove from inventory
        inv = getattr(self.game, f'inventory_{turn_color}')
        if item in inv:
            inv.remove(item)
