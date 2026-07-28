import pytest
from unittest.mock import MagicMock
from logic.deployment_ai import arrange_army

def create_mock_piece(name, is_header=False):
    """Helper to build a mock chess piece."""
    p = MagicMock()
    p.__class__ = type(name, (), {'__name__': name})
    p.name = name
    p.is_header = is_header
    return p

@pytest.fixture
def empty_board():
    return [[None for _ in range(8)] for _ in range(8)]

def test_arrange_army_attacker_positions(empty_board):
    """
    Test that the attacker's army (White) is correctly arranged:
    - Commander in back row (7) center (3 or 4)
    - Pawns in front row (5)
    - Knights on flanks (cols 0, 1, 6, 7)
    - No two units on the same square
    """
    army = [
        create_mock_piece('King', is_header=True),
        create_mock_piece('Pawn'),
        create_mock_piece('Pawn'),
        create_mock_piece('Knight'),
        create_mock_piece('Rook'),
    ]
    
    arrange_army(empty_board, army, is_attacker=True)
    
    placed_pieces = set()
    commander_pos = None
    pawn_rows = []
    knight_cols = []
    
    for r in range(8):
        for c in range(8):
            p = empty_board[r][c]
            if p is not None:
                # Ensure no duplicate piece references
                assert p not in placed_pieces
                placed_pieces.add(p)
                
                name = p.__class__.__name__
                if name == 'King':
                    commander_pos = (r, c)
                elif name == 'Pawn':
                    pawn_rows.append(r)
                elif name == 'Knight':
                    knight_cols.append(c)
                    
    # All pieces were placed
    assert len(placed_pieces) == 5
    
    # Commander is in back row center
    assert commander_pos[0] == 7
    assert commander_pos[1] in [3, 4]
    
    # Pawns are in front row (5)
    assert all(r == 5 for r in pawn_rows)
    
    # Knight is on a flank (0, 1, 6, 7)
    assert all(c in [0, 1, 6, 7] for c in knight_cols)


def test_arrange_army_defender_positions(empty_board):
    """
    Test that the defender's army (Black/Red) is correctly arranged:
    - Commander in back row (0) center (3 or 4)
    - Pawns in front row (2)
    - Knights on flanks
    """
    army = [
        create_mock_piece('Prince', is_header=True),
        create_mock_piece('Levies'),
        create_mock_piece('Knight'),
        create_mock_piece('Knight'),
        create_mock_piece('Bishop'),
    ]
    
    arrange_army(empty_board, army, is_attacker=False)
    
    placed_pieces = set()
    commander_pos = None
    pawn_rows = []
    knight_cols = []
    
    for r in range(8):
        for c in range(8):
            p = empty_board[r][c]
            if p is not None:
                placed_pieces.add(p)
                
                name = p.__class__.__name__
                if name == 'Prince':
                    commander_pos = (r, c)
                elif name == 'Levies':
                    pawn_rows.append(r)
                elif name == 'Knight':
                    knight_cols.append(c)
                    
    assert len(placed_pieces) == 5
    
    # Commander is in back row center
    assert commander_pos[0] == 0
    assert commander_pos[1] in [3, 4]
    
    # Levies (pawns) are in front row (2)
    assert all(r == 2 for r in pawn_rows)
    
    # Knights are on a flank (0, 1, 6, 7)
    assert all(c in [0, 1, 6, 7] for c in knight_cols)

def test_arrange_army_clears_old_positions(empty_board):
    """
    Test that arrange_army clears the old board positions of the army list 
    before re-arranging them, to ensure no duplicates are left behind.
    """
    army = [create_mock_piece('Pawn'), create_mock_piece('Rook')]
    
    # Simulate pieces being randomly placed initially (e.g. by setup_divide_conquer_board)
    empty_board[1][1] = army[0]
    empty_board[2][2] = army[1]
    
    arrange_army(empty_board, army, is_attacker=True)
    
    # Since they are attackers, they must be placed in rows 5-7.
    # The old positions in row 1 and 2 MUST be cleared.
    assert empty_board[1][1] is None
    assert empty_board[2][2] is None
    
    # Count total pieces on board to ensure exactly 2 exist
    count = sum(1 for r in range(8) for c in range(8) if empty_board[r][c] is not None)
    assert count == 2
