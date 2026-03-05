# logic/crash_logic.py
import random

def toss_coin_ayothaya():
    if random.random() < 0.30:
        return 0, "Tails"
    if random.random() < 0.60:
        if random.random() < 0.60:
            return 1, "Yellow Heads"
        else:
            if random.random() < 0.30:
                if random.random() < 0.70:
                    return 2, "Red Heads"
                else:
                    return 3, "Blue Heads"
            else:
                return 2, "Red Heads"
    else:
        return 1, "Yellow Heads"

def toss_coin_medieval():
    if random.random() < 0.50:
        return 0, "Tails"
    if random.random() < 0.01:
        if random.random() < 0.01:
            return 100, "Green Heads"
        else:
            return 10, "Cyan Heads"
    else:
        return 10, "Cyan Heads"

def toss_coin_demon():
    if random.random() < 0.40:
        return -3, "Tails"
    if random.random() < 0.20:
        if random.random() < 0.20:
            return 4, "Purple Heads"
        else:
            return 6, "Orange Heads"
    else:
        return 6, "Orange Heads"

def toss_coin_heaven():
    if random.random() < 0.50:
        return 0, "Tails"
    else:
        return 1, "Yellow Heads"

def calculate_total_points(base_points, num_coins, faction):
    total = base_points
    results = []
    heads_count = 0
    for _ in range(num_coins):
        if faction == "medieval":
            p, color = toss_coin_medieval()
        elif faction == "demon":
            p, color = toss_coin_demon()
        elif faction == "heaven":
            p, color = toss_coin_heaven()
        else:
            p, color = toss_coin_ayothaya()
            
        total += p
        results.append(color)
        if "Heads" in color: heads_count += 1

    if faction == "heaven":
        if heads_count >= 3: total += 3
        if heads_count >= 6: total += 3
        if heads_count >= 9: total += 3

    if faction == "demon" and total <= -3:
        total = abs(total)
            
    return total, results

def resolve_crash(p1_name, p1_faction, p1_base, p1_coins, p2_name, p2_faction, p2_base, p2_coins):
    while True:
        p1_total, p1_results = calculate_total_points(p1_base, p1_coins, p1_faction)
        p2_total, p2_results = calculate_total_points(p2_base, p2_coins, p2_faction)
    
    winner = None
    if p1_total > p2_total: winner = p1_name
    elif p2_total > p1_total: winner = p2_name
        
    return {
        "p1": {"name": p1_name, "faction": p1_faction, "total": p1_total, "results": p1_results},
        "p2": {"name": p2_name, "faction": p2_faction, "total": p2_total, "results": p2_results},
        "winner": winner
    }

def simulate_ai_crash_result(attacker, defender, a_faction, d_faction):
    """จำลองผลการต่อสู้สำหรับ AI (รองรับระบบ Draw/Stagger และ Item)"""
    a_base = getattr(attacker, 'base_points', 5)
    a_coins = getattr(attacker, 'coins', 3)
    d_base = getattr(defender, 'base_points', 5)
    d_coins = getattr(defender, 'coins', 3)
    
    # ไอเทมที่มีผลก่อนเริ่ม Crash
    if getattr(defender, 'item', None) and defender.item.id == 4:
        return "blocked" # โล่สะท้อนการโจมตี
    if getattr(defender, 'item', None) and defender.item.id == 8: a_coins = max(0, a_coins - 1)
    if getattr(attacker, 'item', None) and attacker.item.id == 8: d_coins = max(0, d_coins - 1)
    if getattr(defender, 'item', None) and defender.item.id == 2: a_coins = 0

    stagger_count = 0
    while True:
        a_tot, _ = calculate_total_points(a_base, a_coins, a_faction)
        d_tot, _ = calculate_total_points(d_base, d_coins, d_faction)
        
        if a_tot > d_tot: return "win"
        elif a_tot == d_tot: continue
        else:
            stagger_count += 1
            if stagger_count >= 2: return "died"