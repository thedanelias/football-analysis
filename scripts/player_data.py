"""
API:
    player_match_stats(match_id, player)   -> full stat dict for one game
    player_season_stats(player_id, season_id, competition_id=None)
                                           -> same shape, summed over a season
    get_seasons(player_id)                 -> available seasons for a player
"""

from collections import defaultdict
from scripts.data_loader import DATA_PATH, ROOT, load_all_matches, load_lineups
import csv
import json
import math

EVENTS_PATH = DATA_PATH / "events"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _load_raw_events(match_id):
    with (EVENTS_PATH / f"{match_id}.json").open(encoding="utf-8") as f:
        return json.load(f)


def _slug(name):
    return name.lower().replace(" ", "_").replace("*", "").replace("/", "_")


def _player_id_from_csv(player_name):
    """Resolve a full name, nickname or unique partial name to a player id."""
    path = ROOT / "resources" / "statsbomb_players.csv"
    if not path.exists():
        return None
    query = player_name.strip().lower()
    token_hits = []
    substring_hits = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            player_id = int(row["player_id"])
            fields = {row["player_name"].strip().lower()}
            if row["player_nickname"]:
                fields.add(row["player_nickname"].strip().lower())
            if query in fields:
                return player_id
            if any(query and query in f.split() for f in fields):
                token_hits.append(player_id)
            elif any(query and query in f for f in fields):
                substring_hits.append(player_id)
    for hits in (token_hits, substring_hits):
        distinct = set(hits)
        if len(distinct) == 1:
            return distinct.pop()
    return None


def _resolve_player(events, player):
    """Accept player id, full event name or nickname; return (id, name)."""
    for ev in events:
        p = ev.get("player")
        if not p:
            continue
        if p.get("id") == player or p.get("name") == player:
            return p["id"], p["name"]
    pid = _player_id_from_csv(player) if isinstance(player, str) else None
    if pid is None and isinstance(player, int):
        return None, None
    if pid is not None:
        for ev in events:
            p = ev.get("player")
            if p and p.get("id") == pid:
                return pid, p["name"]
        # player on the pitch but without any attributed event yet (rare)
        return pid, player
    return None, None


def _starter_ids(events):
    ids = set()
    for ev in events:
        if ev["type"]["name"] == "Starting XI":
            for entry in (ev.get("tactics") or {}).get("lineup", []):
                ids.add(entry["player"]["id"])
    return ids


def _subbed_on_ids(events):
    ids = set()
    for ev in events:
        if ev["type"]["name"] == "Substitution":
            rep = (ev.get("substitution") or {}).get("replacement") or {}
            if rep.get("id"):
                ids.add(rep["id"])
    return ids


def _team_names(events):
    names = []
    for ev in events:
        t = (ev.get("team") or {}).get("name")
        if t and t not in names:
            names.append(t)
    return names


# --------------------------------------------------------------------------
# accumulation -- every event type counts generically + detailed extraction
# --------------------------------------------------------------------------

