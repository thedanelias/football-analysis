"""
API:
    get_team_season_stats(team_id, competition_id, season_id) -> Gets all stats for a team for one season in one
    competition
    get_team_seasons(team_id) -> all seasons a team appears in
    get_team_id_by_name(team_name) -> get team id from its name
"""

import json
from functools import lru_cache

import pandas as pd

from data_loader import (
    DATA_PATH,
    ROOT,
    flatten_match,
    load_all_matches,
    load_events,
)

ON_TARGET_OUTCOMES = {"Goal", "Saved", "Saved to Post"}
OFF_TARGET_OUTCOMES = {"Off T", "Wayward"}
WOODWORK_OUTCOMES = {"Post", "Saved to Post"}
OWN_GOAL_OUTCOME = "Own Goal For"
PENALTY_TYPE = "Penalty"
SAVE_TYPES = {"Save", "Penalty Saved", "Shot Saved", "Shot Saved to Post"}
DUEL_WON_OUTCOMES = {"Won", "Success In Play", "Success Out"}
LONG_PASS_METRES = 30.0
BIG_CHANCE_XG_THRESHOLD = 0.3

_SUMMED_METRICS = [
    "goals_scored",
    "own_goals",
    "goals_for",
    "goals_against",
    "xg",
    "xg_for",
    "np_xg",
    "xg_against",
    "shots",
    "shots_on_target",
    "shots_off_target",
    "shots_blocked",
    "hits_woodwork",
    "big_chances",
    "penalties_taken",
    "penalties_scored",
    "passes",
    "passes_completed",
    "passes_long",
    "crosses",
    "through_balls",
    "switches",
    "corners",
    "free_kicks",
    "throw_ins",
    "goal_kicks",
    "dribbles",
    "dribbles_completed",
    "duels",
    "duels_won",
    "tackles",
    "tackles_won",
    "interceptions",
    "clearances",
    "blocks",
    "recoveries",
    "pressures",
    "counterpressures",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "second_yellows",
    "red_cards",
    "offsides",
    "errors",
    "miscontrols",
    "dispossessed",
    "dribbled_past",
    "gk_saves",
]


def _name(value):
    return value.get("name") if isinstance(value, dict) else None


def _sub_dicts(events, column):
    if column in events.columns:
        return events[column].map(lambda v: v if isinstance(v, dict) else {})
    return pd.Series([{} for _ in range(len(events))], index=events.index)


def _flag_column(events, column):
    if column in events.columns:
        return events[column].fillna(False).astype(bool)
    return pd.Series(False, index=events.index)


@lru_cache(maxsize=64)
def _prepared_events(match_id):
    events = load_events(str(match_id))

    shot = _sub_dicts(events, "shot")
    pas = _sub_dicts(events, "pass")
    duel = _sub_dicts(events, "duel")
    dribble = _sub_dicts(events, "dribble")
    keeper = _sub_dicts(events, "goalkeeper")
    bad_behaviour = _sub_dicts(events, "bad_behaviour")
    foul = _sub_dicts(events, "foul_committed")

    def card_name(sub):
        return sub.map(lambda d: _name(d.get("card")))

    cards = card_name(foul).combine(card_name(bad_behaviour), lambda a, b: a if a else b)

    prep = pd.DataFrame(index=events.index)
    prep["type"] = events["type"].map(_name)
    prep["team_id"] = events["team"].map(lambda v: v.get("id"))
    prep["possession_team_id"] = events["possession_team"].map(lambda v: v.get("id"))

    prep["shot_outcome"] = shot.map(lambda d: _name(d.get("outcome")))
    prep["shot_xg"] = shot.map(lambda d: d.get("statsbomb_xg") or 0.0)
    prep["shot_type"] = shot.map(lambda d: _name(d.get("type")))

    prep["pass_outcome"] = pas.map(lambda d: _name(d.get("outcome")))
    prep["pass_length"] = pas.map(lambda d: d.get("length") or 0.0)
    prep["pass_type"] = pas.map(lambda d: _name(d.get("type")))
    prep["pass_is_cross"] = pas.map(lambda d: bool(d.get("cross")))
    prep["pass_is_through_ball"] = pas.map(lambda d: bool(d.get("through_ball")))
    prep["pass_is_switch"] = pas.map(lambda d: bool(d.get("switch")))

    prep["duel_type"] = duel.map(lambda d: _name(d.get("type")))
    prep["duel_outcome"] = duel.map(lambda d: _name(d.get("outcome")))
    prep["dribble_outcome"] = dribble.map(lambda d: _name(d.get("outcome")))
    prep["gk_type"] = keeper.map(lambda d: _name(d.get("type")))
    prep["card"] = cards
    prep["counterpress"] = _flag_column(events, "counterpress")
    return prep


