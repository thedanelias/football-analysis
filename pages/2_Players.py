import pandas as pd
import streamlit as st
from scripts import player_data, seasons_competitions_data, pages_common

st.set_page_config(
    page_title="Player Analysis",
    layout="wide",
)

st.title("Player Analysis")
st.sidebar.header("Filters")

players_df = pages_common.load_csv("resources/statsbomb_players.csv")
player_name = st.session_state.get("player_name")

players = sorted(players_df["player_nickname"].fillna(players_df["player_name"]).tolist())
index = players.index(player_name) if player_name else None

player = st.sidebar.selectbox(
    "Player", players, index=index, placeholder="Select Player"
)

player_id = player_data._player_id_from_csv(player) if player else None

competitions_df = pages_common.load_csv("resources/statsbomb_player_seasons.csv")
competitions_df = competitions_df[competitions_df["player_id"] == player_id]
competition = st.sidebar.selectbox("Competition", sorted(competitions_df["competition_name"].unique()),
                                   index=None, placeholder="Select Competition")
competition_id = seasons_competitions_data.get_competition_id_by_name(competition) if competition else None

seasons_df = competitions_df[competitions_df["competition_id"] == competition_id]
season = st.sidebar.selectbox("Season", sorted(seasons_df["season_name"].unique()),
                                   index=None, placeholder="Select Season")
season_id = seasons_competitions_data.get_season_id_by_name(season) if season else None
season_stats = None

if player_id is None or season_id is None or competition_id is None:
    st.info("Select a player to view their season.")
    st.stop()

if player_id is not None and season_id is not None and competition_id is not None:
    season_stats = player_data.player_season_stats(player_id, season_id, competition_id)


if season_stats:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Goals", season_stats.get("goals", 0))
    col2.metric("Assists", season_stats.get("assists", 0))
    col3.metric("xG", season_stats.get("total_xg", 0))
    col4.metric("Appearances", season_stats.get("appearances", 0))

    st.divider()

    st.subheader("Last 5 Matches")

    def recent_player_matches(player_id, season_id, competition_id):
        played = []
        for match_id in reversed(
            player_data.get_player_match_ids(player_id, season_id, competition_id)
        ):
            try:
                stats = player_data.player_match_stats(match_id, player_id)
            except (ValueError, FileNotFoundError):
                continue
            if stats.get("appearances", 0) > 0:
                played.append(stats)
            if len(played) >= 5:
                break
        return played


    recent = recent_player_matches(player_id, season_id, competition_id)
    st.divider()

    if recent:
        xg_by_match = pd.DataFrame(
            {
                "Match": range(len(recent)), # needed so matches against same opponent aren't counted in the same bar
                "Opponent": [m['opponent_name'] for m in recent],
                "xG": [m.get("total_xg", 0.0) for m in recent]
            }
        )
        st.bar_chart(xg_by_match.set_index("Match")["xG"])
        # adds label to bar chart
        st.dataframe(xg_by_match[["Match", "Opponent", "xG"]], hide_index=True)
    else:
        st.info("No recent matches found for this player.")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Attack")

        attack = pd.DataFrame(
            {
                "Metric": ["Shots", "Goals", "xG", "Key Passes", "Dribbles Completed"],
                "Value": [
                    season_stats.get("shots", 0),
                    season_stats.get("goals", 0),
                    season_stats.get("total_xg", 0),
                    season_stats.get("key_passes", 0),
                    season_stats.get("dribbles_completed", 0),
                ],
            }
        )

        st.dataframe(attack, width="stretch")

    with right:
        st.subheader("Defense")

        defense = pd.DataFrame(
            {
                "Metric": [
                    "Tackles Won",
                    "Interceptions",
                    "Recoveries",
                    "Duels Won",
                    "Pressures",
                ],
                "Value": [
                    season_stats.get("tackles_won", 0),
                    season_stats.get("interceptions", 0),
                    season_stats.get("ball_recoveries", 0),
                    season_stats.get("duels_won", 0),
                    season_stats.get("pressures_applied", 0),
                ],
            }
        )

        st.dataframe(defense, width="stretch")

    st.divider()

    st.subheader("Recent Matches")

    if recent:
        fixtures = pd.DataFrame(
            {
                "Opponent": [m["opponent_name"] for m in recent],
                "Goals": [m.get("goals", 0) for m in recent],
                "Assists": [m.get("assists", 0) for m in recent],
                "xG": [round(m.get("total_xg", 0.0), 2) for m in recent],
            }
        )
        st.dataframe(fixtures, width="stretch")
    else:
        st.info("No recent matches found for this player.")