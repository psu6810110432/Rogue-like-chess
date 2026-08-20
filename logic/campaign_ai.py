# logic/campaign_ai.py
"""
Campaign-level (Macro) AI for the Divide & Conquer game mode.

This module is responsible for making strategic decisions on the campaign
map for the AI-controlled faction (Black by default in PVE matches).
It is completely separate from the Classic Mode chess AI in ai_logic.py
and ai_controller.py, and does NOT alter their behavior in any way.

Phase 4: Economy, Recruitment, Upgrades & Army Movement — the AI
browses each owned node's shop, purchases affordable units, upgrades
buildings, evaluates army strength, and marches to conquer adjacent
neutral or enemy nodes.
"""
import math
import random
from kivy.clock import Clock
from kivy.app import App
from logic.campaign_helpers import generate_piece


class CampaignAI:
    """AI controller for the D&C campaign map."""

    # Delay (seconds) between each visual step of the AI's turn
    STEP_DELAY_SHORT = 1.0
    STEP_DELAY_LONG = 1.5

    # Minimum units the AI leaves behind when marching from a node
    MIN_GARRISON = 2

    def __init__(self):
        # Track all pending scheduled events so we can cancel them cleanly
        self._pending_events = []

    # ------------------------------------------------------------------
    # Public entry point — called by CampaignMapScreen.switch_turn()
    # ------------------------------------------------------------------
    def execute_turn(self, map_screen, faction):
        """
        Main entry point for an AI-controlled campaign turn.

        Runs a chained sequence of visual steps so the player can see
        the AI "thinking", then programmatically ends the turn.

        Parameters
        ----------
        map_screen : CampaignMapScreen
            The campaign map screen instance.
        faction : str
            The faction the AI is playing ('black').
        """
        # Guard: cancel any previously scheduled events (safety net)
        self.cancel()

        # Step 1 — Scroll to the AI's main base and show "analyzing"
        self._step_analyze(map_screen, faction)

    # ------------------------------------------------------------------
    # Chained turn steps
    # ------------------------------------------------------------------
    def _step_analyze(self, map_screen, faction):
        """Step 1: Pan camera to AI base, show 'ANALYZING' label."""
        map_screen.status_lbl.text = "[color=ff6644][b]AI IS ANALYZING...[/b][/color]"
        map_screen.status_lbl.color = (1, 0.4, 0.27, 1)

        self._scroll_to_faction_base(map_screen, faction)

        # 🟢 เปลี่ยนไปเรียก Phase จัดการเศรษฐกิจก่อน
        ev = Clock.schedule_once(
            lambda dt: self._step_trade_and_craft(map_screen, faction),
            self.STEP_DELAY_SHORT,
        )
        self._pending_events.append(ev)

    def _step_trade_and_craft(self, map_screen, faction):
        """Step 1.5: ตลาดและการคราฟต์อาวุธ (ทำงานเฉพาะโหมด Advanced Economy)"""
        app = App.get_running_app()
        if getattr(app, 'selected_economic_system', False):
            map_screen.status_lbl.text = "[color=ffff44][b]AI IS MANAGING ECONOMY...[/b][/color]"
            map_screen.status_lbl.color = (1, 1, 0.27, 1)
            
            # ✨ 1. เพิ่มบรรทัดนี้ ให้ AI สำรวจทรัพยากรและสลับโหมดฟาร์ม
            self.plan_resource_toggles(map_screen, faction)
            
            # เรียกใช้งานระบบการตลาดและการคราฟต์อาวุธ
            self.plan_trading(map_screen, faction)
            self.plan_crafting(map_screen, faction)
            
            delay = self.STEP_DELAY_SHORT
        else:
            delay = 0.1 # หากปิดโหมด Advanced ไว้ ให้ข้ามขั้นตอนนี้ไปไวๆ

        # เชื่อมต่อไปยัง Phase เกณฑ์ทหาร
        ev = Clock.schedule_once(
            lambda dt: self._step_recruit(map_screen, faction),
            delay,
        )
        self._pending_events.append(ev)

    def _step_recruit(self, map_screen, faction):
        """Step 2: Recruit units, show 'RECRUITING' label."""
        map_screen.status_lbl.text = (
            "[color=ff9944][b]AI IS RECRUITING...[/b][/color]"
        )
        map_screen.status_lbl.color = (1, 0.6, 0.27, 1)

        # Execute the actual recruitment logic
        self.plan_recruitment(map_screen, faction)

        # Chain → Step 3 (upgrades) after a longer delay so the player
        # can register that the AI recruited
        ev = Clock.schedule_once(
            lambda dt: self._step_upgrade(map_screen, faction),
            self.STEP_DELAY_LONG,
        )
        self._pending_events.append(ev)

    def _step_upgrade(self, map_screen, faction):
        """Step 3: Upgrade buildings, show 'UPGRADING' label."""
        map_screen.status_lbl.text = (
            "[color=44bbff][b]AI IS UPGRADING FACILITIES...[/b][/color]"
        )
        map_screen.status_lbl.color = (0.27, 0.73, 1, 1)

        # Execute the upgrade logic
        self.plan_upgrades(map_screen, faction)

        # Chain → Step 4 (march) after a delay
        ev = Clock.schedule_once(
            lambda dt: self._step_march(map_screen, faction),
            self.STEP_DELAY_LONG,
        )
        self._pending_events.append(ev)

    def _step_march(self, map_screen, faction):
        """Step 4: March armies, show 'MARCHING' label."""
        map_screen.status_lbl.text = (
            "[color=ff4444][b]AI IS MARCHING...[/b][/color]"
        )
        map_screen.status_lbl.color = (1, 0.27, 0.27, 1)

        # Execute the movement logic
        combat_started = self.plan_army_movements(map_screen, faction)

        if combat_started:
            # Combat transitions to the gameplay screen; the turn will
            # be auto-ended by CampaignMapScreen.on_enter() after the
            # battle resolves.
            self._pending_events.clear()
            return

        # No combat — chain to Step 5 (finish) after a delay
        ev = Clock.schedule_once(
            lambda dt: self._step_finish(map_screen, faction),
            self.STEP_DELAY_LONG,
        )
        self._pending_events.append(ev)

    def _step_finish(self, map_screen, faction):
        """Step 5: End the AI turn."""
        self._pending_events.clear()

        # end_turn(None) signals a programmatic call (not a button press),
        # so the human-player guard in end_turn() lets it through.
        map_screen.end_turn(None)

    # ------------------------------------------------------------------
    # Recruitment logic
    # ------------------------------------------------------------------
    def plan_recruitment(self, map_screen, faction):
        app = App.get_running_app()
        is_advanced = getattr(app, 'selected_economic_system', False)

        owned_nodes = sorted(
            [n for n in map_screen.nodes_list if n.faction == faction],
            key=lambda n: len(n.army_pieces),
        )
        if not owned_nodes: return

        # AI จะพยายามซื้อไปเรื่อยๆ จนกว่าจะไม่เหลือเงิน/ทรัพยากรพอซื้อตัวที่ถูกที่สุด
        purchases_made = True
        while purchases_made:
            purchases_made = False
            for node in owned_nodes:
                has_header = any(
                    p.__class__.__name__.lower() == 'king' or getattr(p, 'name', '') == 'Prince' or getattr(p, 'is_header', False)
                    for p in node.army_pieces
                )
                max_cap = 16 if has_header else 8
                if len(node.army_pieces) >= max_cap: continue

                # ส่ง app เข้าไปเช็คกระเป๋าแบบเต็มรูปแบบ
                bought = self._try_buy_from_node(app, node, faction, is_advanced)
                if bought: purchases_made = True

    def _try_buy_from_node(self, app, node, faction, is_advanced):
        addons = getattr(node, 'addons', {})
        tav_lvl = addons.get('tavern', 1)
        shop = getattr(node, 'shop_recruits', {})
        if not shop: return False

        shop_sources = [(shop, addons)]
        for sv in getattr(node, 'sub_villages', []):
            sv_shop = sv.get('shop_recruits', {})
            sv_addons = sv.get('addons', {})
            if sv_shop: shop_sources.append((sv_shop, sv_addons))

        candidates = []
        for src_shop, src_addons in shop_sources:
            src_tav_lvl = src_addons.get('tavern', 1)
            for row_key in ['row1', 'row2', 'row3', 'row4', 'row5']:
                row = src_shop.get(row_key)
                if row is None: continue
                if src_tav_lvl < row.get('req_lvl', 1): continue
                
                for idx, slot in enumerate(row['data']):
                    if slot is None: continue
                    base_cost = slot['cost']
                    final_tax_cost = self._get_discounted_price(base_cost, src_addons)
                    
                    # 🟢 ดึงโครงสร้างราคาของหมากตัวนี้
                    cost_dict = self._get_unit_costs(slot['name'], final_tax_cost, is_advanced)
                    
                    # 🟢 เช็คว่า AI สามารถจ่ายได้ครบทุกค่าหรือไม่
                    if self._can_afford(app, faction, cost_dict):
                        candidates.append((cost_dict, slot['name'], row_key, idx, src_shop, src_addons))

        if not candidates: return False

        random.shuffle(candidates)
        # จัดเรียงโดยให้ความสำคัญกับตัวที่ใช้ภาษีน้อยที่สุดก่อน
        candidates.sort(key=lambda c: c[0]['tax_points'])

        cost_dict, piece_name, row_key, idx, src_shop, src_addons = candidates[0]

        # 1. จ่ายทรัพยากร
        self._pay_costs(app, faction, cost_dict)
        
        # 2. นำของออกจาก Shop และเสกทหาร
        src_shop[row_key]['data'][idx] = None
        new_p = generate_piece(piece_name, faction, app)

        # 3. Apply weaponsmith / blacksmith bonuses
        spec = src_addons.get('special')
        slvl = src_addons.get('special_lvl', 0)

        if spec == 'weaponsmith':
            new_p.base_atk += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'atk_buff'
            new_p.second_hidden_passive.description = f"Weaponsmith Forged (+{slvl} ATK)"
        elif spec == 'blacksmith':
            new_p.base_def += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'def_buff'
            new_p.second_hidden_passive.description = f"Blacksmith Forged (+{slvl} DEF)"

        node.army_pieces.append(new_p)
        return True

    # ------------------------------------------------------------------
    # Army movement logic
    # ------------------------------------------------------------------
    def plan_army_movements(self, map_screen, faction):
        """
        Evaluate armies across owned nodes and march to conquer ONE
        adjacent non-allied node per turn.

        Returns True if combat was initiated (screen transitioned to
        gameplay), False otherwise.

        Mirrors the player's march flow:
          1. Remove marching units from source node (leave garrison)
          2. Set app.combat_marching_army and app.combat_marching_fatigue
          3. Call map_screen.initiate_combat(source, target)
        """
        app = App.get_running_app()

        owned_nodes = [
            n for n in map_screen.nodes_list if n.faction == faction
        ]
        if not owned_nodes:
            return False

        # Score every possible (source, target) attack pair
        best_source = None
        best_target = None
        best_score = -1

        for node in owned_nodes:
            army_size = len(node.army_pieces)
            # Need enough troops to leave a garrison AND still march
            if army_size <= self.MIN_GARRISON:
                continue
            # Exhausted armies cannot march
            if getattr(node, 'fatigue', 0) >= 6:
                continue

            for neighbor in getattr(node, 'neighbors', []):
                if neighbor.faction == faction:
                    continue  # skip friendly nodes

                score = 0
                # Prioritise neutral (red) nodes for early expansion
                if neighbor.faction == 'red':
                    score = 10
                else:
                    score = 5

                # Prefer targets we outnumber
                marchers = army_size - self.MIN_GARRISON
                target_strength = len(getattr(neighbor, 'army_pieces', []))
                if marchers > target_strength:
                    score += 5

                if marchers < target_strength:
                    continue

                # Prefer attacking with bigger armies
                score += marchers

                if score > best_score:
                    best_score = score
                    best_source = node
                    best_target = neighbor

        if best_source is None or best_target is None:
            return False

        # --- Form the marching army (mirrors campaign_panel.execute_action) ---

        # Keep the first MIN_GARRISON units as garrison, send the rest
        garrison = best_source.army_pieces[:self.MIN_GARRISON]
        marching_army = best_source.army_pieces[self.MIN_GARRISON:]
        best_source.army_pieces = garrison

        # Set up combat state (mirrors map_node.on_release enemy branch)
        source_fatigue = getattr(best_source, 'fatigue', 0)
        fatigue_cost = 2 if best_target.node_type == 'castle' else 1
        app.combat_marching_army = marching_army
        app.combat_marching_fatigue = min(6, source_fatigue + fatigue_cost)

        # Initiate the battle — this transitions to the gameplay screen
        map_screen.initiate_combat(best_source, best_target)
        return True

    # ------------------------------------------------------------------
    # Upgrade logic
    # ------------------------------------------------------------------
    def plan_upgrades(self, map_screen, faction):
        app = App.get_running_app()
        is_advanced = getattr(app, 'selected_economic_system', False)

        owned_nodes = [n for n in map_screen.nodes_list if n.faction == faction]
        if not owned_nodes: return

        # 🟢 ประเมินสถานะ End Game (มียึดปราสาทได้หลายเมือง หรือทรัพยากรล้นเหลือ)
        owned_castles = len([n for n in owned_nodes if n.node_type == 'castle'])
        wood = app.wood_points.get(faction, 0)
        iron = app.iron_points.get(faction, 0)
        is_endgame = (owned_castles >= 2) or (wood > 30 and iron > 20)

        upgraded = True
        while upgraded:
            upgraded = False
            candidates = []
            for node in owned_nodes:
                # 🟢 ส่งค่า is_endgame เข้าไปให้ฟังก์ชันลูกตัดสินใจ
                candidates.extend(self._collect_upgrade_candidates(node, is_advanced, is_endgame))

            if not candidates: break

            candidates.sort(key=lambda c: (c['priority'], c['cost_dict'].get('tax_points', 0)))

            for cand in candidates:
                if not self._can_afford(app, faction, cand['cost_dict']):
                    continue
                
                self._pay_costs(app, faction, cand['cost_dict'])
                
                if cand['key'] == 'new_building':
                    cand['node_ref'].building_state = f"building_{cand['b_name']}"
                else:
                    cand['addons'][cand['key']] += 1
                    
                upgraded = True
                break

    def _collect_upgrade_candidates(self, node, is_advanced, is_endgame):
        results = []

        def _scan_addons(addons):
            farm_lvl = addons.get('farm', 1)
            if farm_lvl < 3:
                cost_dict = self._get_building_costs('farm', farm_lvl, farm_lvl * 5, is_advanced)
                results.append({'key': 'farm', 'cost_dict': cost_dict, 'priority': 2, 'addons': addons})
            
            tav_lvl = addons.get('tavern', 1)
            if tav_lvl < 3:
                cost_dict = self._get_building_costs('tavern', tav_lvl, tav_lvl * 6, is_advanced)
                results.append({'key': 'tavern', 'cost_dict': cost_dict, 'priority': 3, 'addons': addons})
            
            spec = addons.get('special')
            spec_lvl = addons.get('special_lvl', 0)
            if spec and spec not in ['mine'] and spec_lvl < 3:
                cost_dict = self._get_building_costs('special_lvl', spec_lvl, spec_lvl * 8, is_advanced)
                results.append({'key': 'special_lvl', 'cost_dict': cost_dict, 'priority': 4, 'addons': addons})

        # 🟢 ลอจิกการเลือกสร้างตึกอย่างมีชั้นเชิง
        if node.node_type == 'castle' and getattr(node, 'building_state', None) is None:
            # เช็คว่าเมืองนี้ (หรือหมู่บ้านลูก) มีเหมือง (Mine) หรือไม่
            has_mine = False
            if getattr(node, 'addons', {}).get('special') == 'mine': has_mine = True
            for sv in getattr(node, 'sub_villages', []):
                if sv.get('addons', {}).get('special') == 'mine': has_mine = True
                
            # ตัดสินใจสร้างตึกตามสถานการณ์
            if is_endgame:
                b_name, b_cost = 'wallbuilder', 15    # ท้ายเกม: สร้างกำแพงเตรียมรับมือศัตรู
            elif has_mine:
                b_name, b_cost = 'makerspace', 12     # มีเหมือง: สร้างที่คราฟต์เพื่อแปรรูปแร่
            else:
                b_name, b_cost = 'market', 10         # ไม่มีเหมือง: สร้างตลาดเพื่อซื้อแร่มาทดแทน
                
            cost_dict = self._get_building_costs(f"new_{b_name}", 1, b_cost, is_advanced)
            results.append({
                'key': 'new_building', 
                'b_name': b_name, 
                'cost_dict': cost_dict, 
                'priority': 1, 
                'node_ref': node 
            })

        main_addons = getattr(node, 'addons', {})
        if main_addons: _scan_addons(main_addons)

        for sv in getattr(node, 'sub_villages', []):
            sv_addons = sv.get('addons', {})
            if sv_addons: _scan_addons(sv_addons)

        return results
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_discounted_price(base_cost, addons):
        """
        Replica of CampaignArmyPanel.get_discounted_price() — computes
        the final recruitment cost after applying statue discounts.
        """
        if addons.get('special') == 'statue':
            lvl = addons.get('special_lvl', 1)
            if lvl == 1:
                discount = 1
            elif lvl == 2:
                discount = 2
            elif lvl >= 3:
                discount = math.ceil(base_cost / 2)
            else:
                discount = 0
            max_discount = math.ceil(base_cost / 2)
            actual_discount = min(discount, max_discount)
            return max(1, base_cost - actual_discount)
        return base_cost

    @staticmethod
    def _get_node_capacity(node):
        """Return the maximum army size for a node."""
        has_header = any(
            p.__class__.__name__.lower() == 'king'
            or getattr(p, 'name', '') == 'Prince'
            or getattr(p, 'is_header', False)
            for p in node.army_pieces
        )
        return 16 if has_header else 8

    def _scroll_to_faction_base(self, map_screen, faction):
        """Pan the ScrollView to center on the faction's main base."""
        target_node = next(
            (n for n in map_screen.nodes_list
             if n.faction == faction and n.is_main_base),
            None,
        )
        if target_node and map_screen.map_content.width > 0:
            map_screen.scroll_view.scroll_x = (
                target_node.x / map_screen.map_content.width
            )
            map_screen.scroll_view.scroll_y = (
                target_node.y / map_screen.map_content.height
            )

    # ==================================================================
    # Trading & Crafting Logic
    # ==================================================================
    def plan_trading(self, map_screen, faction):
        """ลอจิกสำหรับซื้อทรัพยากรจากตลาด (Market)"""
        app = App.get_running_app()
        owned_nodes = [n for n in map_screen.nodes_list if n.faction == faction]
        
        # ค้นหาว่ามีเมืองไหนสร้าง Market ไว้ไหม
        market_nodes = [n for n in owned_nodes if getattr(n, 'building_state', '') == 'market']
        if not market_nodes: return
        
        market = market_nodes[0]
        rates = getattr(market, 'market_rates', {})
        if not rates: return

        # 🟢 กำหนดเป้าหมายตุนทรัพยากรให้ AI (อิงจากคีย์ใน Maker Rate ของคุณ)
        # รูปแบบ: 'ตัวแปรในกระเป๋า': ('คีย์ในตลาด', จำนวนที่อยากตุนไว้ในคลัง)
        target_stock = {
            'wood_points': ('wood', 15), 
            'iron_points': ('iron', 10),
            'coal_points': ('coal', 5),
            'silver_points': ('silver', 3), # ตุนเงินไว้เผื่อหลอมเหล็ก
            'gold_points': ('gold', 2),     # ตุนทองไว้เผื่อหลอมเหล็ก
            'weapon_t1_points': ('weapon_t1', 3), 
            'weapon_t2_points': ('weapon_t2', 2),
            'weapon_t3_points': ('weapon_t3', 1)
        }

        budget = app.tax_points.get(faction, 0)
        
        for res_name, (rate_key, target_amount) in target_stock.items():
            current = getattr(app, res_name, {}).get(faction, 0)
            cost_per_unit = rates.get(rate_key, 999) # ดึงราคาแบบสุ่ม (Swing) ที่คุณตั้งไว้
            
            while current < target_amount and budget >= cost_per_unit:
                budget -= cost_per_unit
                current += 1
                getattr(app, res_name)[faction] = current
                
        app.tax_points[faction] = budget

    def plan_crafting(self, map_screen, faction):
        """ลอจิกสำหรับคราฟต์อาวุธที่ Makerspace ตามสูตรเป๊ะๆ"""
        app = App.get_running_app()
        owned_nodes = [n for n in map_screen.nodes_list if n.faction == faction]
        
        # ค้นหาว่ามีเมืองไหนสร้าง Makerspace ไว้ไหม
        makerspace_nodes = [n for n in owned_nodes if getattr(n, 'building_state', '') == 'makerspace']
        if not makerspace_nodes: return

        # 🟢 1. แปรรูปแร่ดิบเป็นเหล็ก (Iron) ถ้าเหล็กน้อยกว่า 15 และมีเงิน Tax พอจ่ายค่าคราฟต์
        while app.iron_points.get(faction, 0) < 15 and app.tax_points.get(faction, 0) >= 2:
            if getattr(app, 'gold_points', {}).get(faction, 0) >= 1:
                # 1 Gold + 2 Tax -> 3 Iron
                app.gold_points[faction] -= 1
                app.tax_points[faction] -= 2
                app.iron_points[faction] = app.iron_points.get(faction, 0) + 3
            elif getattr(app, 'silver_points', {}).get(faction, 0) >= 1:
                # 1 Silver + 2 Tax -> 1 Iron
                app.silver_points[faction] -= 1
                app.tax_points[faction] -= 2
                app.iron_points[faction] = app.iron_points.get(faction, 0) + 1
            elif getattr(app, 'coal_points', {}).get(faction, 0) >= 2:
                # 2 Coal + 2 Tax -> 1 Iron
                app.coal_points[faction] -= 2
                app.tax_points[faction] -= 2
                app.iron_points[faction] = app.iron_points.get(faction, 0) + 1
            else:
                break # วัตถุดิบในการหลอมเหล็กหมดแล้ว

        # 🟢 2. คราฟต์อาวุธตามสูตรใหม่
        # รูปแบบ: ('ชื่อตัวแปร', {'ทรัพยากรที่ต้องจ่าย': จำนวน}, จำนวนที่จะตุน)
        crafting_recipes = [
            # 6 Wood + 4 Iron = Wep T3
            ('weapon_t3_points', {'wood_points': 6, 'iron_points': 4}, 2),  
            # 4 Wood + 3 Iron = Wep T2
            ('weapon_t2_points', {'wood_points': 4, 'iron_points': 3}, 3),  
            # 2 Wood + 3 Iron = Wep T1
            ('weapon_t1_points', {'wood_points': 2, 'iron_points': 3}, 5)   
        ]

        for wp_name, cost_dict, target_amount in crafting_recipes:
            current_wp = getattr(app, wp_name, {}).get(faction, 0)
            
            while current_wp < target_amount and self._can_afford(app, faction, cost_dict):
                # หักทรัพยากรทิ้ง
                self._pay_costs(app, faction, cost_dict)
                # เพิ่มอาวุธเข้าคลัง
                current_wp += 1
                getattr(app, wp_name)[faction] = current_wp

    def _get_unit_costs(self, piece_name, base_cost, is_advanced):
        """คำนวณราคาทหารเป็นแบบตระกร้าทรัพยากร"""
        if not is_advanced:
            return {'tax_points': base_cost}
            
        # 🟢 Pawn กับ Levies ใช้แค่เงิน (Tax) อย่างเดียว
        costs = {'tax_points': base_cost}
        p_name = piece_name.lower()
        
        if p_name in ['levies', 'pawn']:
            return costs
            
        # 🟢 ทหารระดับสูงขึ้นไป ต้องกินเสบียงและใช้อาวุธ
        costs['supplies_points'] = 2
        
        if p_name in ['menatarm', 'hastati', 'knight']:
            costs['weapon_t2_points'] = 1
        elif p_name in ['bishop', 'rook', 'queen', 'praetorian', 'royalguard']:
            costs['weapon_t3_points'] = 1
            costs['supplies_points'] = 4
        else:
            costs['weapon_t1_points'] = 1 # เผื่อคลาสอื่นๆ ที่หลุดมา
            
        return costs

    def _get_building_costs(self, key, level, base_cost, is_advanced):
        """คำนวณราคาสิ่งปลูกสร้างเป็นแบบตระกร้าทรัพยากร"""
        if not is_advanced:
            return {'tax_points': base_cost}
            
        costs = {'tax_points': base_cost}
        if key == 'farm':
            costs['wood_points'] = level * 2
        elif key == 'tavern':
            costs['wood_points'] = level * 3
            costs['iron_points'] = level * 1
        elif key == 'special_lvl': 
            costs['wood_points'] = level * 2
            costs['iron_points'] = level * 2
            
        # 🟢 เพิ่มราคาสร้างตึกใหม่ (Market, Makerspace, Wallbuilder)
        elif key == 'new_market':
            costs = {'wood_points': 3}
        elif key == 'new_makerspace':
            costs = {'wood_points': 4}
        elif key == 'new_wallbuilder':
            costs = {'wood_points': 9}
            
        return costs

    def _can_afford(self, app, faction, cost_dict):
        """เช็คว่า AI มีทรัพยากรทุกชนิดใน cost_dict เพียงพอหรือไม่"""
        for res_name, required_amount in cost_dict.items():
            current_amount = getattr(app, res_name, {}).get(faction, 0)
            if current_amount < required_amount:
                return False
        return True

    def _pay_costs(self, app, faction, cost_dict):
        """หักทรัพยากรทั้งหมดใน cost_dict ออกจากกระเป๋า AI"""
        for res_name, required_amount in cost_dict.items():
            res_dict = getattr(app, res_name, {})
            current_amount = res_dict.get(faction, 0)
            res_dict[faction] = max(0, current_amount - required_amount)

    def plan_resource_toggles(self, map_screen, faction):
        """ลอจิกปรับโหมดฟาร์มและเหมืองตามความต้องการทรัพยากร"""
        app = App.get_running_app()
        wood = app.wood_points.get(faction, 0)
        iron = app.iron_points.get(faction, 0)
        
        # 🟢 ถ้าทรัพยากรมีเยอะพอสมควรแล้ว ให้บังคับกลับไปเก็บภาษี (Tax)
        need_resources = True
        if wood >= 25 and iron >= 15:
            need_resources = False
        
        owned_nodes = [n for n in map_screen.nodes_list if n.faction == faction]
        for node in owned_nodes:
            addons = getattr(node, 'addons', {})
            if addons.get('farm', 0) > 0:
                addons['farm_mode'] = 'resources' if need_resources else 'tax'
            if addons.get('special') == 'mine':
                addons['mine_mode'] = 'resources' if need_resources else 'tax'
                
            for sv in getattr(node, 'sub_villages', []):
                sv_addons = sv.get('addons', {})
                if sv_addons.get('farm', 0) > 0:
                    sv_addons['farm_mode'] = 'resources' if need_resources else 'tax'
                if sv_addons.get('special') == 'mine':
                    sv_addons['mine_mode'] = 'resources' if need_resources else 'tax'

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cancel(self):
        """Cancel all pending AI actions (e.g. if the player quits mid-turn)."""
        for ev in self._pending_events:
            ev.cancel()
        self._pending_events.clear()
