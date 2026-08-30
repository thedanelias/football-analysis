import streamlit as st
import pandas as pd
import numpy as np
from scripts import player_data

st.set_page_config(
    page_title = "Player Analysis",
    layout = "wide"
)

st.title("Player Analysis")
st.sidebar.header("Filters")

players_df = pd.read_csv("resources/statsbomb_players.csv")
player_id = st.session_state.get("player_id")
player_name = st.session_state.get("player_name")

players = sorted(players_df["player_nickname"].fillna(players_df["player_name"]).tolist())
index = players.index(player_name) if player_name else None

player = st.sidebar.selectbox(
    "Player", players, index=index, placeholder="Select Player"
)

if player:
    player_id = player_data._player_id_from_csv(player)

seasons_df = pd.read_csv("resources/statsbomb_player_seasons.csv")
competitions_df = seasons_df[seasons_df["player_id"] == player_id]
competition = st.sidebar.selectbox("Competition", sorted(competitions_df["competition_name"].unique()), index=None,
                                   placeholder="Select Competition")

seasons = competitions_df[competitions_df["competition_name"] == competition]
season = st.sidebar.selectbox(
    "Season", sorted(seasons["season_name"].unique()), index=None, placeholder="Select Season"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Goals", 20)
col2.metric("Assists", 10)
col3.metric("xG", 23.4)
col4.metric("Rating", 6.7)

st.divider()

st.subheader("Last 5 Matches")

ratings = pd.DataFrame({
    "Match": np.arange(1, 6),
    "Rating": np.random.normal(5, 1.5, 5)
})

st.line_chart(ratings.set_index("Match"))

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Attack")

    stats = pd.DataFrame({
        "Metric": [
            "Shots/90",
            "Goals/90",
            "xG/90",
            "Key Passes",
            "Dribbles"
        ],
        "Value": [2.3, 0.54, 0.66, 2.3, 1.9]
    })

    st.dataframe(stats, width="stretch")

with right:
    st.subheader("Defense")

    stats = pd.DataFrame({
        "Metric": [
            "Tackles",
            "Interceptions",
            "Recoveries",
            "Duels Won",
            "Pressures"
        ],
        "Value": [1.2, 3.4, 5.0, 2.3, 10.5]
    })

    st.dataframe(stats, width="stretch")

st.divider()

st.subheader("Recent Matches")

matches = pd.DataFrame({
    "Opponent": ["Chelsea", "Arsenal", "Liverpool", "Villa", "Spurs"],
    "Rating": [8.3, 7.9, 6.8, 8.7, 7.5],
    "Goals": [1, 2, 0, 1, 0],
    "Assists": [0, 1, 0, 0, 2]
})

st.dataframe(matches, width="stretch")