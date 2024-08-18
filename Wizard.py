import streamlit as st
from utils.functions import *

if "data" not in st.session_state:
    st.session_state["data"] = load_players()
    st.session_state["roster"] = dict()
    st.session_state["draft_begun"] = False

def begin_draft():
    positions = st.session_state.roster.keys()
    df = st.session_state.data.copy()
    df = df[df.position.isin(positions)].copy()
    st.session_state["draft"] = Draft(st.session_state.player_num, df, st.session_state.roster)
    for position in positions:
        if position == "FLEX":
            data = df[df.position.isin(["WR", "RB", "TE"])].copy()
        else:
            data = df[df.position == position].copy()
        data.sort_values("projection", inplace = True, ascending = False)
        data.insert(0, 'Rank', range(1, len(data) + 1))
        st.session_state[position] = data.copy()        
        create_newpage(position)   
    num_players = st.session_state.player_num
    half_players = num_players / 2
    df["avg"] = df.groupby("position", group_keys = False).projection.apply(lambda x: x.rolling(window = 5).mean())    
    st.session_state.data["differential"] = st.session_state.data.groupby("position").projection.apply(lambda x: x.shift(-half_players).rolling(window=half_players).mean()
    st.session_state["draft_order"] = [i for i in range(1, num_players+1)] + [i for i in range(num_players, 0, -1)] 
    st.session_state.draft_begun = True

st.title("NFL Draft Wizard")
if not st.session_state.draft_begun:
    st.number_input("How many teams in your draft?", min_value = 1, key = "player_num")
    st.number_input("What number are you?", min_value = 1, key = "your_num")
    position_choices = st.multiselect("What positions are on the roster?", options = ["QB", "RB", "WR", "TE", "FLEX", "K", "DST"])
    for choice in position_choices:
        position_number = st.number_input(choice, min_value = 1)
        st.session_state.roster[choice] = position_number
    st.button("Enter Draft!", on_click = begin_draft)

else:
    for i in range(st.session_state.player_num):
        st.session_state[f"Team_{i+1}"] = Team(i+1)
    up = st.session_state.draft_order[0]
    on_deck = st.session_state.draft_order[1]
    if up == st.session_state.your_num:
        st.header("Your pick!")
    else:
        st.header(f"Team {up} is up")
    if on_deck == st.session_state.your_num:
        st.header("Your pick next!")
    else:
        st.header(f"Team {on_deck} is up next")


    #Put where it needs to go:
    # st.session_state.draft_order.append(st.session_state.draft.next_picks.pop(0))

    
