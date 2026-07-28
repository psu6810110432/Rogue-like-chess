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
        map_screen.status_lbl.text = (
            "[color=ff6644][b]AI IS ANALYZING...[/b][/color]"
        )
        map_screen.status_lbl.color = (1, 0.4, 0.27, 1)

        # Scroll the map viewport to center on the AI faction's main base
        self._scroll_to_faction_base(map_screen, faction)

        # Chain → Step 2 after a delay
        ev = Clock.schedule_once(
            lambda dt: self._step_recruit(map_screen, faction),
            self.STEP_DELAY_SHORT,
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
        """
        Browse every owned node's shop and buy affordable units,
        mirroring the player's recruitment path exactly.

        The AI prioritises nodes that are under-garrisoned (fewest
        current troops) and prefers the cheapest units first so it
        can spread purchases across multiple nodes.
        """
        app = App.get_running_app()
        budget = app.tax_points.get(faction, 0)
        if budget <= 0:
            return

        # Collect all friendly nodes, sorted by army size (weakest first)
        owned_nodes = sorted(
            [n for n in map_screen.nodes_list if n.faction == faction],
            key=lambda n: len(n.army_pieces),
        )
        if not owned_nodes:
            return

        # Keep buying until we run out of money or all nodes are full
        purchases_made = True  # sentinel to break when no more buys possible
        while budget >= 2 and purchases_made:
            purchases_made = False
            for node in owned_nodes:
                if budget < 2:
                    break

                # Capacity check (same formula as campaign_panel.buy_piece)
                has_header = any(
                    p.__class__.__name__.lower() == 'king'
                    or getattr(p, 'name', '') == 'Prince'
                    or getattr(p, 'is_header', False)
                    for p in node.army_pieces
                )
                max_cap = 16 if has_header else 8
                if len(node.army_pieces) >= max_cap:
                    continue

                # Try to find an affordable item in this node's shop
                bought = self._try_buy_from_node(app, node, faction, budget)
                if bought is not None:
                    budget -= bought
                    purchases_made = True

        # Write the updated budget back
        app.tax_points[faction] = budget

    def _try_buy_from_node(self, app, node, faction, budget):
        """
        Attempt to buy a single unit from *node*'s shop.

        Returns the cost paid, or None if nothing could be bought.
        Exactly mirrors the player's buy path in CampaignArmyPanel.buy_piece().
        """
        addons = getattr(node, 'addons', {})
        tav_lvl = addons.get('tavern', 1)
        shop = getattr(node, 'shop_recruits', {})
        if not shop:
            return None

        # Also consider sub-village shops for castles
        shop_sources = [(shop, addons)]
        for sv in getattr(node, 'sub_villages', []):
            sv_shop = sv.get('shop_recruits', {})
            sv_addons = sv.get('addons', {})
            if sv_shop:
                shop_sources.append((sv_shop, sv_addons))

        # Gather all available (non-None) items the AI can afford
        candidates = []
        for src_shop, src_addons in shop_sources:
            src_tav_lvl = src_addons.get('tavern', 1)
            for row_key in ['row1', 'row2', 'row3', 'row4', 'row5']:
                row = src_shop.get(row_key)
                if row is None:
                    continue
                # Tavern level gating — must match or exceed required level
                if src_tav_lvl < row.get('req_lvl', 1):
                    continue
                for idx, slot in enumerate(row['data']):
                    if slot is None:
                        continue
                    base_cost = slot['cost']
                    final_cost = self._get_discounted_price(
                        base_cost, src_addons,
                    )
                    if final_cost <= budget:
                        candidates.append(
                            (final_cost, slot['name'], row_key, idx,
                             src_shop, src_addons)
                        )

        if not candidates:
            return None

        # Sort cheapest-first so the AI stretches its budget, with a
        # small random shuffle among same-price options for variety.
        random.shuffle(candidates)
        candidates.sort(key=lambda c: c[0])

        cost, piece_name, row_key, idx, src_shop, src_addons = candidates[0]

        # --- Reproduce the exact buy_piece() sequence ---

        # 1. Consume the shop slot
        src_shop[row_key]['data'][idx] = None

        # 2. Create the unit (identical to campaign_panel.buy_piece)
        new_p = generate_piece(piece_name, faction, app)

        # 3. Apply weaponsmith / blacksmith bonuses from the source
        spec = src_addons.get('special')
        slvl = src_addons.get('special_lvl', 0)

        if spec == 'weaponsmith':
            new_p.base_atk += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'atk_buff'
            new_p.second_hidden_passive.description = (
                f"Weaponsmith Forged (+{slvl} ATK)"
            )
        elif spec == 'blacksmith':
            new_p.base_def += slvl
            if not getattr(new_p, 'second_hidden_passive', None):
                from components.hidden_passive import HiddenPassive
                new_p.second_hidden_passive = HiddenPassive()
                new_p.second_hidden_passive.passive_type = 'def_buff'
            new_p.second_hidden_passive.description = (
                f"Blacksmith Forged (+{slvl} DEF)"
            )

        # 4. Add the unit to the node's army
        node.army_pieces.append(new_p)

        return cost

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
        """
        Upgrade buildings across all owned nodes, mirroring the player's
        BuildPopup / upgrade_addon() path exactly.

        Priority order (best ROI first):
          1. Farms   — cost = level × 5, max level 3  (+2 tax per level)
          2. Taverns — cost = level × 6, max level 3  (unlocks unit tiers)
          3. Special — cost = level × 8, max level 3  (mine excluded)
        """
        app = App.get_running_app()
        budget = app.tax_points.get(faction, 0)
        if budget <= 0:
            return

        owned_nodes = [
            n for n in map_screen.nodes_list if n.faction == faction
        ]
        if not owned_nodes:
            return

        # Keep upgrading until we can no longer afford anything
        upgraded = True
        while budget > 0 and upgraded:
            upgraded = False

            # Collect every possible upgrade across all owned nodes
            candidates = []
            for node in owned_nodes:
                candidates.extend(
                    self._collect_upgrade_candidates(node)
                )

            if not candidates:
                break

            # Sort by priority (lower = better), then by cost (cheapest first)
            candidates.sort(key=lambda c: (c['priority'], c['cost']))

            for cand in candidates:
                if cand['cost'] > budget:
                    continue
                # Perform the upgrade — identical to upgrade_addon()
                budget -= cand['cost']
                cand['addons'][cand['key']] += 1
                upgraded = True
                break  # re-collect after each upgrade (levels changed)

        app.tax_points[faction] = budget

    @staticmethod
    def _collect_upgrade_candidates(node):
        """
        Return a list of upgrade candidates for *node* (and its
        sub-villages if it is a castle).  Each candidate is a dict:
          {'key': str, 'cost': int, 'priority': int, 'addons': dict}

        Priority values: 1 = farm, 2 = tavern, 3 = special.
        Mirrors the BuildPopup rules exactly:
          - Farm:    key='farm',        cost = farm_lvl × 5,  max 3
          - Tavern:  key='tavern',      cost = tav_lvl  × 6,  max 3
          - Special: key='special_lvl', cost = spec_lvl × 8,  max 3
                     (mine is excluded from upgrades)
        """
        results = []

        def _scan_addons(addons):
            # Farm
            farm_lvl = addons.get('farm', 1)
            if farm_lvl < 3:
                results.append({
                    'key': 'farm',
                    'cost': farm_lvl * 5,
                    'priority': 1,
                    'addons': addons,
                })
            # Tavern
            tav_lvl = addons.get('tavern', 1)
            if tav_lvl < 3:
                results.append({
                    'key': 'tavern',
                    'cost': tav_lvl * 6,
                    'priority': 2,
                    'addons': addons,
                })
            # Special (mine excluded — matches BuildPopup line 252)
            spec = addons.get('special')
            spec_lvl = addons.get('special_lvl', 0)
            if spec and spec not in ['mine'] and spec_lvl < 3:
                results.append({
                    'key': 'special_lvl',
                    'cost': spec_lvl * 8,
                    'priority': 3,
                    'addons': addons,
                })

        # Main node addons
        main_addons = getattr(node, 'addons', {})
        if main_addons:
            _scan_addons(main_addons)

        # Castle sub-village addons
        for sv in getattr(node, 'sub_villages', []):
            sv_addons = sv.get('addons', {})
            if sv_addons:
                _scan_addons(sv_addons)

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

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cancel(self):
        """Cancel all pending AI actions (e.g. if the player quits mid-turn)."""
        for ev in self._pending_events:
            ev.cancel()
        self._pending_events.clear()
