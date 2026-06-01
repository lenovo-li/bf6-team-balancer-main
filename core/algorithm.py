"""
BF6 Team Balancer - Core Algorithm Module

Greedy team allocation -> ABAB reserve extraction -> Squad formation -> Balance check
"""

import random
from dataclasses import dataclass, field
from typing import Optional


# -- Config ------------------------------------------------------

GAME_MODES = {
    "conquest": {"kd_weight": 0.7, "kpm_weight": 0.3},    # Conquest
    "breakthrough": {"kd_weight": 0.3, "kpm_weight": 0.7}, # Breakthrough
}

SQUAD_SIZE = 4
MAX_RESERVE = 8
MAX_SQUADS_CONQUEST = 16      # Conquest: max 64 players
MAX_SQUADS_BREAKTHROUGH = 12  # Breakthrough: max 48 players

# Balance warning thresholds
HIGH_STAT_THRESHOLD = 2.0     # KD/KPM above this is considered "high"
BALANCE_DIFF_THRESHOLD = 0.3  # Team avg difference above this triggers warning


# -- Helpers -----------------------------------------------------

def _max_per_team(total_players: int, game_mode: str) -> int:
    """Calculate max players per team, rounded down to nearest multiple of SQUAD_SIZE."""
    max_squads = MAX_SQUADS_CONQUEST if game_mode == "conquest" else MAX_SQUADS_BREAKTHROUGH
    return min((total_players // 2 // SQUAD_SIZE) * SQUAD_SIZE, max_squads * SQUAD_SIZE)


# -- Data Models --------------------------------------------------

@dataclass
class Player:
    """A single player with KD/KPM stats and cached weighted scores per game mode."""
    name: str
    kd: Optional[float]
    kpm: Optional[float]  # offset-adjusted
    _weighted_scores: dict = field(default_factory=dict, repr=False)

    def weighted_score(self, game_mode: str) -> float:
        """Compute weighted score for the given game mode (cached per mode)."""
        if game_mode not in self._weighted_scores:
            cfg = GAME_MODES[game_mode]
            kd = self.kd if self.kd is not None else 0
            kpm = self.kpm if self.kpm is not None else 0
            self._weighted_scores[game_mode] = round(
                kd * cfg["kd_weight"] + kpm * cfg["kpm_weight"], 2
            )
        return self._weighted_scores[game_mode]

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.name == other.name
        return NotImplemented


@dataclass
class Squad:
    """A squad of up to SQUAD_SIZE players."""
    members: list = field(default_factory=list)

    @property
    def avg_kd(self) -> float:
        vals = [p.kd for p in self.members if p.kd is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0

    @property
    def avg_kpm(self) -> float:
        vals = [p.kpm for p in self.members if p.kpm is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0


@dataclass
class Team:
    """A team composed of squads and a buffer for incomplete squads."""
    name: str
    game_mode: str = "conquest"
    squads: list = field(default_factory=list)
    _buffer: list = field(default_factory=list, repr=False)

    @property
    def total_players(self) -> int:
        return sum(len(s.members) for s in self.squads) + len(self._buffer)

    @property
    def total_kpm(self) -> float:
        all_p = self._all_players()
        vals = [p.kpm for p in all_p if p.kpm is not None]
        return round(sum(vals), 2) if vals else 0

    @property
    def avg_kpm(self) -> float:
        all_p = self._all_players()
        vals = [p.kpm for p in all_p if p.kpm is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0

    @property
    def avg_kd(self) -> float:
        all_p = self._all_players()
        vals = [p.kd for p in all_p if p.kd is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0

    @property
    def score(self) -> float:
        all_p = self._all_players()
        return sum(p.weighted_score(self.game_mode) for p in all_p)

    def _all_players(self) -> list:
        result = []
        for s in self.squads:
            result.extend(s.members)
        result.extend(self._buffer)
        return result

    def add_player(self, player: Player) -> None:
        self._buffer.append(player)
        if len(self._buffer) >= SQUAD_SIZE:
            self.squads.append(Squad(members=list(self._buffer)))
            self._buffer.clear()

    def add_players(self, players: list) -> None:
        for p in players:
            self.add_player(p)

    @property
    def remaining_slots(self) -> int:
        # Total capacity is set externally; this counts remaining buffer slots
        # Actual capacity is controlled by max_players during allocation
        return SQUAD_SIZE - len(self._buffer)

    def flush_buffer(self) -> None:
        """Force remaining buffer (< 4 players) into a squad."""
        if self._buffer:
            self.squads.append(Squad(members=list(self._buffer)))
            self._buffer.clear()


# -- Algorithms --------------------------------------------------

def load_players(data: dict) -> list:
    """Load Player list from a parsed JSON dict."""
    players = []
    for p in data["players"]:
        kd = p.get("kd")
        kpm = p.get("kpm_adjusted")
        if kd is None and kpm is None:
            continue  # Skip players with no data
        players.append(Player(
            name=p["name"],
            kd=kd,
            kpm=kpm,
        ))
    return players


def build_custom_squads(player_map: dict, bindings: list) -> tuple:
    """
    Process custom squad bindings.
    bindings: [{"player_a": "name1", "player_b": "name2"}, ...]
    Returns: (custom_squads, unbound_players)
    """
    bound_names = set()
    custom_squads = []

    for b in bindings:
        name_a = b["player_a"]
        name_b = b["player_b"]

        if name_a not in player_map or name_b not in player_map:
            raise ValueError(f"玩家不存在: {name_a} 或 {name_b}")
        if name_a in bound_names or name_b in bound_names:
            raise ValueError(f"玩家已被绑定: {name_a} 或 {name_b}")

        pa = player_map[name_a]
        pb = player_map[name_b]
        bound_names.add(name_a)
        bound_names.add(name_b)
        custom_squads.append([pa, pb])

    unbound = [p for p in player_map.values() if p.name not in bound_names]
    return custom_squads, unbound


def extract_reserves(sorted_players: list, custom_squads: list,
                     game_mode: str, max_reserve: int = MAX_RESERVE) -> list:
    """
    ABAB front/back extraction of reserves from sorted independent players.
    Goal: equal team sizes divisible by 4, maximize active player count.
    Custom squad members are excluded from reserve extraction (cannot split).
    """
    bound_names = set()
    for squad in custom_squads:
        for p in squad:
            bound_names.add(p.name)

    eligible = [p for p in sorted_players if p.name not in bound_names]
    bound_count = sum(len(s) for s in custom_squads)
    total = len(eligible) + bound_count

    max_per_team = _max_per_team(total, game_mode)

    # Active players = per-team count x 2
    active = max_per_team * 2
    target_reserve = total - active
    target_reserve = min(target_reserve, max_reserve)
    target_reserve = max(target_reserve, 0)

    reserves = []
    left = 0
    right = len(eligible) - 1
    take_from_front = True

    while left <= right and len(reserves) < target_reserve:
        if take_from_front:
            reserves.append(eligible[left])
            left += 1
        else:
            reserves.append(eligible[right])
            right -= 1
        take_from_front = not take_from_front

    return reserves


def allocate_teams(
    players: list,
    bindings: list,
    game_mode: str,
    team_a_name: str = "北约",
    team_b_name: str = "和平军团",
) -> tuple:
    """
    Greedy team allocation.
    bindings: [{"player_a": "name1", "player_b": "name2"}, ...]
    Returns: (team_a, team_b, reserves)
    """
    # 1. Process custom squad bindings
    player_map = {p.name: p for p in players}
    custom_squads, independent = build_custom_squads(player_map, bindings)

    # 2. Sort independent players by score descending
    sorted_players = sorted(independent, key=lambda p: p.weighted_score(game_mode), reverse=True)

    # 3. ABAB reserve extraction (from independent players only)
    reserves = extract_reserves(sorted_players, custom_squads, game_mode)
    reserve_names = {p.name for p in reserves}

    # 4. Build allocation list (exclude reserves)
    remaining_players = [p for p in sorted_players if p.name not in reserve_names]

    # 5. Calculate max capacity
    total_remaining = len(remaining_players) + sum(len(s) for s in custom_squads)
    max_per_team = _max_per_team(total_remaining * 2, game_mode)

    # 6. Create teams
    team_a = Team(name=team_a_name, game_mode=game_mode)
    team_b = Team(name=team_b_name, game_mode=game_mode)

    # 7. Greedy allocation
    #    Treat custom squads as atomic units (avg score, 2 slots), interleave with solo players
    items = []
    for p in remaining_players:
        items.append((p.weighted_score(game_mode), "player", p))
    for squad in custom_squads:
        avg_score = sum(p.weighted_score(game_mode) for p in squad) / len(squad)
        items.append((avg_score, "squad", squad))

    # Sort by score descending
    items.sort(key=lambda x: x[0], reverse=True)

    for score, item_type, data in items:
        # Assign to the team with the lower total score
        target = team_a if team_a.score <= team_b.score else team_b

        if item_type == "player":
            if target.total_players < max_per_team:
                target.add_player(data)
            else:
                other = team_b if target is team_a else team_a
                other.add_player(data)
        else:
            # Custom squad: needs 2 slots
            squad_size = len(data)
            if target.total_players + squad_size <= max_per_team:
                target.add_players(data)
            else:
                other = team_b if target is team_a else team_a
                other.add_players(data)

    # 8. Force remaining buffer (< 4 players) into squads
    team_a.flush_buffer()
    team_b.flush_buffer()

    return team_a, team_b, reserves


def random_allocate(
    players: list,
    bindings: list,
    game_mode: str = "conquest",
    team_a_name: str = "北约",
    team_b_name: str = "和平军团",
) -> tuple:
    """
    Random team allocation. Custom squad bindings still apply (cannot split),
    everything else is shuffled randomly.
    Returns: (team_a, team_b, reserves)
    """
    # 1. Process custom squad bindings
    player_map = {p.name: p for p in players}
    custom_squads, independent = build_custom_squads(player_map, bindings)

    # 2. Calculate capacity
    total = len(players)
    max_per_team = _max_per_team(total, game_mode)
    active = max_per_team * 2

    # 3. Randomly draw reserves from independent players (custom squad members excluded)
    reserve_target = total - active
    reserve_target = min(reserve_target, MAX_RESERVE)
    reserve_target = max(reserve_target, 0)

    random.shuffle(independent)
    reserves = independent[:reserve_target]
    remaining_players = independent[reserve_target:]

    # 4. Build allocation list: custom squads + remaining independent players, shuffle all
    items = []
    for p in remaining_players:
        items.append(("player", [p]))
    for squad in custom_squads:
        items.append(("squad", squad))
    random.shuffle(items)

    # 5. Create teams
    team_a = Team(name=team_a_name, game_mode=game_mode)
    team_b = Team(name=team_b_name, game_mode=game_mode)

    # 6. Round-robin allocation (AABB alternating, keep team sizes balanced)
    turn_a = True
    for item_type, members in items:
        target = team_a if turn_a else team_b
        other = team_b if turn_a else team_a

        if target.total_players + len(members) <= max_per_team:
            target.add_players(members)
        else:
            other.add_players(members)

        # Toggle turn
        turn_a = not turn_a

    # 7. Force remaining buffer into squads
    team_a.flush_buffer()
    team_b.flush_buffer()

    return team_a, team_b, reserves


def compute_balance_report(team_a: Team, team_b: Team, reserves: list, game_mode: str) -> dict:
    """Compute balance report for the two teams."""

    def _high_count(players: list, attr: str) -> int:
        return sum(1 for p in players if getattr(p, attr) is not None and getattr(p, attr) >= HIGH_STAT_THRESHOLD)

    report = {
        "game_mode": game_mode,
        "team_a": {
            "name": team_a.name,
            "total_players": team_a.total_players,
            "num_squads": len(team_a.squads),
            "avg_kd": team_a.avg_kd,
            "avg_kpm": team_a.avg_kpm,
            "total_score": round(team_a.score, 2),
            "squads": [
                {
                    "squad_id": i + 1,
                    "avg_kd": s.avg_kd,
                    "avg_kpm": s.avg_kpm,
                    "members": [{"name": p.name, "kd": p.kd, "kpm": p.kpm} for p in s.members],
                }
                for i, s in enumerate(team_a.squads)
            ],
            "high_kd_count": _high_count(team_a._all_players(), "kd"),
            "high_kpm_count": _high_count(team_a._all_players(), "kpm"),
        },
        "team_b": {
            "name": team_b.name,
            "total_players": team_b.total_players,
            "num_squads": len(team_b.squads),
            "avg_kd": team_b.avg_kd,
            "avg_kpm": team_b.avg_kpm,
            "total_score": round(team_b.score, 2),
            "squads": [
                {
                    "squad_id": i + 1,
                    "avg_kd": s.avg_kd,
                    "avg_kpm": s.avg_kpm,
                    "members": [{"name": p.name, "kd": p.kd, "kpm": p.kpm} for p in s.members],
                }
                for i, s in enumerate(team_b.squads)
            ],
            "high_kd_count": _high_count(team_b._all_players(), "kd"),
            "high_kpm_count": _high_count(team_b._all_players(), "kpm"),
        },
        "reserves": {
            "count": len(reserves),
            "members": [{"name": p.name, "kd": p.kd, "kpm": p.kpm} for p in reserves],
        },
        "balance": {
            "kd_diff": round(abs(team_a.avg_kd - team_b.avg_kd), 2),
            "kpm_diff": round(abs(team_a.avg_kpm - team_b.avg_kpm), 2),
            "score_diff": round(abs(team_a.score - team_b.score), 2),
        },
        "warnings": [],
    }

    # Generate warnings
    if report["balance"]["kd_diff"] > BALANCE_DIFF_THRESHOLD:
        report["warnings"].append(f"KD差距较大 ({report['balance']['kd_diff']})，征服模式下可能失衡")
    if report["balance"]["kpm_diff"] > BALANCE_DIFF_THRESHOLD:
        report["warnings"].append(f"KPM差距较大 ({report['balance']['kpm_diff']})，突破模式下可能失衡")
    if report["reserves"]["count"] > MAX_RESERVE:
        report["warnings"].append(f"候补人数({report['reserves']['count']})超过上限{MAX_RESERVE}")

    return report
