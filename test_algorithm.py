"""
Algorithm tests - pytest-based, self-contained, no external files needed.
Run: python -m pytest test_algorithm.py -v
"""

import pytest
from core.algorithm import (
    Player, Squad, Team,
    load_players, allocate_teams, random_allocate,
    build_custom_squads, extract_reserves, compute_balance_report,
    GAME_MODES, SQUAD_SIZE,
)


# -- Fixtures ----------------------------------------------------

def make_player(name, kd=1.0, kpm=1.0):
    """Helper to create a Player quickly."""
    return Player(name=name, kd=kd, kpm=kpm)


def make_players(n, base_kd=1.0, base_kpm=1.0):
    """Generate n players with incrementing stats."""
    return [
        Player(name=f"P{i+1}", kd=round(base_kd + i * 0.1, 2), kpm=round(base_kpm + i * 0.05, 2))
        for i in range(n)
    ]


SAMPLE_JSON = {
    "meta": {"total_players": 6, "kpm_offset": 1.313},
    "players": [
        {"name": "Alice", "kd": 3.5, "kpm_adjusted": 2.0},
        {"name": "Bob", "kd": 1.2, "kpm_adjusted": 1.5},
        {"name": "Charlie", "kd": 0.8, "kpm_adjusted": 0.9},
        {"name": "Dave", "kd": 2.1, "kpm_adjusted": 1.8},
        {"name": "Eve", "kd": 0.5, "kpm_adjusted": 0.3},
        {"name": "Frank", "kd": 1.5, "kpm_adjusted": 1.2},
    ],
}


# -- Player model tests -----------------------------------------

class TestPlayer:
    def test_weighted_score_conquest(self):
        p = Player(name="Test", kd=2.0, kpm=1.0)
        cfg = GAME_MODES["conquest"]
        expected = round(2.0 * cfg["kd_weight"] + 1.0 * cfg["kpm_weight"], 2)
        assert p.weighted_score("conquest") == expected

    def test_weighted_score_breakthrough(self):
        p = Player(name="Test", kd=2.0, kpm=1.0)
        cfg = GAME_MODES["breakthrough"]
        expected = round(2.0 * cfg["kd_weight"] + 1.0 * cfg["kpm_weight"], 2)
        assert p.weighted_score("breakthrough") == expected

    def test_weighted_score_cache_per_mode(self):
        """Scores should be cached independently per game mode."""
        p = Player(name="Test", kd=2.0, kpm=1.0)
        s1 = p.weighted_score("conquest")
        s2 = p.weighted_score("breakthrough")
        assert s1 != s2
        # Cached values should be stable
        assert p.weighted_score("conquest") == s1
        assert p.weighted_score("breakthrough") == s2

    def test_hash_identity(self):
        p1 = Player(name="Same", kd=1.0, kpm=1.0)
        p2 = Player(name="Same", kd=1.0, kpm=1.0)
        p3 = Player(name="Different", kd=1.0, kpm=1.0)
        # Same name -> same hash and equal
        assert hash(p1) == hash(p2)
        assert p1 == p2
        # Different name -> different hash and not equal
        assert hash(p1) != hash(p3)
        assert p1 != p3


# -- Squad / Team tests -----------------------------------------

class TestSquad:
    def test_avg_empty(self):
        sq = Squad(members=[])
        assert sq.avg_kd == 0
        assert sq.avg_kpm == 0

    def test_avg_with_members(self):
        sq = Squad(members=[
            Player(name="A", kd=2.0, kpm=1.0),
            Player(name="B", kd=4.0, kpm=3.0),
        ])
        assert sq.avg_kd == 3.0
        assert sq.avg_kpm == 2.0


class TestTeam:
    def test_add_player_auto_squad(self):
        team = Team(name="Test")
        for i in range(SQUAD_SIZE):
            team.add_player(Player(name=f"P{i}", kd=1.0, kpm=1.0))
        assert len(team.squads) == 1
        assert team.total_players == SQUAD_SIZE

    def test_flush_buffer(self):
        team = Team(name="Test")
        team.add_player(Player(name="P0", kd=1.0, kpm=1.0))
        assert len(team.squads) == 0
        team.flush_buffer()
        assert len(team.squads) == 1
        assert team.squads[0].members[0].name == "P0"

    def test_score_uses_game_mode(self):
        p = Player(name="P0", kd=2.0, kpm=1.0)
        team_cq = Team(name="A", game_mode="conquest")
        team_bt = Team(name="B", game_mode="breakthrough")
        team_cq.add_player(p)
        team_bt.add_player(p)
        assert team_cq.score != team_bt.score


# -- load_players tests -----------------------------------------

class TestLoadPlayers:
    def test_load_basic(self):
        players = load_players(SAMPLE_JSON)
        assert len(players) == 6
        assert players[0].name == "Alice"
        assert players[0].kd == 3.5

    def test_skip_both_none(self):
        data = {"players": [
            {"name": "Ghost", "kd": None, "kpm_adjusted": None},
            {"name": "Valid", "kd": 1.0, "kpm_adjusted": 1.0},
        ]}
        players = load_players(data)
        assert len(players) == 1
        assert players[0].name == "Valid"


# -- build_custom_squads tests -----------------------------------

