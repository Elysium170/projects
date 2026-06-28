import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import numpy as np
import streamlit as st

PRIMARY = "#286f2c"
GREY = "#D2BBBB"

# ----------------------------
# Helpers
# ----------------------------
def white_box(content):
    return f"""
    <div style="background-color:white;padding:12px;border-radius:6px;">
        {content}
    </div>
    """

def plot_to_html(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200)
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")

    return f'<img src="data:image/png;base64,{img}" style="width:90%;"/>'

# ----------------------------
# Load + clean data
# ----------------------------
@st.cache_data
def load_data():
    
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent

    file_path = BASE_DIR / "Football_World_Cup_2026_Pick_Em_1-79.xlsx"

    df = pd.read_excel(file_path)

    # ✅ identify missing names
    mask = df["Name"].isna() | (df["Name"].str.strip() == "")

    # ✅ only modify blanks
    df.loc[mask, "Name"] = "Unnamed_" + df.index[mask].astype(str)

    df.columns = (
        df.columns
        .str.replace('\xa0', ' ', regex=False)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )

    team_columns = [
        "$10 - Favourites",
        "$9 - Giants",
        "$8 - Heavy Hitters",
        "$6 - Danger Teams",
        "$4 - Rising Dark Horses",
        "$3 - Outsiders",
        "$2 - Wildcards",
        "$1 - Long Shots",
        "$0.50 - Hail Mary's"
    ]

    # ✅ reshape instead of looping
    long_df = (
        df.melt(id_vars="Name", value_vars=team_columns, value_name="Team")
        .dropna(subset=["Team"])
    )

    # ✅ split and explode
    long_df["Team"] = long_df["Team"].str.split(";")
    long_df = long_df.explode("Team")

    long_df = long_df[long_df["Team"].str.strip() != ""]

    long_df["Team"] = (
        long_df["Team"]
        .str.strip()
        .replace({
            "Sweeden": "Sweden",
            "New Zealand ": "New Zealand"
        })
    )

    return long_df, df