def _accumulate(events, player_id, s):
    for ev in events:
        p = ev.get("player")
        if not p or p.get("id") != player_id:
            continue

        etype = ev["type"]["name"]
        s["total_events"] += 1
        s[_slug(etype) + "_events"] += 1          # generic: covers EVERY type
        if ev.get("under_pressure"):
            s["pressured_actions"] += 1
        if ev.get("counterpress"):
            s["counterpress_actions"] += 1

        fifty = ev.get("50_50")
        if fifty:
            outcome = (fifty.get("outcome") or {}).get("name", "")
            s["fifty_fifties"] += 1
            if outcome == "Won":
                s["fifty_fifties_won"] += 1
            elif outcome == "Lost":
                s["fifty_fifties_lost"] += 1
            elif outcome.startswith("Success"):
                s["fifty_fifties_success_to_team"] += 1

        if etype == "Pass":
            pas = ev.get("pass", {})
            s["pass_attempts"] += 1
            if "outcome" not in pas:
                s["passes_completed"] += 1
            else:
                s["passes_incomplete"] += 1
            loc, end_loc = ev.get("location"), pas.get("end_location")
            if loc and end_loc:
                s["total_pass_distance"] += math.dist(loc, end_loc)
            if pas.get("goal_assist"):
                s["assists"] += 1
            if pas.get("shot_assist"):
                s["key_passes"] += 1
            if pas.get("cross"):
                s["crosses"] += 1
            if pas.get("through_ball"):
                s["through_balls"] += 1
            if pas.get("switch"):
                s["switches"] += 1
            if pas.get("cut_back"):
                s["cut_backs"] += 1
            if pas.get("misinformation"):
                s["misinformation_passes"] += 1
            if pas.get("no_touch"):
                s["passes_no_touch"] += 1
            sub_type = (pas.get("type") or {}).get("name")
            if sub_type:
                s["pass_type_" + _slug(sub_type)] += 1
            body_part = (pas.get("body_part") or {}).get("name")
            if body_part:
                s["pass_body_" + _slug(body_part)] += 1
            height = (pas.get("height") or {}).get("name")
            if height:
                s["pass_height_" + _slug(height)] += 1
            technique = (pas.get("technique") or {}).get("name")
            if technique:
                s["pass_technique_" + _slug(technique)] += 1

        elif etype == "Shot":
            shot = ev.get("shot", {})
            outcome = (shot.get("outcome") or {}).get("name", "")
            shot_type = (shot.get("type") or {}).get("name", "")
            body_part = (shot.get("body_part") or {}).get("name", "")
            s["shots"] += 1
            s["total_xg"] += shot.get("statsbomb_xg") or 0.0
            if outcome == "Goal":
                s["goals"] += 1
            if outcome in ("Goal", "Saved", "Saved to Post", "Saved Off Target"):
                s["shots_on_target"] += 1
            if outcome.startswith("Saved"):
                s["shots_saved"] += 1
            if outcome == "Off Target":
                s["shots_off_target"] += 1
            if outcome == "Blocked":
                s["shots_blocked"] += 1
            if "Post" in outcome:
                s["shots_hit_post_or_bar"] += 1
            if shot_type == "Penalty":
                s["penalties_taken"] += 1
            elif shot_type == "Free Kick":
                s["free_kick_shots"] += 1
            elif shot_type == "Corner":
                s["corner_shots"] += 1
            elif shot_type == "Kick Off":
                s["kick_off_shots"] += 1
            if body_part == "Head":
                s["headed_shots"] += 1
            if shot.get("first_time"):
                s["first_time_shots"] += 1
            if shot.get("one_on_one"):
                s["one_on_one_shots"] += 1
            if shot.get("deflected"):
                s["deflected_shots"] += 1
            if shot.get("follows_dribble"):
                s["shots_after_dribble"] += 1
            if shot.get("open_goal"):
                s["open_goal_shots"] += 1
            if shot.get("aerial_won"):
                s["shots_after_aerial_won"] += 1

        elif etype == "Dribble":
            dr = ev.get("dribble", {})
            outcome = (dr.get("outcome") or {}).get("name", "")
            s["dribbles_attempted"] += 1
            if outcome == "Complete":
                s["dribbles_completed"] += 1
            if dr.get("nutmeg"):
                s["nutmegs"] += 1
            if dr.get("no_touch"):
                s["dribbles_no_touch"] += 1

        elif etype == "Carry":
            carry = ev.get("carry", {})
            loc, end_loc = ev.get("location"), carry.get("end_location")
            if loc and end_loc:
                s["carries"] += 1
                s["total_carry_distance"] += math.dist(loc, end_loc)

        elif etype == "Duel":
            duel = ev.get("duel", {})
            duel_type = (duel.get("type") or {}).get("name", "")
            outcome = (duel.get("outcome") or {}).get("name", "")
            s["duels"] += 1
            if outcome in ("Won", "Won Clean") or outcome.startswith("Success"):
                s["duels_won"] += 1
            if duel_type == "Tackle":
                s["tackles_attempted"] += 1
                if outcome in ("Won", "Won Clean"):
                    s["tackles_won"] += 1
            elif duel_type == "Sliding Tackle":
                s["sliding_tackles_attempted"] += 1
                if outcome in ("Won", "Won Clean"):
                    s["sliding_tackles_won"] += 1
            elif duel_type == "Aerial Won":
                s["aerial_duels_won"] += 1
            elif duel_type == "Aerial Lost":
                s["aerial_duels_lost"] += 1

        elif etype == "Clearance":
            cl = ev.get("clearance", {})
            s["clearances"] += 1
            if cl.get("aerial_won"):
                s["aerial_clearances_won"] += 1
            if cl.get("head"):
                s["headed_clearances"] += 1
            body_part = (cl.get("body_part") or {}).get("name")
            if body_part:
                s["clearance_body_" + _slug(body_part)] += 1

        elif etype == "Block":
            block = ev.get("block", {})
            s["blocks"] += 1
            if block.get("offensive_block"):
                s["offensive_blocks"] += 1
            if block.get("save_block"):
                s["save_blocks"] += 1
            if block.get("deflection"):
                s["deflections"] += 1

        elif etype == "Interception":
            outcome = ((ev.get("interception") or {}).get("outcome") or {}).get("name", "")
            s["interceptions"] += 1
            if outcome in ("Won", "Success in Play"):
                s["interceptions_won"] += 1
            elif outcome == "Lost":
                s["interceptions_lost"] += 1

        elif etype == "Ball Receipt*":
            outcome = ((ev.get("ball_receipt") or {}).get("outcome") or {}).get("name", "")
            s["ball_receipts"] += 1
            if outcome == "Incomplete":
                s["failed_ball_receipts"] += 1

        elif etype == "Ball Recovery":
            s["ball_recoveries"] += 1

        elif etype == "Foul Won":
            fw = ev.get("foul_won", {})
            s["fouls_won"] += 1
            if fw.get("penalty"):
                s["penalties_won"] += 1
            if fw.get("advantage"):
                s["fouls_won_advantage"] += 1

        elif etype == "Foul Committed":
            fc = ev.get("foul_committed", {})
            s["fouls_committed"] += 1
            if fc.get("penalty"):
                s["penalties_conceded"] += 1
            if fc.get("advantage"):
                s["fouls_committed_advantage"] += 1
            card = (fc.get("card") or {}).get("name")
            if card == "Yellow Card":
                s["yellow_cards"] += 1
            elif card == "Second Yellow":
                s["second_yellows"] += 1
            elif card == "Red Card":
                s["red_cards"] += 1

        elif etype == "Bad Behaviour":
            card = ((ev.get("bad_behaviour") or {}).get("card") or {}).get("name")
            if card == "Yellow Card":
                s["yellow_cards"] += 1
            elif card == "Second Yellow":
                s["second_yellows"] += 1
            elif card == "Red Card":
                s["red_cards"] += 1

        elif etype == "Dispossessed":
            s["times_dispossessed"] += 1

        elif etype == "Miscontrol":
            s["miscontrols"] += 1

        elif etype == "Dribbled Past":
            s["times_dribbled_past"] += 1

        elif etype == "Error":
            s["errors"] += 1

        elif etype == "Pressure":
            s["pressures_applied"] += 1

        elif etype == "Goal Keeper":
            gk = ev.get("goalkeeper", {})
            gk_type = (gk.get("type") or {}).get("name", "")
            outcome = (gk.get("outcome") or {}).get("name", "")
            position = (gk.get("position") or {}).get("name", "")
            s["gk_action_" + _slug(gk_type or "unknown")] += 1
            if gk_type == "Save" and outcome != "Conceded":
                s["gk_saves"] += 1
            elif gk_type == "Shot Faced":
                s["gk_shots_faced"] += 1
            elif gk_type == "Goal Conceded":
                s["gk_goals_conceded"] += 1
            elif gk_type == "Punch":
                s["gk_punches"] += 1
            elif gk_type == "Collected":
                s["gk_collections"] += 1
                if outcome == "Claim":
                    s["gk_claims"] += 1
            elif gk_type == "Keeper Sweeper":
                s["gk_sweeper_actions"] += 1
            elif gk_type == "Smother":
                s["gk_smoothers"] += 1
            elif gk_type == "Clearance":
                s["gk_clearances"] += 1
            if position == "Goalkeeper":
                s["gk_events_as_gk"] += 1


