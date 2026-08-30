import pandas as pd
import streamlit as st
from scripts import player_data

st.set_page_config(
    page_title = "Football Analytics",
    page_icon="@",
    layout="wide"
)

st.title("Football Analytics")

match, team, player = st.columns(3)

with match:
    st.subheader("Matches")

    matches_df = pd.read_csv("resources/statsbomb_matches.csv")
    competitions = sorted(matches_df["competition_name"].unique())

    competition = st.selectbox(
        "Competition", competitions, index=None, placeholder="Select a Competition")

    team_df = matches_df

    if competition:
        team_df = matches_df[matches_df["competition_name"] == competition]

    team_name = st.selectbox(
        "Team", team_df["home_team_name"].unique(), index=None, placeholder="Select a Team"
    )
    away_team_df = matches_df

    if team_name:
        away_team_df = team_df[team_df["home_team_name"] == team_name]

    away_team_name = st.selectbox(
        "Opposition", away_team_df["away_team_name"].unique(), index=None, placeholder="Select an Away Team"
    )

    seasons_df = matches_df

    if away_team_name:
        seasons_df = away_team_df[away_team_df["away_team_name"] == away_team_name]
    season = st.selectbox(
        "Season", seasons_df["season_name"].unique(), index=None, placeholder="Select a Season"
    )

    match_id = seasons_df[seasons_df["season_name"] == season]["match_id"]
    if st.button("Open Match"):
        st.session_state["match_id"] = match_id
        st.switch_page("pages/1_Matches.py")

with team:
    st.subheader("Teams")

    teams_df = pd.read_csv("resources/statsbomb_teams.csv")
    teams = sorted(teams_df["team_name"].tolist())

    team_search = st.selectbox("Team:", teams, index=None, placeholder="Search for a team")

    if team_search:
        st.session_state["team_name"] = team_search
        st.switch_page("pages/3_Teams.py")


with player:
    st.subheader("Players")

    players_df = pd.read_csv("resources/statsbomb_players.csv")
    players = sorted(players_df["player_nickname"].fillna(players_df["player_name"]).tolist())

    player_search = st.selectbox("Player:", players, index=None, placeholder="Search for a player")

    if player_search:
        st.session_state["player_id"] = player_data._player_id_from_csv(player_search)
        st.session_state["player_name"] = player_search
        st.switch_page("pages/2_Players.py")

st.divider()

st.subheader("Recent Matches")

st.divider()

st.subheader("Statistics Summary")