# ----------------------------
# Charts
# ----------------------------
def team_popularity_chart(long_df_all, subset_players):

    df = long_df_all.copy()

    filter_subset = st.checkbox("Show only Come On Phoenix players", value=False)

    
    if filter_subset:
        df = df[df["Name"].isin(subset_players)]

    # --- All possible teams ---
    all_teams = {
        "England", "Spain", "France",
        "Brazil", "Argentina", "Portugal", "Germany",
        "Netherlands", "Belgium", "Norway", "Colombia",
        "Uruguay", "Mexico", "USA", "Japan", "Morocco",
        "Switzerland", "Croatia", "Ecuador", "Turkey", "Senegal", "Sweden",
        "Scotland", "Austria", "Canada", "Bosnia", "Paraguay", "Egypt", "Algeria", "Ghana", "Czech Republic", "Ivory Coast",
        "Australia", "South Africa", "Iran", "South Korea", "Saudi Arabia", "Tunisia",
        "Panama", "Cape Verde", "Uzbekistan", "DR Congo",
        "New Zealand", "Qatar", "Haiti", "Jordan", "Iraq", "Curacao"
    }

    # --- Player → unique teams ---
    players = df.groupby("Name")["Team"].apply(set)

    team_counts = (
        players.explode()
        .value_counts()
    )

    # --- % of players picking each team ---
    data = (
        (team_counts / len(players) * 100)
        .round()
        .astype(int)
        .sort_values()
    )

    # --- Key teams ---
    # Sort descending once
    sorted_data = data.sort_values(ascending=False)

    # Top value
    top_value = sorted_data.iloc[0]

    # All teams tied for top
    top_teams = sorted_data[sorted_data == top_value].index.tolist()

    # Next value (strictly less than top)
    remaining = sorted_data[sorted_data < top_value]

    second_teams = []
    if not remaining.empty:
        second_value = remaining.iloc[0]
        second_teams = remaining[remaining == second_value].index.tolist()

    # --- Teams with no picks ---
    picked_teams = set(team_counts.index)
    no_picks = sorted(all_teams - picked_teams)

    # --- Colours ---
    colours = [PRIMARY if t in top_teams else GREY for t in data.index]

    # --- Dynamic height (same as leaderboard) ---
    height_per_team = 0.3
    fig_height = max(4, len(data) * height_per_team)

    fig, ax = plt.subplots(figsize=(6.5, fig_height))
    sns.barplot(x=data.values, y=data.index, palette=colours)

    ax.invert_yaxis()

    for i, v in enumerate(data.values):
        ax.text(v + 0.5, i, f"{v}%", va="center", fontsize=10)

    ax.set(xlabel=None, ylabel=None)
    ax.set_xlim(0, max(data.values) + 5)

    ax.grid(False)
    sns.despine(left=True, bottom=True)
    plt.xticks([])
    plt.tight_layout()

    small_group = filter_subset  # only triggers for Phoenix players

    def format_list(items):
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return ", ".join(items[:-1]) + f", and {items[-1]}"

    parts = []

    # --- Commentary ---
    if not small_group:
        top_text = format_list(top_teams)

        second_text = ""
        if second_teams:
            second_text = f", followed by <b>{format_list(second_teams)}</b>"

        # ✅ add top text
        parts.append(
            f"<p>After including players from a work league comp as well, <b>{top_text}</b> had the most backers{second_text}.</p>"
        )

        # ✅ add no picks text if needed
        if no_picks:
            parts.append(
                f"<p>There were sadly no picks for {' and '.join(no_picks)}. Can they outperform expectations?</p>"
            )

    # --- Chart ---
    chart_html = plot_to_html(fig)

    scroll_box = f"""
    <div style="
        max-height: 350px;
        overflow-y: scroll;
        padding-right: 10px;
        position: relative;
    ">
        {chart_html}

        <div style="
            position: sticky;
            bottom: 0;
            height: 30px;
            background: linear-gradient(transparent, white);
        "></div>
    </div>
    """

    parts.append(scroll_box)

    # --- Title ---
    title = "Most backed teams (Come On Phoenix)" if filter_subset else "Most backed teams (All players)"

    # --- Final HTML ---
    html = f"""
    <h2>{title}</h2>
    {"".join(parts)}
    """
    st.markdown(white_box(html), unsafe_allow_html=True)


def nz_chart(long_df):

    # ✅ calculate at player level
    players = long_df.groupby("Name")["Team"].apply(list)

    nz_count = players.apply(lambda x: "New Zealand" in x).sum()
    total = len(players)
    non_nz = total - nz_count

    pct_nz = int(round(nz_count / total * 100))
    pct_other = int(100 - pct_nz)

    # ✅ updated labels + order (NZ first)
    data = pd.Series({
        "Selected NZ": pct_nz,
        "Less confident in NZ": pct_other
    })

    colours = [PRIMARY, GREY]

    fig, ax = plt.subplots(figsize=(5, 2.8))

    sns.barplot(x=data.values, y=data.index, palette=colours)

    # ✅ annotate percentages
    for i, v in enumerate(data.values):
        ax.text(v + 1, i, f"{v}%", va="center", fontsize=10)

    ax.set(xlabel=None, ylabel=None)
    ax.set_xlim(0, 100)

    ax.grid(False)
    sns.despine(left=True, bottom=True)
    plt.xticks([])

    plt.tight_layout()

    html = f"""
    <h2>Percent that selected New Zealand</h2>
    <p><b>{pct_nz}%</b> of players selected NZ.</p>
    {plot_to_html(fig)}
    """

    st.markdown(white_box(html), unsafe_allow_html=True)