def _finalize(raw, extra_meta=None):
    stats = {}
    if extra_meta:
        stats.update(extra_meta)

    for key in ("total_events", "pass_attempts", "passes_completed", "passes_incomplete",
                "shots", "goals", "assists", "key_passes", "total_xg",
                "dribbles_attempted", "dribbles_completed"):
        if key not in raw:
            raw[key] = raw.get(key, 0)

    total = float(raw.get("total_pass_distance", 0.0))
    attempts = raw.get("pass_attempts", 0)
    completed = raw.get("passes_completed", 0)
    if attempts:
        stats["pass_completion_pct"] = round(100.0 * completed / attempts, 1)
    if raw.get("pass_attempts"):
        stats["avg_pass_distance_m"] = round(total / attempts, 2)

    attempted = raw.get("dribbles_attempted", 0)
    if attempted:
        stats["dribble_success_pct"] = round(
            100.0 * raw.get("dribbles_completed", 0) / attempted, 1)
    duels = raw.get("duels", 0)
    if duels:
        stats["duel_win_pct"] = round(100.0 * raw.get("duels_won", 0) / duels, 1)
    shots = raw.get("shots", 0)
    if shots:
        stats["xg_per_shot"] = round(raw.get("total_xg", 0.0) / shots, 3)

    # approximate touch count (receivals + carries + ball-striking actions)
    stats["touches"] = int(sum(
        raw.get(k, 0)
        for k in ("ball_receipts", "carries", "dribbles_attempted", "shots",
                  "miscontrols", "times_dispossessed")
    ))

    for key in sorted(raw):
        value = raw[key]
        if isinstance(value, float):
            value = round(value, 2)
            if value.is_integer():
                value = int(value)
        stats[key] = value
    return stats


