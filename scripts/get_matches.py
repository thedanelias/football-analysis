from data_loader import ROOT, load_all_matches, write_csv

HEADER = ["match_id", "match_date", "kick_off", "match_week",
          "competition_id", "competition_name", "season_id", "season_name",
          "competition_stage", "home_team_id", "home_team_name", "home_score",
          "away_score", "away_team_name", "away_team_id", "stadium", "referee"]


def get_searchable_matches():
    matches_df = load_all_matches()
    return matches_df[HEADER].to_dict(orient="records")



out_path = ROOT / "resources" / "statsbomb_matches.csv"
write_csv(out_path, HEADER, get_searchable_matches())