def player_picks(long_df, name):

    teams = long_df[long_df["Name"] == name]["Team"].tolist()
    count = len(teams)

    avg = round(long_df.groupby("Name").size().mean())

    if count > avg:
        extra = f"<b>Sees promise in the underdogs</b> to sneak some wins, going for quantity over quality ({count} teams chosen vs average of {avg})."
    elif count < avg:
        extra = f"<b>Favours the bigger teams</b>, going for a quality over quantity approach ({count} teams picked vs average of {avg})."
    else:
        extra = f"Picked {count} teams, on par with the average."

    # add small insights
    nz_picked = "New Zealand" in teams

    if nz_picked:
        nz_text = "Most importantly has <b>faith / blind hope in the New Zealanders</b> with Wood and Elijah looking like prime Kane and Son."
    else:
        nz_text = "Opted against New Zealand, craaaaazy."

    # chips
    chips = " ".join([
        f'<span style="background:#e6f4ea; color:#1b5e20; padding:8px 14px; border-radius:14px; margin:4px; font-size:20px; display:inline-block;">{t}</span>'
        for t in teams
    ])


    html = f"""
    <h2>{name} is backing:</h2>
    <div>{chips}</div><br>
    <p>{extra} <br><br> {nz_text}</p>
    """

    st.markdown(white_box(html), unsafe_allow_html=True)


def picks_per_person_chart(long_df):
    data = long_df.groupby("Name").size().sort_values(ascending=False).head(12)

    # Get top 2 names
    top_2 = data.index[:2]

    # Apply colours
    colours = [PRIMARY if n in top_2 else GREY for n in data.index]

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=data.values, y=data.index, palette=colours)

    for i, v in enumerate(data.values):
        ax.text(v + 0.2, i, str(v), va='center', fontsize=10)

    ax.set(xlabel=None, ylabel=None)
    ax.grid(False)
    sns.despine(left=True, bottom=True)
    plt.xticks([])
    plt.tight_layout()

    avg = round(long_df.groupby("Name").size().mean(), 1)

    html = f"""
    <h2>Picks per player</h2>
    <p>Average picks across Come on Phoenix: <b>{avg}</b></p>
    {plot_to_html(fig)}
    """
    st.markdown(white_box(html), unsafe_allow_html=True)


def similarity_chart(long_df, selected, subset_players):

    # ✅ filter to subset players
    long_df = long_df[long_df["Name"].isin(subset_players)]

    base = set(long_df[long_df["Name"] == selected]["Team"])

    rows = []
    overlap_map = {}  # stores shared teams

    # ----------------------------
    # ✅ Build overlap data
    # ----------------------------
    for name, g in long_df.groupby("Name"):
        if name == selected:
            continue

        teams = set(g["Team"])
        shared = base & teams

        rows.append({
            "Name": name,
            "Overlap": len(shared)
        })

        overlap_map[name] = shared  # store actual teams

    df = (
        pd.DataFrame(rows)
        .sort_values(["Overlap", "Name"], ascending=[False, True])
        .head(10)
    )

    if df.empty:
        return

    colours = [PRIMARY] + [GREY] * (len(df) - 1)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.invert_yaxis()

    bars = ax.barh(
        df["Name"],
        df["Overlap"],
        color=colours
    )

    ax.bar_label(
        bars,
        labels=df["Overlap"],
        padding=5,
        fontsize=10
    )

    ax.set(xlabel=None, ylabel=None)
    ax.grid(False)
    sns.despine(left=True, bottom=True)
    plt.xticks([])
    plt.tight_layout()

    # ----------------------------
    # ✅ Insight logic
    # ----------------------------
    top_name = df.iloc[0]["Name"]
    top_overlap = df.iloc[0]["Overlap"]
    total_selected = len(base)

    pct_overlap = int(round((top_overlap / total_selected) * 100)) if total_selected > 0 else 0

    shared_teams = overlap_map[top_name]

    # ✅ only show team list if not identical
    team_text = ""
    if top_overlap != total_selected:
        shared_list = ", ".join(sorted(shared_teams))

        # optional cap to avoid long text
        if len(shared_teams) > 5:
            shared_list = ", ".join(sorted(list(shared_teams))[:5]) + "..."

        team_text = f"""
        <b>They agreed on:</b> {shared_list}
        """

    # ----------------------------
    # ✅ Output
    # ----------------------------
    html = f"""
    <h2>Who’s on the same wavelength?</h2>
    <p>
    <b>{top_name}</b> thought most similarly to <b>{selected}</b>, 
    with <b>{top_overlap}</b> shared picks out of <b>{total_selected}</b>.
    </p>
    <p>{team_text}</p>
    {plot_to_html(fig)}
    """

    st.markdown(white_box(html), unsafe_allow_html=True)


