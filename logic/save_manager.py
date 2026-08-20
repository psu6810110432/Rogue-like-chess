# logic/save_manager.py
import sqlite3
import os
import datetime

DB_PATH = 'rogue_chess_save.db'

def get_connection():
    """สร้างและคืนค่า Connection ของ SQLite"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """สร้างตารางที่จำเป็นหากยังไม่มีในระบบ"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. ตาราง World State (เพิ่ม white_tribe และ black_tribe)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS worlds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_name TEXT NOT NULL,
            map_size TEXT,
            map_seed INTEGER,
            current_turn INTEGER DEFAULT 1,
            active_faction TEXT,
            match_type TEXT DEFAULT 'LOCAL_PVP',  
            economic_system BOOLEAN DEFAULT 0,    
            ai_difficulty TEXT DEFAULT 'normal',  
            is_autosave BOOLEAN DEFAULT 0,
            is_suspended BOOLEAN DEFAULT 0,
            last_played TIMESTAMP,
            white_tribe TEXT DEFAULT 'the knight company',
            black_tribe TEXT DEFAULT 'the chaos mankind'
        )
    ''')
    # ... โค้ดสร้างตารางอื่นๆ เหมือนเดิม ...

    # 2. ตาราง Factions (เก็บทรัพยากรของแต่ละสีใน World นั้น)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id INTEGER,
            faction_name TEXT,
            tax_points INTEGER DEFAULT 0,
            supplies_points INTEGER DEFAULT 0,
            weapon_t1 INTEGER DEFAULT 0,
            weapon_t2 INTEGER DEFAULT 0,
            weapon_t3 INTEGER DEFAULT 0,
            wood_points INTEGER DEFAULT 0,     
            iron_points INTEGER DEFAULT 0,     
            coal_points INTEGER DEFAULT 0,     
            silver_points INTEGER DEFAULT 0,   
            gold_points INTEGER DEFAULT 0,     
            FOREIGN KEY(world_id) REFERENCES worlds(id) ON DELETE CASCADE
        )
    ''')

    # 3. ตาราง Nodes (เก็บสถานะเมืองและสิ่งปลูกสร้าง)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id INTEGER,
            node_index INTEGER,
            faction TEXT,
            node_type TEXT,
            loyalty INTEGER,
            fatigue INTEGER,
            farm_lvl INTEGER DEFAULT 1,
            tavern_lvl INTEGER DEFAULT 1,
            special_type TEXT,
            special_lvl INTEGER DEFAULT 0,
            building_state TEXT,               
            wallbuilder_cooldown INTEGER DEFAULT 0, 
            FOREIGN KEY(world_id) REFERENCES worlds(id) ON DELETE CASCADE
        )
    ''')

    # 4. ตาราง Units (เก็บทหารที่ประจำการในแต่ละ Node)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id INTEGER,
            piece_class TEXT,
            upgrade_level INTEGER DEFAULT 0,
            item_id INTEGER,
            is_commander BOOLEAN DEFAULT 0,
            FOREIGN KEY(node_id) REFERENCES nodes(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# เพิ่มต่อใน logic/save_manager.py

def save_game(app, map_screen, save_name, is_autosave=False, is_suspended=False):
    """
    บันทึกสถานะเกมปัจจุบันลง Database
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # อนุญาตให้ใช้งาน Foreign Key เพื่อให้ลบข้อมูลเกี่ยวเนื่องได้ง่าย
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. ตรวจสอบว่าเป็นการเขียนทับ Autosave เดิมหรือไม่
    if is_autosave:
        cursor.execute("DELETE FROM worlds WHERE is_autosave = 1")
    
    # บันทึกข้อมูลภาพรวม (World)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # หากไม่ได้ตั้งชื่อเซฟ ให้ใช้วันเวลา
    final_save_name = save_name if save_name else f"Autosave {timestamp}" if is_autosave else f"World {timestamp}"

    # ใช้ getattr ดึงค่า ถ้าไม่มีให้ใช้ 'Medium' เป็นค่าเริ่มต้น
    map_size = getattr(app, 'selected_map_size', 'Medium')

    # ใช้ getattr ดึงค่า ถ้าไม่มีให้ใช้ 'Medium' เป็นค่าเริ่มต้น
    map_size = getattr(app, 'selected_map_size', 'Medium')
    
    # 🟢 เพิ่มการดึงค่าตัวแปรให้ครอบคลุมและตรงกับ App 100%
    current_turn = getattr(app, 'turn_number', getattr(map_screen, 'current_turn', getattr(map_screen, 'turn_count', 1)))
    active_faction = getattr(app, 'current_map_turn', getattr(map_screen, 'current_faction', getattr(map_screen, 'active_faction', 'white')))
    map_seed = getattr(app, 'current_map_seed', 0)

    # ดึงการตั้งค่าห้องจาก App
    match_type = getattr(app, 'match_type', 'LOCAL_PVP')
    econ_system = 1 if getattr(app, 'selected_economic_system', False) else 0
    ai_diff = getattr(app, 'ai_difficulty', 'normal')

    # 🟢 ดึงข้อมูลเผ่าของทั้ง 2 ฝ่าย (ถ้าหาไม่เจอให้ใช้ค่าเริ่มต้น)
    w_tribe = getattr(app, 'white_tribe', 'the knight company')
    b_tribe = getattr(app, 'black_tribe', 'the chaos mankind')

    cursor.execute('''
        INSERT INTO worlds (save_name, map_size, map_seed, current_turn, active_faction, match_type, economic_system, ai_difficulty, is_autosave, is_suspended, last_played)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (final_save_name, map_size, map_seed, current_turn, active_faction, match_type, econ_system, ai_diff, is_autosave, is_suspended, timestamp))
    
    world_id = cursor.lastrowid

    # ✨ เพิ่มบรรทัดนี้เข้าไป! เพื่อบังคับให้เกมรู้ตัวว่า ID เซฟปัจจุบันถูกเปลี่ยนแล้ว
    app.loaded_world_id = world_id

    # 2. บันทึกทรัพยากร (Factions)
    for faction in ['white', 'black', 'red']:
        cursor.execute('''
            INSERT INTO factions (world_id, faction_name, tax_points, supplies_points, weapon_t1, weapon_t2, weapon_t3, wood_points, iron_points, coal_points, silver_points, gold_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            world_id, faction,
            app.tax_points.get(faction, 0),
            app.supplies_points.get(faction, 0),
            app.weapon_t1_points.get(faction, 0),
            app.weapon_t2_points.get(faction, 0),
            app.weapon_t3_points.get(faction, 0),
            getattr(app, 'wood_points', {}).get(faction, 0), 
            getattr(app, 'iron_points', {}).get(faction, 0),
            getattr(app, 'coal_points', {}).get(faction, 0),
            getattr(app, 'silver_points', {}).get(faction, 0),
            getattr(app, 'gold_points', {}).get(faction, 0)
        ))

    # 3. บันทึกแผนที่และสิ่งปลูกสร้าง (Nodes)
    for index, node in enumerate(map_screen.nodes_list):
        addons = getattr(node, 'addons', {})
        
        # ดึงสถานะตึกที่สร้างระหว่างเกม
        b_state = getattr(node, 'building_state', None)
        wb_cd = getattr(node, 'wallbuilder_cooldown', 0)

        cursor.execute('''
            INSERT INTO nodes (world_id, node_index, faction, node_type, loyalty, fatigue, farm_lvl, tavern_lvl, special_type, special_lvl, building_state, wallbuilder_cooldown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            world_id, index, node.faction, node.node_type, 
            getattr(node, 'loyalty', 100), getattr(node, 'fatigue', 0),
            addons.get('farm', 1), addons.get('tavern', 1),
            addons.get('special', None), addons.get('special_lvl', 0),
            b_state, wb_cd  # 🟢 ยัดค่าที่ดึงมาลง Database
        ))
        
        node_id = cursor.lastrowid

        # 4. บันทึกทหารใน Node นั้นๆ (Units)
        for piece in node.army_pieces:
            piece_class = piece.__class__.__name__
            item_id = piece.item.id if getattr(piece, 'item', None) else None
            is_cmd = 1 if piece_class.lower() == 'king' or getattr(piece, 'is_header', False) else 0
            
            cursor.execute('''
                INSERT INTO units (node_id, piece_class, upgrade_level, item_id, is_commander)
                VALUES (?, ?, ?, ?, ?)
            ''', (node_id, piece_class, getattr(piece, 'upgrade_level', 0), item_id, is_cmd))

    conn.commit()
    conn.close()
    print(f"[Save Manager] บันทึกข้อมูลสำเร็จ: {final_save_name}")

