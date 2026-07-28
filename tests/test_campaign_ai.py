import sys
from unittest.mock import MagicMock

# Attempt to aggressively mock kivy to allow headless testing
class MockKivy(MagicMock):
    pass

sys.modules['kivy'] = MockKivy()
sys.modules['kivy.app'] = MockKivy()
sys.modules['kivy.clock'] = MockKivy()
sys.modules['kivy.uix'] = MockKivy()
sys.modules['kivy.uix.screenmanager'] = MockKivy()
sys.modules['kivy.uix.floatlayout'] = MockKivy()
sys.modules['kivy.uix.boxlayout'] = MockKivy()
sys.modules['kivy.uix.gridlayout'] = MockKivy()
sys.modules['kivy.uix.scrollview'] = MockKivy()
sys.modules['kivy.uix.button'] = MockKivy()
sys.modules['kivy.uix.label'] = MockKivy()
sys.modules['kivy.uix.image'] = MockKivy()
sys.modules['kivy.graphics'] = MockKivy()
sys.modules['kivy.metrics'] = MockKivy()
sys.modules['kivy.uix.modalview'] = MockKivy()
sys.modules['kivy.uix.behaviors'] = MockKivy()

import pytest
from unittest.mock import patch
from logic.campaign_ai import CampaignAI

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.tax_points = {'black': 10, 'white': 10}
    return app

@pytest.fixture
def map_screen():
    screen = MagicMock()
    screen.nodes_list = []
    screen.status_lbl = MagicMock()
    return screen

@pytest.fixture
def campaign_ai():
    return CampaignAI()

def create_mock_node(faction='black', army_pieces=None, shop_cost=2, tavern_lvl=1):
    node = MagicMock()
    node.faction = faction
    node.army_pieces = army_pieces if army_pieces is not None else []
    node.addons = {'tavern': tavern_lvl}
    node.shop_recruits = {
        'row1': {'req_lvl': 1, 'data': [{'name': 'pawn', 'cost': shop_cost}]}
    }
    node.sub_villages = []
    return node

@patch('logic.campaign_ai.App')
@patch('logic.campaign_ai.generate_piece')
def test_recruitment_deducts_coins(mock_generate, mock_app_cls, mock_app, campaign_ai, map_screen):
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 10
    
    node = create_mock_node(shop_cost=2)
    map_screen.nodes_list = [node]
    
    campaign_ai.plan_recruitment(map_screen, 'black')
    
    assert mock_app.tax_points['black'] == 8
    assert node.shop_recruits['row1']['data'][0] is None

@patch('logic.campaign_ai.App')
@patch('logic.campaign_ai.generate_piece')
def test_recruitment_adds_unit(mock_generate, mock_app_cls, mock_app, campaign_ai, map_screen):
    mock_app_cls.get_running_app.return_value = mock_app
    mock_piece = MagicMock()
    mock_generate.return_value = mock_piece
    
    node = create_mock_node(shop_cost=2)
    map_screen.nodes_list = [node]
    
    campaign_ai.plan_recruitment(map_screen, 'black')
    
    assert len(node.army_pieces) == 1
    assert node.army_pieces[0] == mock_piece

@patch('logic.campaign_ai.App')
@patch('logic.campaign_ai.generate_piece')
def test_recruitment_respects_capacity(mock_generate, mock_app_cls, mock_app, campaign_ai, map_screen):
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 10
    
    # Create node with 8 units (capacity reached)
    mock_pieces = []
    for _ in range(8):
        mp = MagicMock()
        mp.__class__.__name__ = 'Pawn'
        mp.name = 'Pawn'
        mp.is_header = False
        mock_pieces.append(mp)
        
    node = create_mock_node(shop_cost=2, army_pieces=mock_pieces)
    map_screen.nodes_list = [node]
    
    campaign_ai.plan_recruitment(map_screen, 'black')
    
    # Should not deduct coins or add units
    assert mock_app.tax_points['black'] == 10
    assert len(node.army_pieces) == 8
    assert node.shop_recruits['row1']['data'][0] is not None

@patch('logic.campaign_ai.App')
@patch('logic.campaign_ai.generate_piece')
def test_recruitment_stops_on_low_budget(mock_generate, mock_app_cls, mock_app, campaign_ai, map_screen):
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 1
    
    node = create_mock_node(shop_cost=2)
    map_screen.nodes_list = [node]
    
    campaign_ai.plan_recruitment(map_screen, 'black')
    
    # Should not buy anything
    assert mock_app.tax_points['black'] == 1
    assert len(node.army_pieces) == 0
    assert node.shop_recruits['row1']['data'][0] is not None


# ===================================================================
#  Upgrade tests
# ===================================================================

def create_upgrade_node(faction='black', farm_lvl=1, tavern_lvl=1,
                        special=None, special_lvl=0, sub_villages=None):
    """Helper to build a mock node with real addons dicts for upgrade tests."""
    node = MagicMock()
    node.faction = faction
    node.army_pieces = []
    node.addons = {
        'farm': farm_lvl,
        'tavern': tavern_lvl,
        'special': special,
        'special_lvl': special_lvl,
    }
    node.sub_villages = sub_villages if sub_villages is not None else []
    node.shop_recruits = {}
    return node


@patch('logic.campaign_ai.App')
def test_upgrade_deducts_coins_and_increments_level(mock_app_cls, mock_app, campaign_ai, map_screen):
    """Upgrading a lvl-1 farm costs 5 coins and bumps the level to 2."""
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 10

    node = create_upgrade_node(farm_lvl=1, tavern_lvl=3)  # tavern maxed so only farm is upgradable
    map_screen.nodes_list = [node]

    campaign_ai.plan_upgrades(map_screen, 'black')

    # Farm lvl 1 → 2 costs 5, then farm lvl 2 → 3 costs 10 (too expensive with 5 left)
    assert node.addons['farm'] == 2
    assert mock_app.tax_points['black'] == 5