# ----------------------------
# Scores
# ----------------------------
@st.cache_data
def load_results():
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent

    file_path = BASE_DIR / "results.xlsx"

    return pd.read_excel(file_path)


@st.cache_data
def calculate_scores(long_df, results):

    rows = []

    for _, r in results.iterrows():

        is_final = r.get("Is_Final", False)

        result = r["Result"]

        # Skip unplayed matches
        if pd.isna(result):
            continue

        # ✅ Parse score (assumes format "24-18")
        try:
            score_a, score_b = map(int, result.split("-"))
        except:
            continue  # skip bad format

        # ✅ Determine outcome
        if score_a == score_b:
            teams = [
                (r["Team_A"], 5),
                (r["Team_B"], 5)
            ]
        else:
            if score_a > score_b:
                winner = r["Team_A"]
                loser = r["Team_B"]
            else:
                winner = r["Team_B"]
                loser = r["Team_A"]

            teams = [
                (winner, 10),
                (loser, 0)
            ]

        for team, base_points in teams:

            bonus = 0

            if is_final:
                if base_points == 10:
                    bonus = 35   # winner bonus
                else:
                    bonus = 10   # loser bonus

            rows.append({
                "Team": team,
                "Points": base_points + bonus
            })

    results_expanded = pd.DataFrame(rows)


    # ✅ FIX: left join to keep all picks
    merged = long_df.merge(results_expanded, on="Team", how="left")

    # ✅ fill missing scores with 0
    merged["Points"] = merged["Points"].fillna(0)


    scores = (
        merged.groupby("Name")["Points"]
        .sum()
        .reset_index()
    )

    return scores


