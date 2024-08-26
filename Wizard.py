import streamlit as st
from utils.functions import *

if "data" not in st.session_state:
    st.session_state["data"] = load_players()
    st.session_state["roster"] = dict()
    st.session_state["draft_begun"] = False

def begin_draft():
    st.session_state["your_team"] = dict(zip([key for key in st.session_state.roster.keys()], [list() for i in st.session_state.roster]))
    num_players = st.session_state.player_num
    st.session_state["draft_order"] = [i for i in range(1, num_players+1)] + [i for i in range(num_players, 0, -1)] 
    positions = st.session_state.roster.keys()
    df = st.session_state.data.copy()
    df = df[df.position.isin(positions)].copy()
    for position in positions:
        if position == "FLEX":
            data = df[df.position.isin(["WR", "RB", "TE"])].copy()
        else:
            data = df[df.position == position].copy()
        data.sort_values("projection", inplace = True, ascending = False)
        data.insert(0, 'Rank', range(1, len(data) + 1))
        first_index = st.session_state.draft_order.index(st.session_state.your_num)
        # The following won't work if you are first or last in the snake draft
        second_index = st.session_state.draft_order.index(st.session_state.your_num, first_index + 1)
        print(second_index)
        num_at_risk = round(second_index / 2)
        data["likely_picked"] = [1]*num_at_risk + [0]*(len(data) - num_at_risk)      
        st.session_state[position] = data.copy()        
    st.session_state.draft_begun = True

def enact_pick():
    if st.session_state.draft_order[0] == st.session_state.your_num:
        position_taken = st.session_state.data.loc[st.session_state.data.Player == st.session_state.pick, "position"].values[0]
        st.session_state["your_team"][position_taken].append(st.session_state.pick)
    st.session_state.draft_order.append(st.session_state.draft_order.pop(0))
    st.session_state.data.loc[st.session_state.data.Player == st.session_state.pick, "picked"] = 1
    for position in st.session_state.roster.keys():
        st.session_state[position] = st.session_state[position][st.session_state[position].Player != st.session_state.pick].copy()
        first_index = st.session_state.draft_order.index(st.session_state.your_num)
        # The following won't work if you are first or last in the snake draft
        second_index = st.session_state.draft_order.index(st.session_state.your_num, first_index + 1)
        num_at_risk = round(second_index / 2)      
        st.session_state[position]["likely_picked"] = [1]*num_at_risk + [0]*(len(st.session_state[position]) - num_at_risk)


st.title("NFL Draft Wizard")
if not st.session_state.draft_begun:
    player_num = st.number_input("How many teams in your draft?", min_value = 1)
    your_num = st.number_input("What number are you?", min_value = 1)
    st.session_state["player_num"] = player_num
    st.session_state["your_num"] = your_num
    position_choices = st.multiselect("What positions are on the roster?", options = ["QB", "RB", "WR", "TE", "FLEX", "K", "DST"])
    for choice in position_choices:
        position_number = st.number_input(choice, min_value = 1)
        st.session_state.roster[choice] = position_number
    st.button("Enter Draft!", on_click = begin_draft)

else:
    up = st.session_state.draft_order[0]
    on_deck = st.session_state.draft_order[1]
    up_next = ""
    if up == st.session_state.your_num:
        up_next += "Your pick!"
    else:
        up_next += f"Team {up} is up."
    if on_deck == st.session_state.your_num:
        up_next += " Your pick next!"
    else:
        up_next += f" Team {on_deck} is up next"
    st.header(up_next)
    st.write("Draft Order")
    st.write(" | ".join(map(str, st.session_state.draft_order)))
    st.header("Recommended Pick")
    how_to_choose = dict()
    best_player = dict()    
    for position in st.session_state.roster.keys():
        _max = st.session_state[position].projection.max()
        best_player[position] = st.session_state[position].loc[st.session_state[position].projection == _max, "Player"].values[0]
        next_max = st.session_state[position][st.session_state[position].likely_picked == 0].projection.max()
        diff = _max - next_max
        if len(st.session_state.your_team[position]) >= st.session_state.roster[position]:
            diff *= -1
        how_to_choose[position] = diff
    recommended_pick = best_player[max(how_to_choose, key = how_to_choose.get)]
    st.dataframe(st.session_state.data[st.session_state.data.Player == recommended_pick], hide_index = True)
    st.selectbox(f"Team {up} picks", options = st.session_state.data.loc[st.session_state.data.picked == 0, "Player"], key = "pick", index = None)
    st.button("Enact Pick!", on_click = enact_pick)
    for position in st.session_state.roster.keys():
        st.header(position)
        st.write("Best Pick")
        st.dataframe(st.session_state[position].loc[st.session_state[position].Player == best_player[position]], hide_index = True)
        st.write("Difference between this guy and the next to likely be available:")
        st.write(round(how_to_choose[position], 2))
        st.dataframe(st.session_state[position], hide_index = True)
    st.header("Your Team")
    st.write(st.session_state.your_team)





    