def _match_context(events, player_id):
    starters = _starter_ids(events)
    subs_on = _subbed_on_ids(events)
    team_names = _team_names(events)
    player_team = None
    for ev in events:
        p, t = ev.get("player"), (ev.get("team") or {}).get("name")
        if p and t and p.get("id") == player_id:
            player_team = t
            break
    opponent = next((n for n in team_names if n != player_team), None)
    return {
        "started": player_id in starters,
        "came_on_as_sub": player_id in subs_on,
        "team_name": player_team,
        "opponent_name": opponent,
    }


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def get_player_events(match_id, player):
    """Raw StatsBomb event dicts attributed to the given player in one match."""
    events = _load_raw_events(match_id)
    pid, name = _resolve_player(events, player)
    if pid is None:
        raise ValueError(f"Player {player!r} not found in match {match_id}")
    return [ev for ev in events
            if (ev.get("player") or {}).get("id") == pid]


def _lineup_entry(match_id, player):
    """Find a player in the match lineups even when they have zero events."""
    try:
        lineups = load_lineups(match_id)
    except FileNotFoundError:
        return None
    query = str(player).strip().lower()
    for row in lineups.to_dict(orient="records"):
        for entry in row.get("lineup", []):
            names = {str(entry.get("player_name", "")).strip().lower(),
                     str(entry.get("player_nickname") or "").strip().lower()}
            if int(entry.get("player_id")) == player or query in names:
                return {
                    "player_id": int(entry["player_id"]),
                    "player_name": entry.get("player_name"),
                    "team_name": row.get("team_name"),
                }
    return None


def player_match_stats(match_id, player):
    """Every tracked statistic for `player` (id, name or nickname) in one game."""
    events = _load_raw_events(match_id)
    pid, pname = _resolve_player(events, player)

    if pid is None:
        bench = _lineup_entry(match_id, player)
        if bench is None:
            raise ValueError(f"Player {player!r} not found in match {match_id}")
        teams = _team_names(events)
        meta = {
            "match_id": int(match_id),
            **bench,
            "started": False,
            "came_on_as_sub": False,
            "opponent_name": next((n for n in teams if n != bench["team_name"]), None),
            "appearances": 0,
            "starts": 0,
        }
        return _finalize(defaultdict(float), meta)

    raw = defaultdict(float)
    participation = _accumulate_with_participation(events, pid, raw)
    context = _match_context(events, pid)

    meta = {
        "match_id": int(match_id),
        "player_id": pid,
        "player_name": pname,
        **context,
        **participation,
    }
    return _finalize(raw, meta)


def _accumulate_with_participation(events, pid, raw):
    starters = _starter_ids(events)
    subs_on = _subbed_on_ids(events)
    has_activity = any((ev.get("player") or {}).get("id") == pid for ev in events)
    started = pid in starters
    came_on = pid in subs_on
    if started:
        _accumulate(events, pid, raw)
        return {"appearances": 1, "starts": 1}
    if came_on or has_activity:
        _accumulate(events, pid, raw)
        return {"appearances": 1, "starts": 0}
    return {"appearances": 0, "starts": 0}   # unused substitute


