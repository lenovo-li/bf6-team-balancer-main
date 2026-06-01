"""
BF6 Team Balancer - History module

Save/load team allocation history, max 5 records, auto-evicts oldest.
Storage path: %USERPROFILE%/Documents/BF6TeamBalancer/history.json
"""

import json
import os
from datetime import datetime

MAX_RECORDS = 5
HISTORY_DIR = os.path.join(os.path.expanduser("~"), "Documents", "BF6TeamBalancer")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
CONFIG_FILE = os.path.join(HISTORY_DIR, "config.json")


def get_history_path() -> str:
    return HISTORY_FILE


def load_history() -> list:
    """Load history record list. Returns empty list if file doesn't exist."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_record(report: dict, alloc_mode: str) -> None:
    """
    Save one allocation record. Inserts at head, auto-truncates beyond MAX_RECORDS.

    report: return value of compute_balance_report()
    alloc_mode: "balanced" | "random"
    """
    r = report
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alloc_mode": alloc_mode,
        "game_mode": r["game_mode"],
        "team_a": _extract_team(r["team_a"]),
        "team_b": _extract_team(r["team_b"]),
        "reserves": [m["name"] for m in r["reserves"]["members"]],
        "balance": r["balance"],
    }

    history = load_history()
    history.insert(0, record)
    history = history[:MAX_RECORDS]

    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _extract_team(team_data: dict) -> dict:
    """Extract simplified structure from report team data."""
    squads = []
    for sq in team_data["squads"]:
        squads.append({
            "id": sq["squad_id"],
            "members": [p["name"] for p in sq["members"]],
        })
    return {
        "name": team_data["name"],
        "total_players": team_data["total_players"],
        "num_squads": team_data["num_squads"],
        "squads": squads,
    }


def format_record_text(record: dict) -> str:
    """Format a history record into readable text."""
    mode_map = {"balanced": "均衡", "random": "随机"}
    game_map = {"conquest": "征服", "breakthrough": "突破"}
    alloc_name = mode_map.get(record["alloc_mode"], record["alloc_mode"])
    game_name = game_map.get(record["game_mode"], record["game_mode"])
    bl = record["balance"]

    lines = [
        f'时间: {record["timestamp"]}',
        f'模式: {alloc_name} · {game_name}',
        "",
    ]

    for team_key in ["team_a", "team_b"]:
        t = record[team_key]
        lines.append(f'【{t["name"]}】({t["total_players"]}人, {t["num_squads"]}小队)')
        for sq in t["squads"]:
            members = "、".join(sq["members"])
            lines.append(f'  小队{sq["id"]}: {members}')
        lines.append("")

    if record["reserves"]:
        lines.append(f'【候补】{"、".join(record["reserves"])}')
        lines.append("")

    lines.append(f'均衡: KD差{bl["kd_diff"]} | KPM差{bl["kpm_diff"]} | 总分差{bl["score_diff"]}')

    return "\n".join(lines)


# -- Theme Config ------------------------------------------------

def load_config() -> dict:
    """Load config file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: dict) -> None:
    """Save config file."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
