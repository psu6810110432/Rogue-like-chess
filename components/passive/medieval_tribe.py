# Medieval Tribe - ความสามารถพิเศษของเผ่า Medieval

def medieval_knight_passive():
    """
    Knight passive ability for Medieval tribe
    - Moves in L-shape: 2 vertical + 1 horizontal OR 2 horizontal + 1 vertical
    - Starting stats: 2 dice, 1 coin
    - Max stats: 12
    """
    def get_valid_moves(start, end, board):
        """
        Check if move is valid for Medieval Knight
        start: start position (row, col)
        end: target position (row, col)
        board: game board state
        """
        sr, sc = start
        er, ec = end
        
        # ดึง piece จาก board
        piece = board[sr][sc]
        if not piece or piece.name.lower() != 'n':
            return False
            
        # ตรวจสอบขอบเขตกระดาน
        if not (0 <= er < 8 and 0 <= ec < 8):
            return False
            
        # คำนวณระยะทาง
        row_diff = abs(sr - er)
        col_diff = abs(sc - ec)
        
        # ตรวจสอบการเดินแบบ L-shape
        is_l_shape = (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
        
        if not is_l_shape:
            return False
            
        # ตรวจสอบว่าช่องเป้าหมายไม่มีหมากฝ่ายเดียวกัน
        target = board[er][ec]
        if target and target.color == piece.color:
            return False
            
        return True
    
    def get_piece_stats():
        """
        Get starting stats for Medieval Knight
        """
        return {
            'dice': 2,
            'coins': 1
        }
    
    return {
        'get_valid_moves': get_valid_moves,
        'get_piece_stats': get_piece_stats
    }

