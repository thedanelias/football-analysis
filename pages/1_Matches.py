import streamlit as st

st.set_page_config(
    page_title = "Football Analytics",
    page_icon="@",
    layout="wide"
)

st.title("Match Analysis")
st.sidebar.header("Matches")

match_id = st.session_state.get("match_id")

competition = st.sidebar.selectbox(
    "Competition",
    ["Premier League", "La Liga", "Champions League"]
)

season = st.sidebar.selectbox(
    "Season",
    ["2020/21", "2019/20", "2018/19"]
)

match = st.sidebar.selectbox(
    "Match",
    ["Select a match..."]
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Possession", ".")

with col2:
    st.metric("Shots", ".")

with col3:
    st.metric("xG", ".")

with col4:
    st.metric("Pass Accuracy", ".")

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Pitch Visualisation")
    st.container(height=500)

with right:
    st.subheader("Player Stats")
    st.dataframe(
        {
            "Player": [],
            "Team": [],
            "Passes": [],
            "Shots": [],
            "xG": [],
            "Rating": []
        },
        width="stretch"
    )

st.divider()

bottom_left, bottom_right = st.columns(2)

with bottom_left:
    st.subheader("Shot Timeline")
    st.container(height=300)

with bottom_right:
    st.subheader("Passing Network")
    st.container(height=300)