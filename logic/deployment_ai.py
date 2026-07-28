# logic/deployment_ai.py
"""
Phase 5: Deployment AI

Handles automatic positioning of AI units on the board before a battle begins.
"""

def arrange_army(board, army_list, is_attacker):
    """
    Arrange the AI army logically in their deployment zone.
    
    Rules:
    - Commander (King/Prince) safely in the back row center.
    - Pawns/Levies in the front row.
    - Knights on the flanks.
    - Remaining pieces in any available safe spot.
    
    Deployment Zones:
    - Attacker: Rows 5, 6, 7 (Bottom 3). Front = 5, Back = 7.
    - Defender: Rows 0, 1, 2 (Top 3). Front = 2, Back = 0.
    """
    if not army_list:
        return

    # 1. Clear existing pieces of this army from the board
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p in army_list:
                board[r][c] = None

    # Determine deployment zone mapping
    if is_attacker:
        back_row = 7
        mid_row = 6
        front_row = 5
    else:
        back_row = 0
        mid_row = 1
        front_row = 2

    available_squares = {
        'back': [(back_row, c) for c in range(8)],
        'mid': [(mid_row, c) for c in range(8)],
        'front': [(front_row, c) for c in range(8)]
    }

    def place_piece(piece, preferred_rows, preferred_cols=None):
        for row_key in preferred_rows:
            squares = available_squares[row_key]
            if preferred_cols is not None:
                # Try to find a square in preferred cols
                for sq in squares:
                    if sq[1] in preferred_cols:
                        board[sq[0]][sq[1]] = piece
                        squares.remove(sq)
                        return True
            
            if squares:
                # If preferred_cols is [3, 4], try to pick closest to center
                if preferred_cols == [3, 4]:
                    squares.sort(key=lambda sq: abs(sq[1] - 3.5))
                sq = squares.pop(0)
                board[sq[0]][sq[1]] = piece
                return True
                
        # If preferred rows are full, fallback to any available row
        for row_key in ['back', 'mid', 'front']:
            if available_squares[row_key]:
                sq = available_squares[row_key].pop(0)
                board[sq[0]][sq[1]] = piece
                return True
        return False

    # Categorize pieces
    commander = None
    pawns = []
    knights = []
    others = []

    for p in army_list:
        p_name = p.__class__.__name__.lower()
        if p_name == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False):
            if not commander:
                commander = p
            else:
                others.append(p)
        elif p_name in ['pawn', 'levies']:
            pawns.append(p)
        elif p_name == 'knight':
            knights.append(p)
        else:
            others.append(p)

    # 1. Place commander safely in back row center (cols 3 or 4)
    if commander:
        place_piece(commander, ['back'], preferred_cols=[3, 4])

    # 2. Place Pawns/Levies in front line
    for p in pawns:
        place_piece(p, ['front', 'mid', 'back'])

    # 3. Place Knights on flanks (cols 0, 1, 6, 7)
    for p in knights:
        place_piece(p, ['mid', 'back', 'front'], preferred_cols=[0, 1, 6, 7])

    # 4. Place remaining pieces (Rooks, Bishops, Queens, etc.)
    for p in others:
        place_piece(p, ['mid', 'back', 'front'])