# เพิ่มต่อท้ายไฟล์ logic/save_manager.py

def get_suspended_save():
    """เช็คว่ามีเซฟที่ค้างอยู่ (Crash/Suspended) หรือไม่"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, save_name FROM worlds WHERE is_suspended = 1 ORDER BY last_played DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row  # จะคืนค่า (id, save_name) หรือ None ถ้าไม่มี

def clear_suspended_status(world_id):
    """เคลียร์สถานะค้าง เพื่อให้กลายเป็นเซฟปกติเมื่อผู้เล่นกด No"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE worlds SET is_suspended = 0 WHERE id = ?", (world_id,))
    conn.commit()
    conn.close()

def get_all_saves():
    """ดึงข้อมูลเซฟทั้งหมดมาแสดงในหน้า Load Game (สูงสุด 3 ช่อง)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, save_name, current_turn, last_played, is_autosave FROM worlds ORDER BY last_played DESC LIMIT 3")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_save(world_id):
    """ลบเซฟทิ้ง"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM worlds WHERE id = ?", (world_id,))
    conn.commit()
    conn.close()

def rename_save(world_id, new_name):
    """เปลี่ยนชื่อเซฟ (Edit)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE worlds SET save_name = ? WHERE id = ?", (new_name, world_id))
    conn.commit()
    conn.close()

def load_game_data(world_id):
    """ดึงข้อมูลทั้งหมดของ World ID นั้นๆ ออกมาจาก Database"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # ทำให้ดึงค่าผ่านชื่อคอลัมน์ได้ (เช่น row['tax_points'])
    cursor = conn.cursor()

    # 1. ดึงข้อมูล World
    cursor.execute("SELECT * FROM worlds WHERE id = ?", (world_id,))
    world_row = cursor.fetchone()
    if not world_row:
        conn.close()
        return None
    world_data = dict(world_row)

    # 2. ดึงข้อมูล Factions
    cursor.execute("SELECT * FROM factions WHERE world_id = ?", (world_id,))
    factions_data = [dict(row) for row in cursor.fetchall()]

    # 3. ดึงข้อมูล Nodes
    cursor.execute("SELECT * FROM nodes WHERE world_id = ?", (world_id,))
    nodes_data = [dict(row) for row in cursor.fetchall()]

    # 4. ดึงข้อมูล Units ทั้งหมดที่อยู่ใน World นี้
    cursor.execute("""
        SELECT u.* FROM units u 
        JOIN nodes n ON u.node_id = n.id 
        WHERE n.world_id = ?
    """, (world_id,))
    units_data = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'world': world_data,
        'factions': factions_data,
        'nodes': nodes_data,
        'units': units_data
    }

# เรียกใช้ทันทีเมื่อมีการ import ไฟล์นี้
init_db()
