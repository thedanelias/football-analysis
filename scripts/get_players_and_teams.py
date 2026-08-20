from data_loader import DATA_PATH, ROOT, load_lineups
import csv

def get_lineup_match_ids():
    lineups_dir = DATA_PATH / "lineups"
    return sorted([p.stem for p in lineups_dir.glob("*.json") if p.is_file()])

def get_lineup_players_and_teams():
    players = {}
    teams = {}

    for match_id in get_lineup_match_ids():
        try:
            lineup = load_lineups(match_id)
        except FileNotFoundError:
            continue

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
    return players, teams

def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


players, teams = get_lineup_players_and_teams()
player_rows = [
            {
                "player_id": player_id,
                **player_info,
            }
            for player_id, player_info in sorted(players.items())
        ]
team_rows = [
            {"team_id": team_id, "team_name":teams[team_id]}
            for team_id in sorted(teams)
        ]

write_csv(ROOT / "resources" / "statsbomb_players.csv", ["player_id", "player_name",
                                    "player_nickname", "jersey_number", "country", "team_id", "team_name"], player_rows)
write_csv(ROOT / "resources" / "statsbomb_teams.csv", ["team_id", "team_name"], team_rows)