# Medieval Tribe Components

def medieval_pawn_passive():
    """
    Pawn passive ability for Medieval tribe
    - First move: can move 2 squares straight
    - Subsequent moves: 1 square straight only
    - Starting stats: 2 dice, 1 coin
    - Max stats: 12
    """
    def get_valid_moves(start, end, board):
        """
        Check if move is valid for Medieval Pawn
        start: start position (row, col)
        end: target position (row, col)
        board: game board state
        """
        sr, sc = start
        er, ec = end
        
        # ดึง piece จาก board
        piece = board[sr][sc]
        if not piece or piece.name.lower() != 'p':
            return False
            
        direction = -1 if piece.color == 'white' else 1
        
        # การเดินทางตรง
        if sc == ec:
            # First move: can move 1 or 2 squares
            if not piece.has_moved:
                # Move 1 square
                if er == sr + direction and 0 <= er < 8 and not board[er][ec]:
                    return True
                # Move 2 squares
                if er == sr + 2*direction and 0 <= er < 8 and not board[er][ec] and not board[sr + direction][sc]:
                    return True
            else:
                # Subsequent moves: only 1 square
                if er == sr + direction and 0 <= er < 8 and not board[er][ec]:
                    return True
        
        # การกินแนวทแยง
        elif abs(sc - ec) == 1 and er == sr + direction:
            target = board[er][ec]
            if target and target.color != piece.color:
                return True
                
        return False
    
    def get_piece_stats():
        """
        Get starting and max stats for Medieval Pawn
        """
        return {
            'dice': 2,
            'coins': 1,
            'max_stats': 12
        }
    
    return {
        'get_valid_moves': get_valid_moves,
        'get_piece_stats': get_piece_stats
    }