def _team_metrics(prep, team_id):
    mine = prep[prep["team_id"] == team_id]

    possession_pct = round(100.0 * len(mine) / len(prep), 1) if len(prep) else 0.0

    shots = mine[mine["type"] == "Shot"]
    own_goal = shots["shot_outcome"] == OWN_GOAL_OUTCOME
    regular = shots[~own_goal]
    penalties = regular[regular["shot_type"] == PENALTY_TYPE]
    goals = regular["shot_outcome"] == "Goal"

    passes = mine[mine["type"] == "Pass"]
    passes_completed = passes["pass_outcome"].isna()

    duels = mine[mine["duel_outcome"].notna()]
    duels_won = duels["duel_outcome"].isin(DUEL_WON_OUTCOMES)
    tackles = duels["duel_type"] == "Tackle"

    dribbles = mine[mine["dribble_outcome"].notna()]

    pressures = mine["type"] == "Pressure"

    metrics = {
        "possession_pct": possession_pct,
        "goals_scored": int(goals.sum()),
        "own_goals": int(own_goal.sum()),
        "xg": round(float(regular["shot_xg"].sum()), 2),
        "np_xg": round(
            float(regular.loc[regular["shot_type"] != PENALTY_TYPE, "shot_xg"].sum()), 2
        ),
        "shots": len(regular),
        "shots_on_target": int(regular["shot_outcome"].isin(ON_TARGET_OUTCOMES).sum()),
        "shots_off_target": int(regular["shot_outcome"].isin(OFF_TARGET_OUTCOMES).sum()),
        "shots_blocked": int((regular["shot_outcome"] == "Blocked").sum()),
        "hits_woodwork": int(regular["shot_outcome"].isin(WOODWORK_OUTCOMES).sum()),
        "big_chances": int((regular["shot_xg"] >= BIG_CHANCE_XG_THRESHOLD).sum()),
        "penalties_taken": len(penalties),
        "penalties_scored": int((penalties["shot_outcome"] == "Goal").sum()),
        "passes": len(passes),
        "passes_completed": int(passes_completed.sum()),
        "passes_long": int((passes["pass_length"] >= LONG_PASS_METRES).sum()),
        "crosses": int(passes["pass_is_cross"].sum()),
        "through_balls": int(passes["pass_is_through_ball"].sum()),
        "switches": int(passes["pass_is_switch"].sum()),
        "corners": int((passes["pass_type"] == "Corner").sum()),
        "free_kicks": int((passes["pass_type"] == "Free Kick").sum()),
        "throw_ins": int((passes["pass_type"] == "Throw-in").sum()),
        "goal_kicks": int((passes["pass_type"] == "Goal Kick").sum()),
        "dribbles": len(dribbles),
        "dribbles_completed": int((dribbles["dribble_outcome"] == "Complete").sum()),
        "duels": len(duels),
        "duels_won": int(duels_won.sum()),
        "tackles": int(tackles.sum()),
        "tackles_won": int((tackles & duels_won).sum()),
        "interceptions": int((mine["type"] == "Interception").sum()),
        "clearances": int((mine["type"] == "Clearance").sum()),
        "blocks": int((mine["type"] == "Block").sum()),
        "recoveries": int((mine["type"] == "Ball Recovery").sum()),
        "pressures": int(pressures.sum()),
        "counterpressures": int((pressures & mine["counterpress"]).sum()),
        "fouls_committed": int((mine["type"] == "Foul Committed").sum()),
        "fouls_won": int((mine["type"] == "Foul Won").sum()),
        "yellow_cards": int((mine["card"] == "Yellow Card").sum()),
        "second_yellows": int((mine["card"] == "Second Yellow").sum()),
        "red_cards": int((mine["card"] == "Red Card").sum()),
        "offsides": int((mine["type"] == "Offside").sum()),
        "errors": int((mine["type"] == "Error").sum()),
        "miscontrols": int((mine["type"] == "Miscontrol").sum()),
        "dispossessed": int((mine["type"] == "Dispossessed").sum()),
        "dribbled_past": int((mine["type"] == "Dribbled Past").sum()),
        "gk_saves": int(mine["gk_type"].isin(SAVE_TYPES).sum()),
    }

    metrics["pass_accuracy_pct"] = (
        round(100.0 * metrics["passes_completed"] / metrics["passes"], 1)
        if metrics["passes"]
        else 0.0
    )
    metrics["shot_conversion_pct"] = (
        round(100.0 * metrics["goals_scored"] / metrics["shots"], 1)
        if metrics["shots"]
        else 0.0
    )
    return metrics