def results_feed(results, long_df, selected_person):

    st.markdown("### World Cup Matches")

    if results is None or results.empty:
        st.markdown("No matches yet")
        return

    # ----------------------------
    # ✅ FILTER UI (inside function)
    # ----------------------------
    filter_on = st.checkbox(f"Click to only show {selected_person}'s teams")

    # ✅ Get selected player's teams
    player_teams = set()

    if filter_on:
        player_teams = set(
            long_df[long_df["Name"] == selected_person]["Team"]
        )

    # ----------------------------
    # ✅ Sort results
    # ----------------------------
    results = results.sort_values("Match_ID", ascending=True).reset_index(drop=True)

    # ✅ Find next unplayed match
    next_idx = None
    mask_unplayed = results["Result"].isna() | (results["Result"] == "")
    if mask_unplayed.any():
        next_idx = mask_unplayed.idxmax()

    # ----------------------------
    # ✅ Session state
    # ----------------------------
    if "jump_to_next" not in st.session_state:
        st.session_state.jump_to_next = False

    # ----------------------------
    # ✅ Buttons
    # ----------------------------
    col1, col2, col3 = st.columns([1, 1, 1.5])

    with col1:
        if st.button("⬇ Jump to next match"):
            st.session_state.jump_to_next = True

    if st.session_state.jump_to_next:
        with col2:
            if st.button("🔼 Show from start"):
                st.session_state.jump_to_next = False

    # ✅ Decide starting index
    start_idx = 0
    if st.session_state.jump_to_next and next_idx is not None:
        start_idx = max(next_idx - 3, 0)

    # ----------------------------
    # ✅ Scroll container
    # ----------------------------
    with st.container(height=546):

        visible_count = 0  # ✅ track how many rows shown

        # ---------- MAIN ----------
        for idx in range(start_idx, len(results)):
            r = results.iloc[idx]

            if pd.isna(r["Team_A"]) or pd.isna(r["Team_B"]):
                continue

            # ✅ Apply filter
            if filter_on:
                if (r["Team_A"] not in player_teams) and (r["Team_B"] not in player_teams):
                    continue

            visible_count += 1

            matchup = f"{r['Team_A']} vs {r['Team_B']}"

            if pd.isna(r["Result"]):
                outcome = f"{r['Date']}"
                css_class = "result-card result-upcoming"

            else:
                try:
                    score_a, score_b = map(int, str(r["Result"]).strip().split("-"))

                    if score_a == score_b:
                        outcome = f"{r['Result']} draw 🤝"
                    else:
                        if score_a > score_b:
                            winner = r["Team_A"]
                        else:
                            winner = r["Team_B"]

                        outcome = f"{winner} {r['Result']}"

                except:
                    outcome = f"{r['Result']}"

                css_class = "result-card result-played"

            if idx == next_idx:
                css_class += " highlight-next"

            st.markdown(f"""
            <div class="{css_class}">
                <div class="result-header">{matchup}</div>
                <div>{outcome}</div>
            </div>
            """, unsafe_allow_html=True)

        # ---------- EARLIER ----------
        if start_idx > 0:
            st.markdown("### ⬆ Earlier matches")

            for idx in range(0, start_idx):
                r = results.iloc[idx]

                if pd.isna(r["Team_A"]) or pd.isna(r["Team_B"]):
                    continue

                # ✅ Apply filter
                if filter_on:
                    if (r["Team_A"] not in player_teams) and (r["Team_B"] not in player_teams):
                        continue

                visible_count += 1

                matchup = f"{r['Team_A']} vs {r['Team_B']}"

                if pd.isna(r["Result"]):
                    outcome = "Not played yet"
                    css_class = "result-card result-upcoming"
                elif not pd.isna(r["Result"]):
                    try:
                        score_a, score_b = map(int, r["Result"].split("-"))

                        if score_a == score_b:
                            outcome = f"{r['Result']} draw 🤝"
                        else:
                            # ✅ figure out winner
                            if score_a > score_b:
                                winner = r["Team_A"]
                            else:
                                winner = r["Team_B"]

                            outcome = f"{r['Result']} {winner}"


                    except:
                        outcome = f"{r['Result']}"

                    css_class = "result-card result-played"

                st.markdown(f"""
                <div class="{css_class}">
                    <div class="result-header">{matchup}</div>
                    <div>{outcome}</div>
                </div>
                """, unsafe_allow_html=True)

        # ----------------------------
        # ✅ Empty state
        # ----------------------------
        if visible_count == 0:
            if filter_on:
                st.info(f"No matches found for {selected_person}'s teams")
            else:
                st.info("No matches to display")


