import pytest
from unittest.mock import MagicMock, patch
from logic.ai_logic import ChessAI

# --- Mocks ---

class MockPiece:
    def __init__(self, color, name, is_header=False):
        self.color = color
        self.name = name
        self.is_header = is_header
        # Mock class name since ai_logic uses __class__.__name__
        self.__class__ = type(name, (), {'__name__': name})
        
    def is_valid_move(self, start, end, board):
        return True # Default to true for testing, will override in specific tests

class MockBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.legal_moves = {} # Dict of start_pos: [end_pos1, end_pos2]
        
    def get_legal_moves(self, pos):
        return self.legal_moves.get(pos, [])

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.ai_difficulty = 'normal'
    app.combat_marching_fatigue = 0
    app.combat_target = MagicMock()
    app.combat_target.fatigue = 0
    return app

# --- Tests ---

@patch('logic.ai_logic.App')
def test_dnc_commander_protection(mock_app_cls, mock_app):
    """
    In D&C mode, the AI must apply a massive penalty to any move that 
    leaves the Commander in a threatened square.
    """
    mock_app_cls.get_running_app.return_value = mock_app
    
    board = MockBoard()
    commander = MockPiece('black', 'King', is_header=True)
    board.board[0][0] = commander
    
    pawn = MockPiece('black', 'Pawn')
    board.board[1][0] = pawn
    
    # Enemy rook threatening the commander's row
    enemy_rook = MockPiece('white', 'Rook')
    board.board[0][7] = enemy_rook
    
    # Commander can move out of danger (to 1,1)
    # Pawn can move to (2,0)
    board.legal_moves = {
        (0, 0): [(1, 1)],
        (1, 0): [(2, 0)]
    }
    
    # Scenario: Enemy rook attacks (0,0) and (2,0) but NOT (1,1)
    def rook_attacks(start, end, b):
        return end in [(0, 0), (2, 0)]
    enemy_rook.is_valid_move = rook_attacks
    
    # If the AI plays as 'black' in D&C, moving the pawn leaves the commander at (0,0) which is attacked.
    # Moving the commander to (1,1) makes it safe.
    # The AI should choose the commander move.
    
    best_move = ChessAI.get_best_move(board, ai_color='black', game_mode='Divide_Conquer')
    
    # Must choose to move the commander (0,0) -> (1,1) to save it
    assert best_move == ((0, 0), (1, 1))

@patch('logic.ai_logic.App')
def test_classic_ignores_dnc_rules(mock_app_cls, mock_app):
    """
    In Classic mode, the AI (on normal difficulty) does not evaluate the deep 
    commander safety simulation, so it might just choose the first legal move or capture.
    """
    mock_app_cls.get_running_app.return_value = mock_app
    
    board = MockBoard()
    commander = MockPiece('black', 'King', is_header=True)
    board.board[0][0] = commander
    
    # A free enemy piece that the pawn can capture
    free_enemy = MockPiece('white', 'Pawn')
    board.board[2][1] = free_enemy
    
    pawn = MockPiece('black', 'Pawn')
    board.board[1][0] = pawn
    
    enemy_rook = MockPiece('white', 'Rook')
    board.board[0][7] = enemy_rook
    
    board.legal_moves = {
        (0, 0): [(1, 1)],
        (1, 0): [(2, 1)] # Capture!
    }
    
    # Enemy attacks (0,0)
    def rook_attacks(start, end, b):
        return end == (0, 0)
    enemy_rook.is_valid_move = rook_attacks
    
    # In Classic PVP, it evaluates captures over the D&C safety (on normal difficulty).
    best_move = ChessAI.get_best_move(board, ai_color='black', game_mode='PVP')
    
    # Should choose the capture because D&C massive penalty isn't applied
    assert best_move == ((1, 0), (2, 1))

@patch('logic.ai_logic.App')
def test_dnc_fatigue_penalty(mock_app_cls, mock_app):
    """
    In D&C mode, if fatigue is >= 4, the AI penalizes forward moves.
    """
    # Black is defender (moves down: er > sr is forward)
    mock_app.combat_target = MagicMock()
    mock_app.combat_target.fatigue = 5 # High fatigue!
    mock_app_cls.get_running_app.return_value = mock_app
    
    board = MockBoard()
    knight = MockPiece('black', 'Knight')
    board.board[2][2] = knight
    
    # Knight can move forward to (4,3) or backward to (0,1)
    board.legal_moves = {
        (2, 2): [(4, 3), (0, 1)]
    }
    
    # In Divide_Conquer, moving to (4,3) incurs a -15 penalty.
    # Moving to (0,1) incurs no penalty.
    # Therefore, (0,1) should score higher and be chosen.
    best_move = ChessAI.get_best_move(board, ai_color='black', game_mode='Divide_Conquer')
    
    assert best_move == ((2, 2), (0, 1))
