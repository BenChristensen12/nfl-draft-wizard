import streamlit as st
from utils.functions import *

if "data" not in st.session_state:
    st.session_state["data"] = load_players()
    st.session_state["position_counts"] = dict()
    st.session_state["positions"] = ["QB", "RB", "WR", "TE", "K", "DST"]
    st.session_state["draft_begun"] = False
    st.session_state["rounds"] = 16
    st.session_state["all_picks"] = []
    st.session_state["pick_number"] = 0
    st.session_state["denominators"] = {"QB": 4, "RB": 2, "WR": 2, "TE": 4, "K": 8, "DST": 8}

def calculate_lead(pick_num, score = "projection"):
    data = st.session_state.data.sort_values([score], ascending = False)   
    df = pd.DataFrame()
    for position in st.session_state.chosen_positions:
        denominator = st.session_state.denominators[position]
        window = max(round(st.session_state.picks_between[pick_num]/denominator), 1)
        position_df = data[(data.position == position) & ~data.Pick].copy()
        position_df["lead"] = position_df[score] - position_df[score].shift(-window)
        df = pd.concat([df, position_df])
    df = data.merge(df, how = 'left', on = ["position", "Player", "Team", "low", "projection", "high"])
    return df

def begin_draft():
    st.session_state["roster"] = dict(zip(st.session_state.positions, [[] for position in st.session_state.positions]))
    num_players = st.session_state.num_players
    st.session_state["draft_order"] = int(st.session_state.rounds/2) * ([i for i in range(1, num_players+1)] + [i for i in range(num_players, 0, -1)])
    i, n = st.session_state.your_num, st.session_state.num_players
    repeats = int(st.session_state.rounds / 2)
    st.session_state["your_pick_order"] = sorted([2*k*n + i for k in range(repeats)] + [2*k*n + 2*n + 1-i for k in range(repeats)])
    st.session_state["picks_between"] = st.session_state.rounds * [2*(num_players-i) if i < num_players else 2*(num_players-1) for i in range(1, num_players+1)]       
    st.session_state["draft_begun"] = True


st.title("NFL Draft Wizard")
if not st.session_state.draft_begun:
    st.session_state["num_players"] = st.number_input("How many teams in your draft?", min_value = 1)
    st.session_state["your_num"] = st.number_input("What number are you in the draft?", min_value = 1)

    chosen_positions = st.multiselect("What positions are on the roster?", options = st.session_state.positions)
    st.session_state["chosen_positions"] = chosen_positions
    st.button("Enter Draft!", on_click = begin_draft)

else:
    if st.session_state.pick_number+1 == st.session_state.your_num:
        st.header("Round y | It is your pick!")
    else:
        st.header(f"Round y | x picks to go")
    score = st.selectbox("Select Score to Optimize", options = ["low", "projection", "high"], index = 1)
    st.subheader("Recommended Pick")
    df = calculate_lead(st.session_state.pick_number, score)
    agg_dict ={"Player": "first", "lead": "first", score: "first"}
    highest_lead = df.groupby("position", as_index = False).agg(agg_dict).sort_values("lead", ascending = False)
    highest_pts = df.groupby("position", as_index = False).agg(agg_dict).sort_values([score], ascending = False)
    highest_lead = highest_lead[["position", "Player", score, "lead"]].round().copy()
    st.dataframe(highest_lead, hide_index = True)    
    positions = st.session_state.chosen_positions    
    tabs = st.tabs(["All"] + positions)
    picked = set()
    for i, tab in enumerate(tabs):
        with tab:
            if i > 0:
                position = positions[i-1]
                data_df = df.loc[df.position == position, ["Pick", "Player", "low", "projection", "high", "lead"]].sort_values(score, ascending = False).round()
            else:
                data_df = df[["Pick", "position", "Player", "low", "projection", "high", "lead"]].sort_values(score, ascending = False).round()
            edited_df = st.data_editor(data_df, disabled = ["position", "Player", "low", "projection", "high", "lead"], hide_index = True)
            picked.update(edited_df.loc[df.Pick, "Player"].values)
    picked = list(picked)
    st.session_state.data.Pick = 0
    st.session_state.data.loc[st.session_state.data.Player.isin(picked), "Pick"] = 1


st.session_state



    
# For each position, don't hide any players, just have the checkbox mean the player has been picked
# On recommendation page, hide flex