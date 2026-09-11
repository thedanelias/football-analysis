import pandas as pd

from data_loader import DATA_PATH, ROOT, load_lineups, load_all_matches, write_csv


def get_lineup_match_ids():
    lineups_dir = DATA_PATH / "lineups"
    return sorted([p.stem for p in lineups_dir.glob("*.json") if p.is_file()])


def build_match_season_map():
    matches_df = load_all_matches()
    return {
        int(row["match_id"]): (
            row["competition_id"],
            row["competition_name"],
            row["season_id"],
            row["season_name"],
        )
        for _, row in matches_df.iterrows()
    }


def get_lineup_players_and_teams(match_seasons=None):
    """One pass over all lineups: player/team info plus season appearances."""
    if match_seasons is None:
        match_seasons = build_match_season_map()

    players = {}
    teams = {}
    # (player_id, team_id, team_name, competition_id, competition_name, season_id, season_name) -> num matches
    appearances = {}

    for match_id in get_lineup_match_ids():
        try:
            lineup = load_lineups(match_id)
        except FileNotFoundError:
            continue

        season = match_seasons.get(int(match_id))

        for row in lineup.to_dict(orient='records'):
            team_id = int(row.get("team_id"))
            team_name = row.get("team_name")
            teams[team_id] = team_name

            for player in row.get("lineup", []):
                player_id = int(player.get("player_id"))
                if player_id not in players:
                    players[player_id] = {
                        "player_name": player.get("player_name"),
                        "player_nickname": player.get("player_nickname"),
                        "jersey_number": player.get("jersey_number"),
                        "country": player.get("country"),
                        "team_id": team_id,
                        "team_name": team_name
                    }

                if season is not None:
                    key = (player_id, team_id, team_name, *season)
                    appearances[key] = appearances.get(key, 0) + 1

    return players, teams, appearances


def format_player_seasons(players, appearances):
    rows = []
    for key, num_matches in sorted(appearances.items()):
        player_id, team_id, team_name, comp_id, comp_name, season_id, season_name = key
        rows.append({
            "player_id": player_id,
            "player_name": players[player_id]["player_name"],
            "team_id": team_id,
            "team_name": team_name,
            "competition_id": comp_id,
            "competition_name": comp_name,
            "season_id": season_id,
            "season_name": season_name,
            "num_matches": num_matches,
        })
    return rows


def get_team_seasons(matches_df):
    columns = ["team_id", "team_name", "competition_id",
               "competition_name", "season_id", "season_name"]

    home = matches_df.rename(columns={"home_team_id": "team_id", "home_team_name": "team_name"})
    away = matches_df.rename(columns={"away_team_id": "team_id", "away_team_name": "team_name"})
    combined = pd.concat([home[columns], away[columns]], ignore_index=True)

    counts = combined.groupby(columns, as_index=False).size()
    counts = counts.rename(columns={"size": "num_matches"})
    return counts.to_dict(orient="records")


def get_all_players_and_teams():
    matches_df = load_all_matches()
    players, teams, appearances = get_lineup_players_and_teams()

    player_rows = [
        {
            "player_id": player_id,
            **player_info,
        }
        for player_id, player_info in sorted(players.items())
    ]
    team_rows = [
        {"team_id": team_id, "team_name": teams[team_id]}
        for team_id in sorted(teams)
    ]

    write_csv(ROOT / "resources" / "statsbomb_players.csv", ["player_id", "player_name",
                                        "player_nickname", "jersey_number", "country", "team_id", "team_name"], player_rows)
    write_csv(ROOT / "resources" / "statsbomb_teams.csv", ["team_id", "team_name"], team_rows)
    write_csv(ROOT / "resources" / "statsbomb_player_seasons.csv",
              ["player_id", "player_name", "team_id", "team_name",
               "competition_id", "competition_name", "season_id", "season_name", "num_matches"],
              format_player_seasons(players, appearances))
    write_csv(ROOT / "resources" / "statsbomb_team_seasons.csv",
              ["team_id", "team_name", "competition_id", "competition_name",
               "season_id", "season_name", "num_matches"],
              get_team_seasons(matches_df))
