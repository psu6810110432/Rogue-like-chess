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

        upgraded = True
        while upgraded:
            upgraded = False
            candidates = []
            for node in owned_nodes:
                candidates.extend(self._collect_upgrade_candidates(node, is_advanced))

            if not candidates: break

            # เรียงตามลำดับความสำคัญ (priority) และราคาภาษี
            candidates.sort(key=lambda c: (c['priority'], c['cost_dict']['tax_points']))

            for cand in candidates:
                if not self._can_afford(app, faction, cand['cost_dict']):
                    continue
                
                # จ่ายทรัพยากร
                self._pay_costs(app, faction, cand['cost_dict'])
                
                # 🟢 เช็คว่าเป็นการสร้างตึกใหม่ หรืออัปเกรดตึกเดิม
                if cand['key'] == 'new_building':
                    # เปลี่ยนสถานะเมืองเป็นกำลังก่อสร้าง (รอสร้างเสร็จตอนจบเทิร์น)
                    cand['node_ref'].building_state = f"building_{cand['b_name']}"
                else:
                    cand['addons'][cand['key']] += 1
                    
                upgraded = True
                break

    def _collect_upgrade_candidates(self, node, is_advanced):
        results = []

        def _scan_addons(addons):
            # Farm
            farm_lvl = addons.get('farm', 1)
            if farm_lvl < 3:
                cost_dict = self._get_building_costs('farm', farm_lvl, farm_lvl * 5, is_advanced)
                results.append({'key': 'farm', 'cost_dict': cost_dict, 'priority': 2, 'addons': addons}) # ถอย Priority ลงมา
            
            # Tavern
            tav_lvl = addons.get('tavern', 1)
            if tav_lvl < 3:
                cost_dict = self._get_building_costs('tavern', tav_lvl, tav_lvl * 6, is_advanced)
                results.append({'key': 'tavern', 'cost_dict': cost_dict, 'priority': 3, 'addons': addons})
            
            # Special
            spec = addons.get('special')
            spec_lvl = addons.get('special_lvl', 0)
            if spec and spec not in ['mine'] and spec_lvl < 3:
                cost_dict = self._get_building_costs('special_lvl', spec_lvl, spec_lvl * 8, is_advanced)
                results.append({'key': 'special_lvl', 'cost_dict': cost_dict, 'priority': 4, 'addons': addons})

        # --- 🟢 เริ่ม: ลอจิกให้ AI ตัดสินใจสร้างตึกใหม่ ---
        if node.node_type == 'castle' and getattr(node, 'building_state', None) is None:
            # AI จะสุ่มว่าอยากสร้างตึกอะไร เพื่อความหลากหลาย
            new_buildings = [
                ('market', 10),      # (ชื่อตึก, ราคาภาษีเริ่มต้น)
                ('makerspace', 12),
                ('wallbuilder', 15)
            ]
            import random
            b_name, b_cost = random.choice(new_buildings)
            
            # ดึงราคาแบบตระกร้า และตั้ง Priority เป็น 1 (สำคัญสุด)
            cost_dict = self._get_building_costs(f"new_{b_name}", 1, b_cost, is_advanced)
            results.append({
                'key': 'new_building', 
                'b_name': b_name, 
                'cost_dict': cost_dict, 
                'priority': 1, 
                'node_ref': node # ส่งอ้างอิงเมืองมาด้วยเพื่อเอาไปเปลี่ยนสถานะ
            })
        # --- จบ: ลอจิกตึกใหม่ ---

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

        # AI กำหนดเป้าหมายตุนทรัพยากร (ถ้าของเหลือน้อยกว่านี้จะพยายามซื้อ)
        target_stock = {
            'wood_points': ('wood', 15), 
            'iron_points': ('iron', 10),
            'coal_points': ('coal', 5)
        }

        budget = app.tax_points.get(faction, 0)
        
        for res_name, (rate_key, target_amount) in target_stock.items():
            current = getattr(app, res_name, {}).get(faction, 0)
            cost_per_unit = rates.get(rate_key, 999) # ถ้าไม่มีของขายในตลาด ตั้งแพงๆ ไว้
            
            while current < target_amount and budget >= cost_per_unit:
                budget -= cost_per_unit
                current += 1
                getattr(app, res_name)[faction] = current
                
        app.tax_points[faction] = budget

    def plan_crafting(self, map_screen, faction):
        """ลอจิกสำหรับคราฟต์อาวุธที่ Makerspace"""
        app = App.get_running_app()
        owned_nodes = [n for n in map_screen.nodes_list if n.faction == faction]
        
        # ค้นหาว่ามีเมืองไหนสร้าง Makerspace ไว้ไหม
        makerspace_nodes = [n for n in owned_nodes if getattr(n, 'building_state', '') == 'makerspace']
        if not makerspace_nodes: return

        # 🛠️ ตำราคราฟต์อาวุธของ AI (สามารถแก้ทรัพยากรที่ใช้ให้ตรงกับ UI ผู้เล่นได้เลย)
        # รูปแบบ: ('ชื่อตัวแปรอาวุธ', {'ทรัพยากรที่ต้องใช้': จำนวน}, จำนวนชิ้นที่ AI อยากตุนไว้)
        crafting_recipes = [
            ('weapon_t1_points', {'wood_points': 2}, 5),               # ตุน T1 ไว้ 5 ชิ้น
            ('weapon_t2_points', {'wood_points': 1, 'iron_points': 2}, 3), # ตุน T2 ไว้ 3 ชิ้น
            ('weapon_t3_points', {'iron_points': 3, 'coal_points': 1}, 2)  # ตุน T3 ไว้ 2 ชิ้น
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
            
        # 🛠️ ราคาทหารโหมด Advanced (คุณสามารถปรับแก้ตัวเลขตรงนี้ให้ตรงกับหน้า UI ของคุณได้เลย)
        costs = {'tax_points': base_cost, 'supplies_points': 2}
        p_name = piece_name.lower()
        
        if p_name in ['levies', 'pawn']:
            costs['weapon_t1_points'] = 1
        elif p_name in ['menatarm', 'hastati', 'knight']:
            costs['weapon_t2_points'] = 1
        elif p_name in ['bishop', 'rook', 'queen', 'praetorian', 'royalguard']:
            costs['weapon_t3_points'] = 1
            costs['supplies_points'] = 4
            
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
        elif key in ['new_market', 'new_makerspace', 'new_wallbuilder']:
            costs['wood_points'] = 5
            costs['iron_points'] = 3
            
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

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cancel(self):
        """Cancel all pending AI actions (e.g. if the player quits mid-turn)."""
        for ev in self._pending_events:
            ev.cancel()
        self._pending_events.clear()
