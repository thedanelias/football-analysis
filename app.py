import streamlit as st

st.set_page_config(
    page_title = "Football Analytics",
    page_icon="@",
    layout="wide"
)

st.title("Football Analytics")

match, team, player = st.columns(3)

with match:
    st.subheader("Matches")

    st.selectbox(
        "Country",
        ["England", "Spain"]
    )

    st.selectbox(
        "Competition",
        ["Premier League", "Championship", "League 1", "League 2"]
    )

    st.selectbox(
        "Home Team",
        ["Arsenal", "Chelsea", "Tottenham"]
    )

    st.selectbox(
        "Away Team",
        ["Arsenal", "Chelsea", "Tottenham"]
    )

    st.selectbox(
        "Season",
        ["2024/25", "2025/26"]
    )

    st.button("Open Match")

with team:
    st.subheader("Teams")

    team_search = st.text_input("Search for a team...")

with player:
    st.subheader("Players")

    player_search = st.text_input("Search for a player...")

st.divider()

st.subheader("Recent Matches")

st.divider()

st.subheader("Statistics Summary")