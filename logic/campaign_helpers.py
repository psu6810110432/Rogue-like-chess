# logic/campaign_helpers.py
import math
from logic.pieces import Pawn, Knight, Bishop, Rook, Queen, King, Prince
from logic.pieces import Princess, Menatarm, Praetorian, Royalguard, Hastati, Levies
from components.hidden_passive import HiddenPassive

def check_rect_overlap(r1, r2):
    x1, y1, w1, h1 = r1; x2, y2, w2, h2 = r2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

def is_overlapping_any(rect, rect_list):
    for r in rect_list:
        if check_rect_overlap(rect, r): return True
    return False

def get_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def generate_piece(piece_name, faction, app):
    theme = getattr(app, f'selected_unit_{faction}', 'Medieval Knights') if faction != 'red' else 'Bandit'
    
    theme_map = {
        "Medieval Knights": "the knight company",
        "Heaven": "the ancient runes",
        "Ayothaya": "the chaos mankind",
        "Demon": "the deep anomaly",
        "Bandit": "bandit"
    }
    tribe = theme_map.get(theme, theme.lower())
    color = faction if faction in ['white', 'black'] else 'black'
    
    classes = {
        'pawn': Pawn, 'knight': Knight, 'bishop': Bishop, 'rook': Rook, 'queen': Queen, 'king': King, 'prince': Prince,
        'princess': Princess, 'menatarm': Menatarm, 'praetorian': Praetorian, 'royalguard': Royalguard,
        'hastati': Hastati, 'levies': Levies
    }
    
    p = classes[piece_name](color, tribe)
    if piece_name == 'prince': p.name = "Prince" 
    
    if not hasattr(p, 'hidden_passive') or p.hidden_passive is None:
        p.hidden_passive = HiddenPassive()
        p.base_points, p.coins = p.hidden_passive.apply_passive(p.base_points, p.coins)
    
    p.base_atk = getattr(p, 'base_atk', p.base_points)
    p.base_def = getattr(p, 'base_def', p.base_points)
    p.is_header = False 
    return p

def clone_piece(p, faction, app):
    p_name = p.__class__.__name__.lower()
    if getattr(p, 'name', '') == 'Prince': p_name = 'prince'
    elif getattr(p, 'name', '') == 'Garrison Commander': p_name = 'king' 
    
    new_p = generate_piece(p_name, faction, app)
    new_p.base_points = p.base_points
    new_p.coins = p.coins
    new_p.item = getattr(p, 'item', None)
    new_p.hidden_passive = getattr(p, 'hidden_passive', None)
    new_p.second_hidden_passive = getattr(p, 'second_hidden_passive', None)
    new_p.base_atk = getattr(p, 'base_atk', p.base_points)
    new_p.base_def = getattr(p, 'base_def', p.base_points)
    new_p.upgrade_level = getattr(p, 'upgrade_level', 0)
    new_p.upgrade_path = getattr(p, 'upgrade_path', 'standard')
    return new_p

def ensure_header(army_list, faction, app):
    has_header = any(p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False) for p in army_list)
    if not has_header and army_list:
        army_list[0].is_header = True
        
        def king_move(s, e, b, ep=None):
            if s == e: return False
            if getattr(army_list[0], 'item', None) and army_list[0].item.id == 9 and army_list[0].check_knight_move(s, e): return True
            return max(abs(s[0]-e[0]), abs(s[1]-e[1])) == 1
            
        army_list[0].is_valid_move = king_move
        army_list[0].name = f"{army_list[0].__class__.__name__.capitalize()} (Commander)"

def clear_temp_headers(army_list):
    for p in army_list:
        if getattr(p, 'is_header', False):
            p.is_header = False
            if "(Commander)" in getattr(p, 'name', ''):
                p.name = p.__class__.__name__.capitalize()

# เพิ่มต่อท้ายไฟล์ logic/campaign_helpers.py

def resolve_map_battle(app, map_screen):
    """จัดการผลสรุปหลังจบการต่อสู้ในโหมดแคมเปญ"""
    src = app.combat_source
    tgt = app.combat_target
    winner = app.battle_winner
    
    clean_atk = [clone_piece(p, src.faction, app) for p in app.survivors_atk]
    clean_def = [clone_piece(p, tgt.faction, app) for p in app.survivors_def]
    clear_temp_headers(clean_atk)
    clear_temp_headers(clean_def)
    
    def had_real_king(army): 
        return any(p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' for p in army) and not any(getattr(p, 'is_header', False) for p in army)
    
    atk_had_king = had_real_king(app.combat_marching_army)
    atk_has_king = had_real_king(app.survivors_atk)
    def_had_king = had_real_king(app.combat_target_army)
    def_has_king = had_real_king(app.survivors_def)
    
    # 1. เงื่อนไขการตายของแม่ทัพ
    if atk_had_king and not atk_has_king and src.faction in ['white', 'black']:
        map_screen.show_game_over(winner_faction=tgt.faction, reason="ATTACKING KING KILLED")
        return True
    if def_had_king and not def_has_king and tgt.faction in ['white', 'black']:
        map_screen.show_game_over(winner_faction=src.faction, reason="DEFENDING KING KILLED")
        return True
        
    # 2. คำนวณพื้นที่
    if winner == 'attacker':
        orig_tgt_faction = tgt.faction
        if tgt.is_main_base and tgt.faction in ['white', 'black']:
            map_screen.show_game_over(winner_faction=src.faction, reason="MAIN BASE CAPTURED")
            return True
            
        tgt.faction = src.faction
        tgt.army_pieces = clean_atk
        tgt.loyalty = 100 
        tgt.update_graphics()
        
        if tgt.node_type == 'castle' and orig_tgt_faction == 'red':
            app.prince_rewards[src.faction] += 1
        
        map_screen.status_lbl.text = f"[color=00ff00]VICTORY! YOU CAPTURED {tgt.node_id}.[/color]"
        
        if orig_tgt_faction in ['white', 'black'] and clean_def:
            retreat_node = map_screen.get_nearest_friendly_base(tgt)
            if retreat_node:
                retreat_node.army_pieces.extend(clean_def)
                map_screen.status_lbl.text += f" ENEMY RETREATED TO {retreat_node.node_id}."
                
    elif winner == 'defender':
        tgt.army_pieces = clean_def
        if src.faction in ['white', 'black']:
            if clean_atk:
                src.army_pieces.extend(clean_atk)
                map_screen.status_lbl.text = f"[color=ff0000]DEFEAT! YOUR ARMY RETREATED TO {src.node_id}.[/color]"
            else:
                map_screen.status_lbl.text = f"[color=ff0000]CRUSHING DEFEAT! ARMY DESTROYED.[/color]"
    else: # เสมอ
        tgt.army_pieces = clean_def
        if src.faction in ['white', 'black']: 
            src.army_pieces.extend(clean_atk)
            
    app.battle_finished = False
    return False