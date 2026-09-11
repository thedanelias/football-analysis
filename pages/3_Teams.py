import streamlit as st
import pandas as pd
from scripts import team_data, seasons_competitions_data, parse_team_stats_season, player_data
from scripts.parse_team_stats_season import get_team_record

st.set_page_config(
    page_title = "Team Analysis",
    layout = "wide"
)

st.title("Team Analysis")

# get team id if selected from homepage
team_name = st.session_state.get("team_name")
team_seasons_df = pd.read_csv("resources/statsbomb_team_seasons.csv")
teams_df = pd.read_csv("resources/statsbomb_teams.csv")

st.sidebar.header("Filters")

teams = sorted(teams_df["team_name"].unique())
index = teams.index(team_name) if team_name else None

team = st.sidebar.selectbox(
    "Team", teams, index=index, placeholder="Select Team"
)

if not team:
    st.info("Select a team to view its season.")
    st.stop()

team_id = team_data.get_team_id_by_name(team)

team_competitions_df = team_seasons_df[team_seasons_df["team_name"] == team]
competition = st.sidebar.selectbox("Competition", sorted(team_competitions_df["competition_name"].unique()),
                                   index=None, placeholder="Select Competition")
competition_id = seasons_competitions_data.get_competition_id_by_name(competition)

team_seasons_df = team_competitions_df[team_competitions_df["competition_name"] == competition]
season = st.sidebar.selectbox("Season", sorted(team_seasons_df["season_name"].unique()), index=None,
                              placeholder="Select Season")
season_id = seasons_competitions_data.get_season_id_by_name(season, competition_id)



st.header(team)
season_stats = None
if season_id and competition_id and team_id is not None:
    season_stats = team_data.get_team_season_stats(team_id, competition_id, season_id)


if season_stats:
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    record = get_team_record(season_stats)
    col1.metric("Points", parse_team_stats_season.get_team_points(season_stats))
    goals = parse_team_stats_season.get_team_goals(season_stats)
    col2.metric("Goals For", goals[0])
    col3.metric("Goals Against", goals[1])
    col4.metric("Wins", record[0])
    col5.metric("Draws", record[1])
    col6.metric("Losses", record[2])

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Attack")
        attack = parse_team_stats_season.get_attack_frame(season_stats)
        st.dataframe(attack, width="stretch")

    with right:
        st.subheader("Defense")
        defense = parse_team_stats_season.get_defense_frame(season_stats)
        st.dataframe(defense, width="stretch")

    st.divider()
    st.subheader("Recent Results")

    fixtures = pd.DataFrame(parse_team_stats_season.get_recent_results(season_stats))

    st.dataframe(fixtures, width="stretch")

    st.divider()

    st.subheader("Squad Statstics")


    def squad_stats(team_id, competition_id, season_id):
        player_seasons = pd.read_csv("resources/statsbomb_player_seasons.csv")
        players_meta = pd.read_csv("resources/statsbomb_players.csv")
        squad = player_seasons[
            (player_seasons["team_id"] == int(team_id))
            & (player_seasons["competition_id"] == int(competition_id))
            & (player_seasons["season_id"] == int(season_id))
            & (player_seasons["num_matches"] > 0)
        ]
        name_map = dict(
            zip(
                players_meta["player_id"],
                players_meta["player_nickname"].fillna(players_meta["player_name"]),
            )
        )
        rows = []
        for pid in squad["player_id"].dropna().unique():
            pid = int(pid)
            stats = player_data.player_season_stats(pid, season_id, competition_id)
            rows.append(
                {
                    "Player": name_map.get(pid, str(pid)),
                    "Appearances": stats.get("appearances", 0),
                    "Goals": stats.get("goals", 0),
                    "Assists": stats.get("assists", 0),
                    "xG": round(stats.get("total_xg", 0.0), 2),
                }
            )
        return sorted(
            rows, key=lambda r: (r["Goals"], r["Assists"]), reverse=True
        )[:20]


    squad = pd.DataFrame(squad_stats(team_id, competition_id, season_id))
    st.dataframe(squad, width="stretch")