@patch('logic.campaign_ai.App')
def test_upgrade_respects_max_level(mock_app_cls, mock_app, campaign_ai, map_screen):
    """Buildings already at max level (3) should not be upgraded."""
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 50

    node = create_upgrade_node(farm_lvl=3, tavern_lvl=3)
    map_screen.nodes_list = [node]

    campaign_ai.plan_upgrades(map_screen, 'black')

    # Nothing to upgrade — coins untouched
    assert mock_app.tax_points['black'] == 50
    assert node.addons['farm'] == 3
    assert node.addons['tavern'] == 3


@patch('logic.campaign_ai.App')
def test_upgrade_stops_on_low_budget(mock_app_cls, mock_app, campaign_ai, map_screen):
    """AI with only 3 coins cannot afford the cheapest upgrade (farm lvl 1 = 5)."""
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 3

    node = create_upgrade_node(farm_lvl=1, tavern_lvl=1)
    map_screen.nodes_list = [node]

    campaign_ai.plan_upgrades(map_screen, 'black')

    # Nothing upgraded
    assert mock_app.tax_points['black'] == 3
    assert node.addons['farm'] == 1
    assert node.addons['tavern'] == 1


@patch('logic.campaign_ai.App')
def test_upgrade_excludes_mine(mock_app_cls, mock_app, campaign_ai, map_screen):
    """Mine special buildings should NOT be offered for upgrade (matching BuildPopup)."""
    mock_app_cls.get_running_app.return_value = mock_app
    mock_app.tax_points['black'] = 50

    # All standard buildings maxed, only special is available — but it's a mine
    node = create_upgrade_node(farm_lvl=3, tavern_lvl=3, special='mine', special_lvl=1)
    map_screen.nodes_list = [node]

    campaign_ai.plan_upgrades(map_screen, 'black')

    # Mine is excluded — coins untouched, level unchanged
    assert mock_app.tax_points['black'] == 50
    assert node.addons['special_lvl'] == 1


# ===================================================================
#  Army movement tests
# ===================================================================

def _make_pawn_mock():
    """Create a mock piece that looks like a Pawn (no header)."""
    p = MagicMock()
    p.__class__ = type('Pawn', (), {'__name__': 'Pawn'})
    p.name = 'Pawn'
    p.is_header = False
    return p


def create_movement_node(faction='black', army_count=5, fatigue=0,
                         neighbors=None, node_type='village'):
    """Helper to build a node for army movement tests."""
    node = MagicMock()
    node.faction = faction
    node.army_pieces = [_make_pawn_mock() for _ in range(army_count)]
    node.fatigue = fatigue
    node.neighbors = neighbors if neighbors is not None else []
    node.node_type = node_type
    node.addons = {}
    node.sub_villages = []
    node.shop_recruits = {}
    return node


@patch('logic.campaign_ai.App')
def test_movement_selects_adjacent_target(mock_app_cls, mock_app, campaign_ai, map_screen):
    """AI should select an adjacent enemy/neutral node as the attack target."""
    mock_app_cls.get_running_app.return_value = mock_app

    enemy_node = create_movement_node(faction='red', army_count=3)
    source_node = create_movement_node(faction='black', army_count=5,
                                       neighbors=[enemy_node])
    map_screen.nodes_list = [source_node]

    result = campaign_ai.plan_army_movements(map_screen, 'black')

    assert result is True
    map_screen.initiate_combat.assert_called_once_with(source_node, enemy_node)


@patch('logic.campaign_ai.App')
def test_movement_leaves_garrison(mock_app_cls, mock_app, campaign_ai, map_screen):
    """AI must leave MIN_GARRISON (2) units behind when marching."""
    mock_app_cls.get_running_app.return_value = mock_app

    enemy_node = create_movement_node(faction='white', army_count=2)
    source_node = create_movement_node(faction='black', army_count=6,
                                       neighbors=[enemy_node])
    map_screen.nodes_list = [source_node]

    campaign_ai.plan_army_movements(map_screen, 'black')

    # Source should have exactly MIN_GARRISON units left
    assert len(source_node.army_pieces) == campaign_ai.MIN_GARRISON
    # Marching army should have the rest
    assert len(mock_app.combat_marching_army) == 4  # 6 - 2


@patch('logic.campaign_ai.App')
def test_movement_skips_small_army(mock_app_cls, mock_app, campaign_ai, map_screen):
    """Nodes with <= MIN_GARRISON units should not attempt to march."""
    mock_app_cls.get_running_app.return_value = mock_app

    enemy_node = create_movement_node(faction='red', army_count=1)
    # Only 2 units — equal to MIN_GARRISON, nothing to march
    source_node = create_movement_node(faction='black', army_count=2,
                                       neighbors=[enemy_node])
    map_screen.nodes_list = [source_node]

    result = campaign_ai.plan_army_movements(map_screen, 'black')

    assert result is False
    map_screen.initiate_combat.assert_not_called()


@patch('logic.campaign_ai.App')
def test_movement_skips_exhausted_node(mock_app_cls, mock_app, campaign_ai, map_screen):
    """Exhausted nodes (fatigue >= 6) cannot march."""
    mock_app_cls.get_running_app.return_value = mock_app

    enemy_node = create_movement_node(faction='red', army_count=2)
    source_node = create_movement_node(faction='black', army_count=8,
                                       fatigue=6,
                                       neighbors=[enemy_node])
    map_screen.nodes_list = [source_node]

    result = campaign_ai.plan_army_movements(map_screen, 'black')

    assert result is False
    map_screen.initiate_combat.assert_not_called()