def _get_match_stats(match_id):
    """Raw per-team metrics for both teams in a single match."""
    prep = _prepared_events(match_id)
    team_ids = [int(tid) for tid in prep["team_id"].dropna().unique()]
    stats = {tid: _team_metrics(prep, tid) for tid in team_ids}

    for tid, metrics in stats.items():
        opp_id = next(other for other in team_ids if other != tid)
        opp = stats[opp_id]
        metrics["goals_for"] = metrics["goals_scored"] + opp["own_goals"]
        metrics["goals_against"] = opp["goals_scored"] + metrics["own_goals"]
        metrics["xg_for"] = metrics["xg"]
        metrics["xg_against"] = opp["xg"]
        metrics["clean_sheet"] = metrics["goals_against"] == 0
    return stats


_match_info_cache = {}


def _get_match_info(match_id):
    """Competition/team/score metadata for a match, from the matches files."""
    match_id = int(match_id)
    if match_id not in _match_info_cache:
        for path in sorted((DATA_PATH / "matches").glob("*/*.json")):
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            for match in data:
                if int(match.get("match_id", -1)) == match_id:
                    _match_info_cache[match_id] = flatten_match(match)
                    break
            if match_id in _match_info_cache:
                break
        else:
            _match_info_cache[match_id] = None
    return _match_info_cache[match_id]


def get_team_match_stats(match_id, team_id):
    """All statistics for one team in one match (totals + match context)."""
    team_id = int(team_id)
    stats = _get_match_stats(match_id)
    if team_id not in stats:
        raise ValueError(f"Team {team_id} has no events in match {match_id}")
    metrics = dict(stats[team_id])

    info = _get_match_info(match_id) or {}
    home_id = info.get("home_team_id")
    away_id = info.get("away_team_id")
    is_home = team_id == home_id
    opp_id = away_id if is_home else home_id
    gf, ga = metrics["goals_for"], metrics["goals_against"]

    metrics.update(
        {
            "match_id": int(match_id),
            "match_date": info.get("match_date"),
            "competition_name": info.get("competition_name"),
            "season_name": info.get("season_name"),
            "venue": "Home" if is_home else "Away",
            "opponent_id": opp_id,
            "opponent_name": info.get("away_team_name" if is_home else "home_team_name"),
            "score": f"{info.get('home_score')}-{info.get('away_score')}",
            "result": "W" if gf > ga else "D" if gf == ga else "L",
            "points": 3 if gf > ga else 1 if gf == ga else 0,
            "failed_to_score": gf == 0,
        }
    )
    return metrics