class TestBuildCustomSquads:
    def test_basic_binding(self):
        players = [make_player("A"), make_player("B"), make_player("C")]
        pmap = {p.name: p for p in players}
        squads, unbound = build_custom_squads(pmap, [{"player_a": "A", "player_b": "B"}])
        assert len(squads) == 1
        assert len(unbound) == 1
        assert unbound[0].name == "C"

    def test_duplicate_binding_raises(self):
        players = [make_player("A"), make_player("B")]
        pmap = {p.name: p for p in players}
        bindings = [
            {"player_a": "A", "player_b": "B"},
            {"player_a": "A", "player_b": "B"},
        ]
        with pytest.raises(ValueError):
            build_custom_squads(pmap, bindings)

    def test_nonexistent_player_raises(self):
        pmap = {"A": make_player("A")}
        with pytest.raises(ValueError):
            build_custom_squads(pmap, [{"player_a": "A", "player_b": "X"}])


# -- extract_reserves tests -------------------------------------

class TestExtractReserves:
    def test_no_reserves_when_few_players(self):
        players = make_players(8)
        reserves = extract_reserves(players, [], "conquest")
        assert len(reserves) == 0

    def test_reserves_from_middle(self):
        """With enough players to exceed team capacity, reserves should be extracted."""
        # 74 players: max_per_team = (74//2//4)*4 = 36, active=72, reserve=2
        players = make_players(74)
        sorted_players = sorted(players, key=lambda p: p.weighted_score("conquest"), reverse=True)
        reserves = extract_reserves(sorted_players, [], "conquest")
        assert len(reserves) == 2
        assert len(reserves) <= 8

    def test_bound_players_excluded(self):
        players = make_players(10)
        squads = [[players[0], players[1]]]
        reserves = extract_reserves(players[2:], squads, "conquest")
        reserve_names = {p.name for p in reserves}
        assert "P1" not in reserve_names
        assert "P2" not in reserve_names


# -- allocate_teams tests ----------------------------------------

class TestAllocateTeams:
    def test_conquest_basic(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        # All players should be allocated (total or reserves)
        total = ta.total_players + tb.total_players + len(rv)
        assert total == len(players)

    def test_team_balance(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        report = compute_balance_report(ta, tb, rv, "conquest")
        # With few players, balance should be reasonable
        assert report["balance"]["kd_diff"] < 1.0

    def test_with_binding(self):
        players = load_players(SAMPLE_JSON)
        bindings = [{"player_a": "Alice", "player_b": "Bob"}]
        ta, tb, rv = allocate_teams(players, bindings, "conquest")
        # Alice and Bob should be on the same team
        all_a = [p.name for p in ta._all_players()]
        all_b = [p.name for p in tb._all_players()]
        same_team = ("Alice" in all_a and "Bob" in all_a) or ("Alice" in all_b and "Bob" in all_b)
        assert same_team

    def test_breakthrough_mode(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = allocate_teams(players, [], "breakthrough")
        total = ta.total_players + tb.total_players + len(rv)
        assert total == len(players)

    def test_squads_formed(self):
        players = make_players(16)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        # Each team should have squads
        assert len(ta.squads) > 0
        assert len(tb.squads) > 0
        # Squad size should be <= SQUAD_SIZE
        for sq in ta.squads + tb.squads:
            assert len(sq.members) <= SQUAD_SIZE


# -- random_allocate tests ---------------------------------------

class TestRandomAllocate:
    def test_all_players_accounted(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = random_allocate(players, [], "conquest")
        total = ta.total_players + tb.total_players + len(rv)
        assert total == len(players)

    def test_binding_still_works(self):
        players = load_players(SAMPLE_JSON)
        bindings = [{"player_a": "Alice", "player_b": "Bob"}]
        ta, tb, rv = random_allocate(players, bindings, "conquest")
        all_a = [p.name for p in ta._all_players()]
        all_b = [p.name for p in tb._all_players()]
        same_team = ("Alice" in all_a and "Bob" in all_a) or ("Alice" in all_b and "Bob" in all_b)
        assert same_team

    def test_team_sizes_balanced(self):
        players = make_players(20)
        ta, tb, rv = random_allocate(players, [], "conquest")
        assert abs(ta.total_players - tb.total_players) <= SQUAD_SIZE


# -- compute_balance_report tests --------------------------------

class TestComputeBalanceReport:
    def test_report_structure(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        report = compute_balance_report(ta, tb, rv, "conquest")
        assert "team_a" in report
        assert "team_b" in report
        assert "reserves" in report
        assert "balance" in report
        assert "warnings" in report

    def test_balance_diffs_non_negative(self):
        players = load_players(SAMPLE_JSON)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        report = compute_balance_report(ta, tb, rv, "conquest")
        bl = report["balance"]
        assert bl["kd_diff"] >= 0
        assert bl["kpm_diff"] >= 0
        assert bl["score_diff"] >= 0


# -- Edge cases --------------------------------------------------

class TestEdgeCases:
    def test_large_player_count(self):
        """Should handle 64+ players without errors."""
        players = make_players(72)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        total = ta.total_players + tb.total_players + len(rv)
        assert total == 72

    def test_odd_player_count(self):
        """Odd number of players should still work."""
        players = make_players(15)
        ta, tb, rv = allocate_teams(players, [], "conquest")
        total = ta.total_players + tb.total_players + len(rv)
        assert total == 15

    def test_single_player(self):
        """Single player should end up in reserves or a team."""
        players = [make_player("Solo", kd=1.0, kpm=1.0)]
        ta, tb, rv = allocate_teams(players, [], "conquest")
        total = ta.total_players + tb.total_players + len(rv)
        assert total == 1
