# controllers/base_controller.py
from abc import ABC, abstractmethod


class BaseGameController(ABC):
    """Abstract interface for game controllers.
    
    LocalGameController: direct board manipulation (PVE, LOCAL_PVP, Campaign)
    OnlineGameController (future): sends actions to server, applies server responses
    """

    @abstractmethod
    def submit_move(self, sr, sc, er, ec):
        """Submit a move from (sr, sc) to (er, ec).
        
        Returns the result from game.move_piece():
        - ("crash", attacker, defender) if a capture triggers the crash system
        - True if the move was successful
        - "promote" if a pawn reached the back rank
        - "died" if the attacker lost a crash
        - False if the move was invalid
        """
        pass

    @abstractmethod
    def submit_crash_resolve(self, sr, sc, er, ec, crash_won):
        """Submit a crash resolution after the coin toss animation.
        
        Args:
            crash_won: "won", "died", or "blocked"
        
        Returns the result from game.move_piece(resolve_crash=True):
        - True, "promote", "died", "survived", "defender_survived", or False
        """
        pass

    @abstractmethod
    def submit_shield_block(self, start_pos, end_pos):
        """Handle a shield-blocked attack (item id=4).
        
        Clears the defender's shield item, marks attacker as moved,
        saves history, and completes the turn.
        """
        pass

    @abstractmethod
    def submit_promotion(self, r, c, piece_class):
        """Promote a pawn at (r, c) to the given piece class."""
        pass

    @abstractmethod
    def submit_undo(self):
        """Undo the last move.
        
        Returns True if undo was successful, False if no moves to undo.
        """
        pass

    @abstractmethod
    def submit_item_use(self, item, piece, turn_color):
        """Apply an item to a piece and remove it from the inventory.
        
        Handles special item effects (e.g., item 6 = coins+1/points-1,
        item 10 = pawn upgrade).
        """
        pass