def get_team_id_by_name(team_name):
    teams_csv = ROOT / "resources" / "statsbomb_teams.csv"
    if teams_csv.exists():
        teams = pd.read_csv(teams_csv)
        hit = teams[
            teams["team_name"].str.lower() == str(team_name).strip().lower()
        ]
        if not hit.empty:
            return int(hit.iloc[0]["team_id"])

    matches = load_all_matches()
    for _, row in matches.iterrows():
        if str(row["home_team_name"]).lower() == str(team_name).lower():
            return int(row["home_team_id"])
        if str(row["away_team_name"]).lower() == str(team_name).lower():
            return int(row["away_team_id"])
    return None


def get_team_seasons(team_id):
    """All (competition, season) pairs the team appears in, with match counts."""
    matches = load_all_matches()
    mine = matches[
        (matches["home_team_id"] == team_id) | (matches["away_team_id"] == team_id)
    ]
    grouped = (
        mine.groupby(
            [
                "competition_id",
                "competition_name",
                "season_id",
                "season_name",
            ],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "num_matches"})
        .sort_values(["competition_name", "season_name"])
    )
    return grouped.to_dict(orient="records")


def get_team_season_stats(team_id, competition_id, season_id):
    """Aggregate all statistics for a team across one competition season."""
    team_id = int(team_id)
    matches = load_all_matches()
    mine = matches[
        (matches["competition_id"] == int(competition_id))
        & (matches["season_id"] == int(season_id))
        & ((matches["home_team_id"] == team_id) | (matches["away_team_id"] == team_id))
    ]

    team_name = None
    totals = {key: 0 for key in _SUMMED_METRICS}
    possession_values = []
    match_summaries = []
    missing_event_matches = []
    wins = draws = losses = points = 0

    for _, row in mine.sort_values("match_date").iterrows():
        match_id = int(row["match_id"])
        try:
            stats = get_team_match_stats(match_id, team_id)
        except (ValueError, FileNotFoundError):
            missing_event_matches.append(match_id)
            continue

        if team_name is None:
            is_home = row["home_team_id"] == team_id
            team_name = row["home_team_name" if is_home else "away_team_name"]
        for key in _SUMMED_METRICS:
            totals[key] += stats[key]
        possession_values.append(stats["possession_pct"])
        wins += stats["result"] == "W"
        draws += stats["result"] == "D"
        losses += stats["result"] == "L"
        points += stats["points"]

        match_summaries.append(
            {
                "match_id": match_id,
                "match_date": stats["match_date"],
                "venue": stats["venue"],
                "opponent_id": stats["opponent_id"],
                "opponent_name": stats["opponent_name"],
                "score": stats["score"],
                "result": stats["result"],
                "goals_for": stats["goals_for"],
                "goals_against": stats["goals_against"],
                "xg_for": stats["xg_for"],
                "xg_against": stats["xg_against"],
                "possession_pct": stats["possession_pct"],
                "clean_sheet": stats["clean_sheet"],
            }
        )

    num_matches = len(match_summaries)
    averages = {
        key: round(total / num_matches, 2) for key, total in totals.items()
    } if num_matches else {}
    if possession_values:
        averages["possession_pct"] = round(sum(possession_values) / num_matches, 1)
        totals["possession_pct"] = round(sum(possession_values), 1)

    if num_matches:
        averages["pass_accuracy_pct"] = (
            round(100.0 * totals["passes_completed"] / totals["passes"], 1)
            if totals["passes"]
            else 0.0
        )
        averages["shot_conversion_pct"] = (
            round(100.0 * totals["goals_scored"] / totals["shots"], 1)
            if totals["shots"]
            else 0.0
        )

    return {
        "team_id": team_id,
        "team_name": team_name,
        "competition_id": int(competition_id),
        "season_id": int(season_id),
        "num_matches": num_matches,
        "num_matches_missing_events": len(missing_event_matches),
        "missing_event_match_ids": missing_event_matches,
        "record": {
            "wins": int(wins),
            "draws": int(draws),
            "losses": int(losses),
            "points": int(points),
            "points_per_game": round(points / num_matches, 2) if num_matches else 0.0,
        },
        "totals": totals,
        "averages": averages,
        "matches": match_summaries,
    }