def leaderboard_chart(scores, selected_person, subset_players):
    if scores is None:
        return
    
    scores = scores[scores["Name"].isin(subset_players)]

    # Aggregate scores (ALL players now, not just top 12)
    data = (
        scores.groupby("Name", as_index=False)["Points"]
        .sum()
        .sort_values(by=["Points", "Name"], ascending=[False, True])
        .set_index("Name")["Points"]
    )

    top_score = data.iloc[0]
    leaders = data[data == top_score].index.tolist()
    n_leaders = len(leaders)

    second_score = data.iloc[1] if len(data) > 1 else None

    # Dynamic height (so bars don’t squash)
    height_per_player = 0.3
    max_height = 12  # ✅ cap it

    fig_height = min(max_height, max(4, len(data) * height_per_player))

    import matplotlib.cm as cm
    import matplotlib.colors as mcolors

    # Create a green gradient
    norm = mcolors.Normalize(vmin=min(data.values), vmax=max(data.values))
    cmap = cm.Greens  # built-in green palette

    colours = [cmap(norm(v)) for v in data.values]

    # Plot
    fig, ax = plt.subplots(figsize=(6, fig_height))
    sns.barplot(x=data.values, y=data.index, palette=colours)

    for i, v in enumerate(data.values):
        ax.text(v + 0.2, i, str(int(v)), va="center", fontsize=10)

    ax.set(xlabel=None, ylabel=None)
    ax.grid(False)
    sns.despine(left=True, bottom=True)
    plt.xticks([])
    plt.tight_layout()

    # --- Commentary ---
    # --- Selected person summary ---
    if selected_person in data.index:
        person_score = int(data[selected_person])

        # Competition rank (counts people ahead properly)
        sorted_scores = data.sort_values(ascending=False)

        ranks = []
        current_rank = 1

        for i, score in enumerate(sorted_scores):
            if i > 0 and score < sorted_scores.iloc[i - 1]:
                current_rank = i + 1
            ranks.append(current_rank)

        rank_series = pd.Series(ranks, index=sorted_scores.index)
        person_rank = int(rank_series[selected_person])

        # 👉 NEW: detect ties at same score
        same_score_count = (data == person_score).sum()

        # Rank suffix (1st, 2nd, 3rd...)
        def rank_suffix(n):
            if 10 <= n % 100 <= 20:
                return "th"
            return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        place_text = f"{person_rank}{rank_suffix(person_rank)}"

        # 👉 NEW: add "(equal)" if tied
        if same_score_count > 1:
            place_text += " equal"

        person_text = (
            f"<b>{selected_person}</b> is on <b>{person_score} points "
            f"in {place_text}</b> place."
        )
    else:
        person_text = ""

    if n_leaders == 1:
        if leaders[0] == selected_person:
            leader_text = ""  # already covered
        else:
            leader_text = f"<b>{leaders[0]}</b> is out in front on <b>{int(top_score)}</b> points 🎉"
    else:
        if n_leaders < 4:
            names = ", ".join(leaders[:-1]) + f" and {leaders[-1]}"
            leader_text = f"The leaders on <b>{int(top_score)}</b> points are {names} 🎉"
        elif n_leaders < 10:
            names = ", ".join(leaders[:-1]) + f" and {leaders[-1]}"
            leader_text = f"<b>The leaders on {int(top_score)} points</b> are: {names} 🎉"
        else:
            leader_text = f"There are <b>{n_leaders}</b> players tied for the lead on <b>{int(top_score)}</b> points 🎉"

    # --- Second place commentary ---
    if second_score is not None and top_score != second_score:
        second_players = data[data == second_score].index.tolist()
        n_second = len(second_players)

        if n_second == 1:
            if second_players[0] == selected_person:
                second_text = ""  # already covered
            else:
                second_text = f"<b>{second_players[0]}</b> is on their tail in second place on <b>{int(second_score)}</b> points."
        else:
            if n_second < 4:
                names = ", ".join(second_players[:-1]) + f" and {second_players[-1]}"
                second_text = f"In second place on their tail with <b>{int(second_score)}</b> points are {names}."
            elif n_second < 10:
                names = ", ".join(second_players[:-1]) + f" and {second_players[-1]}"
                second_text = f"<b>Second place on their tail with {int(second_score)} points</b> is shared by: {names}."
            else:
                second_text = f"There are <b>{n_second}</b> players tied for second on <b>{int(second_score)}</b> points."

        gap = int(top_score - second_score)
        if gap == 5:
            gap_text = "Just <b>5 points</b> in it 👀"
        elif gap <= 10:
            gap_text = f"Only <b>{gap}</b> points separate the top spot 👀"
        else:
            gap_text = f"<b>{gap}</b> points in it. The big teams are still to rack up their points for wins in the knockouts, apart from maybe England."

    else:
        second_text = ""
        gap_text = ""

    extra_text = f"""
    <p>{person_text}</p>
    <p>{leader_text}</p>
    <p>{second_text}</p>
    <p>{gap_text}</p>
    """

    # --- Scroll wrapper ---
    chart_html = plot_to_html(fig)

    scroll_box = f"""
    <div style="
        max-height: 420px;
        padding-right: 10px;
        position: relative;
    ">
        {chart_html}
        <div style="
            position: sticky;
            bottom: 0;
            height: 30px;
            background: linear-gradient(transparent, white);
        "></div>
    </div>
    """

    html = f"""
    <h2>Come on Phoenix Leaderboard</h2>
    {extra_text}
    {scroll_box}
    """

    st.markdown(white_box(html), unsafe_allow_html=True)