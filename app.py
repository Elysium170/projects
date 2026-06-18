# snow --config-file ".streamlit/config.toml" streamlit deploy --replace --connection "snowflake_pub_PROD"

import streamlit as st

from src.world_cup_charts import *

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(layout="wide")

st.markdown("""
<style>

.result-card {
    background: white;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 4px solid #e0e0e0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    font-size: 15px;
}

.result-played {
    border-left: 4px solid #2f5d9b;
    background: #f5f8fc;
}

.result-upcoming {
    color: #999;
}

.result-header {
    font-weight: 600;
}
            
            
/* ✅ ADD THIS */
.scroll-box {
    max-height: 420px;
    overflow-y: scroll;
    padding-right: 6px;
}

/* optional: nicer scrollbar */
.scroll-box::-webkit-scrollbar {
    width: 6px;
}

.scroll-box::-webkit-scrollbar-thumb {
    background: #c4c4c4;
    border-radius: 4px;
}
            

/* ✅ Bigger select box container */
div[data-baseweb="select"] > div {
    min-height: 52px !important;
    font-size: 19px !important;
    display: flex;
    align-items: center;
}

/* ✅ Placeholder + selected text */
div[data-baseweb="select"] span {
    font-size: 19px !important;
}

</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>

/* ✅ Sidebar base (football pitch look) */
section[data-testid="stSidebar"] {
    background: linear-gradient(
        rgba(0,0,0,0.5),
        rgba(0,0,0,0.5)
    ),
    repeating-linear-gradient(
        0deg,
        #2e7d32,
        #2e7d32 40px,
        #388e3c 40px,
        #388e3c 80px
    );
    color: white;
}

don’t override everything) */}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white;
}

/* ✅ Selectbox styling */
div[data-baseweb="select"] {
    background-color: white !important;
    border-radius: 6px !important;
}

/* ✅ Button styling */
section[data-testid="stSidebar"] button {
    background-color: white !important;
    color: #2f5d9b !important;
    border-radius: 6px;
    font-weight: 600;
}

/* ✅ Optional scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-thumb {
    background: #c4c4c4;
    border-radius: 4px;
}

</style>
""", unsafe_allow_html=True)



st.markdown(
    "<h1 style='text-align:center; font-size:58px;'>⚽ Fifa World Cup Pick'em Dashboard - Come On Phoenix edition</h1>",
    unsafe_allow_html=True
)


st.markdown("<div style='height: 2.5em;'></div>", unsafe_allow_html=True)

# ----------------------------
# Load data
# ----------------------------
long_df, df = load_data()

# ✅ get players from rows 79–84 (python is 0-based)
subset_players = df.iloc[79:85]["Name"].dropna().unique()

results = load_results()
scores = calculate_scores(long_df, results)


# ----------------------------
# Sidebar
# ----------------------------

st.markdown("""
<style>
/* Remove focus outline + blinking caret */
div[data-baseweb="select"] input {
    caret-color: transparent;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="font-size:30px; font-weight:870; margin-bottom:0;">
Player Selection
</div>
""", unsafe_allow_html=True)

options = sorted(subset_players)

# ✅ initialise state
if "player_select" not in st.session_state:
    st.session_state.player_select = None

# ✅ clear button BEFORE widget renders
if st.session_state.get("clear_clicked", False):
    st.session_state.player_select = None
    st.session_state.clear_clicked = False

# ✅ selectbox
selected_person = st.sidebar.selectbox(
    "",
    options,
    index=None,
    placeholder="Select a player...",
    key="player_select"
)

# ✅ button sets flag only
if st.sidebar.button("Clear selection"):
    st.session_state.clear_clicked = True
    st.rerun()

# ✅ mini summary
total_players = len(subset_players)
total_picks = len(long_df)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="
    background-color:white;
    color:#2f5d9b;
    padding:6px;
    border-radius:6px;
    border:6px solid #e0e0e0;
    font-size:17px;
">
<b>{total_players}</b> players competing for $50
</div>
""", unsafe_allow_html=True)


# ----------------------------
# Guard: no player selected
# ----------------------------
if selected_person is None:
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #e6f4ea, #eef2f7);
        padding:28px 20px;
        border-radius:10px;
        border:1px solid #d6dde8;
        text-align:center;
        font-size:30px;
        font-weight:800;
        color:#296f2c;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    ">
        👈 Select a player to get started<br>
    </div>
    """, unsafe_allow_html=True)

    st.stop()  # ✅ stops the rest of the app from rendering


# ----------------------------
# ✅ SECTION 1: Player insights (TOP)
# ----------------------------
st.markdown("## 👤 Player Picks and Results")
st.markdown("---")

col1, col2, col3, col4 = st.columns([1, 0.05, 0.05, 1])

with col1:
    player_picks(long_df, selected_person)
    st.markdown("---")
    leaderboard_chart(scores, selected_person, subset_players)

with col4:
    results_feed(results, long_df, selected_person)


# ----------------------------
# ✅ SECTION 3: Overview
# ----------------------------
st.markdown("<div style='height: 0.2em;'></div>", unsafe_allow_html=True)
st.markdown("## 🏆 Competition Insights")
st.markdown("---")

col3, col4 = st.columns([1, 1])

with col3:
    similarity_chart(long_df, selected_person, subset_players)

with col4:
    nz_chart(long_df)

st.markdown("---")

col5, col6 = st.columns([1, 1])

with col5:
    team_popularity_chart(long_df)

with col6:
    picks_per_person_chart(long_df)
