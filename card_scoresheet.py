import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Card Game Scoresheet", layout="wide")

st.title("🃏 Card Game Scoresheet (4 Players)")

# ---------- Helpers ----------
def recalc(df: pd.DataFrame, players: list[str]) -> pd.DataFrame:
    """Add totals & ranks based on lowest total."""
    if df.empty:
        out = pd.DataFrame(columns=["Round"] + players)
        return out

    df2 = df.copy()
    # Ensure numeric
    for p in players:
        df2[p] = pd.to_numeric(df2[p], errors="coerce").fillna(0).astype(int)

    df2["Round"] = range(1, len(df2) + 1)
    return df2[["Round"] + players]

def totals_and_ranks(df: pd.DataFrame, players: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        totals = pd.Series({p: 0 for p in players}, name="Total")
    else:
        totals = df[players].sum()

    totals_df = pd.DataFrame({"Player": totals.index, "Total": totals.values})
    totals_df = totals_df.sort_values("Total", ascending=True).reset_index(drop=True)
    totals_df["Rank"] = range(1, len(players) + 1)

    # Leaderboard view
    leaderboard = totals_df[["Rank", "Player", "Total"]]
    return totals_df, leaderboard

def df_to_csv_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ---------- State ----------
if "rounds" not in st.session_state:
    st.session_state.rounds = []  # list[dict]

# ---------- Setup ----------
with st.sidebar:
    st.header("⚙️ Setup")

    p1 = st.text_input("Player 1", value="Player 1")
    p2 = st.text_input("Player 2", value="Player 2")
    p3 = st.text_input("Player 3", value="Player 3")
    p4 = st.text_input("Player 4", value="Player 4")
    players = [p1.strip() or "Player 1", p2.strip() or "Player 2", p3.strip() or "Player 3", p4.strip() or "Player 4"]

    st.divider()

    if st.button("🧹 Reset game (clear all rounds)", type="secondary"):
        st.session_state.rounds = []
        st.rerun()

    st.caption("Rules: Everyone enters a score each round. Lowest total wins ✅")

# ---------- Add round ----------
st.subheader("➕ Add a round")

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.2])

with c1:
    s1 = st.number_input(players[0], min_value=0, step=1, value=0, key="s1")
with c2:
    s2 = st.number_input(players[1], min_value=0, step=1, value=0, key="s2")
with c3:
    s3 = st.number_input(players[2], min_value=0, step=1, value=0, key="s3")
with c4:
    s4 = st.number_input(players[3], min_value=0, step=1, value=0, key="s4")

with c5:
    if st.button("✅ Add round", type="primary"):
        st.session_state.rounds.append({players[0]: int(s1), players[1]: int(s2), players[2]: int(s3), players[3]: int(s4)})
        # Reset inputs to 0 for fast entry
        st.session_state.s1 = 0
        st.session_state.s2 = 0
        st.session_state.s3 = 0
        st.session_state.s4 = 0
        st.rerun()

# ---------- Table ----------
raw_df = pd.DataFrame(st.session_state.rounds)
df = recalc(raw_df, players)

left, right = st.columns([2.2, 1])

with left:
    st.subheader("📋 Scoresheet")
    if df.empty:
        st.info("No rounds yet. Add the first round above.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Edit last round quickly
        st.caption("Tip: If you entered a round wrong, delete it below and re-add it.")
        del_col1, del_col2 = st.columns([1, 6])
        with del_col1:
            if st.button("🗑️ Delete last round"):
                if st.session_state.rounds:
                    st.session_state.rounds.pop()
                    st.rerun()

with right:
    st.subheader("🏆 Leaderboard (lowest total)")
    totals_df, leaderboard = totals_and_ranks(df, players)
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

    st.metric("Rounds played", value=len(df))

    if not df.empty:
        winner = leaderboard.iloc[0]["Player"]
        st.success(f"Current leader: **{winner}** ✅")

# ---------- Export ----------
st.divider()
st.subheader("⬇️ Export")

if df.empty:
    st.caption("Export becomes available after you add at least 1 round.")
else:
    st.download_button(
        label="Download CSV",
        data=df_to_csv_download(df),
        file_name="card_game_scoresheet.csv",
        mime="text/csv",
    )

# ---------- Optional import ----------
with st.expander("📥 Import from CSV (optional)"):
    st.caption("If you previously exported a CSV, you can paste it here to restore the game.")
    txt = st.text_area("Paste CSV content", height=150)
    if st.button("Import CSV"):
        try:
            imported = pd.read_csv(StringIO(txt))
            # Expect columns: Round + players, but we only need player columns
            # Rebuild rounds list
            rounds = []
            for _, row in imported.iterrows():
                r = {players[i]: int(row.get(players[i], 0)) for i in range(4)}
                rounds.append(r)
            st.session_state.rounds = rounds
            st.success("Imported ✅")
            st.rerun()
        except Exception as e:
            st.error(f"Could not import. Error: {e}")