# ------------------------------ season level ------------------------------

def get_seasons(player_id):
    """{season_key: label} for every season the player appears in locally."""
    seasons = {}
    id_str = str(player_id)
    path = ROOT / "resources" / "statsbomb_player_seasons.csv"
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            if row[0] == id_str:
                seasons[row[6] + "," + row[4]] = row[7] + " " + row[5]
    return seasons


def _season_rows(player_id, season_id=None, competition_id=None):
    """player_seasons.csv rows for this player, optionally filtered."""
    path = ROOT / "resources" / "statsbomb_player_seasons.csv"
    rows = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["player_id"]) != int(player_id):
                continue
            if season_id is not None and int(row["season_id"]) != int(season_id):
                continue
            if competition_id is not None and int(row["competition_id"]) != int(competition_id):
                continue
            rows.append({
                "team_id": int(row["team_id"]),
                "competition_id": int(row["competition_id"]),
                "season_id": int(row["season_id"]),
                "team_name": row["team_name"],
                "competition_name": row["competition_name"],
                "season_name": row["season_name"],
            })
    return rows


def get_player_match_ids(player_id, season_id=None, competition_id=None):
    """Match ids of all games the player's team(s) played in that season.

    Participation itself (start/sub/unused) is resolved per match by
    player_season_stats; this returns the candidate fixture list.
    """
    matches_df = load_all_matches()
    ids = []
    seen = set()
    for row in _season_rows(player_id, season_id, competition_id):
        sel = matches_df[
            (matches_df["season_id"] == row["season_id"]) &
            (matches_df["competition_id"] == row["competition_id"]) &
            ((matches_df["home_team_id"] == row["team_id"]) |
             (matches_df["away_team_id"] == row["team_id"]))
        ]
        for match_id in sel["match_id"]:
            mid = int(match_id)
            if mid not in seen:
                seen.add(mid)
                ids.append(mid)
    return sorted(ids)


def player_season_stats(player_id, season_id, competition_id=None):
    """Aggregate every tracked statistic over a whole season for one player.

    Only matches where the player actually featured (starter, sub used, or at
    least one attributed event) contribute to the totals; unused-substitute
    games count only towards `unused_sub_appearances`.
    """
    raw = defaultdict(float)
    appearances = starts = sub_uses = unused = matches_scanned = 0

    for match_id in get_player_match_ids(player_id, season_id, competition_id):
        try:
            events = _load_raw_events(match_id)
        except FileNotFoundError:
            continue
        matches_scanned += 1
        starters = _starter_ids(events)
        subs_on = _subbed_on_ids(events)
        has_activity = any((ev.get("player") or {}).get("id") == player_id
                           for ev in events)

        if player_id in starters:
            appearances += 1
            starts += 1
            _accumulate(events, player_id, raw)
        elif player_id in subs_on or has_activity:
            appearances += 1
            sub_uses += 1
            _accumulate(events, player_id, raw)
        else:
            unused += 1

    teams = sorted({r["team_name"] for r in _season_rows(player_id, season_id, competition_id)})
    competitions = sorted({r["competition_name"]
                           for r in _season_rows(player_id, season_id, competition_id)})
    meta = {
        "player_id": int(player_id),
        "season_id": season_id if season_id is None else int(season_id),
        "competition_id": competition_id,
        "season_teams": teams,
        "competitions": competitions,
        "matches_scanned": matches_scanned,
        "appearances": appearances,
        "starts": starts,
        "substitute_appearances": sub_uses,
        "unused_sub_appearances": unused,
    }
    return _finalize(raw, meta)


def aggregate_stat_dicts(stat_dicts):
    """Sum a list of already-finalized stat dicts into one (e.g. career totals)."""
    raw = defaultdict(float)
    meta_keys = ("match_id", "player_id", "season_id", "competition_id",
                 "started", "came_on_as_sub")
    text_meta = {}
    for d in stat_dicts:
        for key, value in d.items():
            if key in meta_keys:
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                raw[key] += value
            elif isinstance(value, str) and key not in text_meta:
                text_meta[key] = value
    merged = {k: v for k, v in text_meta.items() if k.endswith("_name")}
    return _finalize(raw, merged)
