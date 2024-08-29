import streamlit as st
from utils.functions import *

if "data" not in st.session_state:
    st.session_state["data"] = load_players()
    st.session_state["roster"] = dict()
    st.session_state["draft_begun"] = False
    st.session_state["rounds"] = 16

def calculate_lead():
    df = st.session_state.data.copy()
    working_df = pd.DataFrame()
    for position in st.session_state.roster.keys():
        position_df = df[(df.position == position) & (df.picked == 0) & (df.likely_pick == 0)].copy()
        position_df["lead"] = position_df.projection - position_df.projection.shift(-1).rolling(window=half).mean().shift(1-half)
        working_df = pd.concat([working_df, position_df])
    st.session_state["working_df"] = working_df.copy()

def begin_draft():
    for i in range(len(st.session_state.num_players)):
        st.session_state[f"team_{i+1}_roster"] = pd.DataFrame(dict(zip(st.session_state.roster.keys(), [[] for key in st.session_state.roster.keys()])))
        st.session_state[f"team_{i+1}_likely_roster"] = pd.DataFrame(dict(zip(st.session_state.roster.keys(), [[] for key in st.session_state.roster.keys()])))
        st.session_state[f"team_{i+1}_picks"] = pd.DataFrame("round": [i for i in range(st.session_state.rounds)], "Player": [])
        st.session_state[f"team_{i+1}_likely_picks"] = pd.DataFrame("round": [i for i in range(st.session_state.rounds)], "Player": [])
    num_players = st.session_state.num_players
    half = int(num_players/2)
    st.session_state["draft_order"] = int(st.session_state.rounds/2) * ([i for i in range(1, num_players+1)] + [i for i in range(num_players, 0, -1)])
    calculate_lead()
    # TODO! the calculate_lead function needs to happen after every pick! Or was it once every round?
    agg_dict ={"Player": "first", "lead": "first"}
    df = st.session_state.working_df.copy()
    for pick_num, team in enumerate(st.session_state.draft_order):
        _round = int(1 + pick_num / num_players)
        roster = st.session_state[f"team_{team}_likely_roster"]
        avail_positions = []
        for position in roster.keys():
            if len(roster[position]) < st.session_state.roster[position]:
                avail_positions.append(position)
        if len(avail_positions) == 0:
            avail_positions = roster.keys()                
        likely_pick = df.loc[(df.likely_pick == 0) & (df.position in avail_positions)].groupby("position", as_index = False).agg(agg_dict).sort_values("lead", ascending = False).iloc[0]
        player, position = likely_pick.Player, likely_pick.position
        df.loc[df.Player == player, ["likely_pick", "round"]] = [1, _round]
        st.session_state[f"team_{i+1}_likely_roster"][position] = player
        st.session_state[f"team_{i+1}_likely_picks"][_round] = player
    for _round in range(st.session_state.rounds, 0, -1):
        df.loc[df.round == i, "likely_pick"] = 0
        team_order = [team for team in range(1, num_players+1)]
        if _round % 2 == 0:
            team_order = team_order[::-1]
        # for team in team_order:        
        for j in range(num_players):
            player = df.loc[df.likely_pick == 0].groupby("position", as_index = False).agg(agg_dict).sort_values("lead", ascending = False).iloc[0].Player
            df.loc[df.Player == player, ["likely_pick", "round"]] = [1, _round]





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
    num_players = st.number_input("How many teams in your draft?", min_value = 1)
    for i in range(len(num_players)):
        st.session_state[f"team_{i+1}_name"] = st.text_input(f"Team {i + 1} Name:")
    your_num = st.number_input("What number are you?", min_value = 1)
    st.session_state["num_players"] = num_players
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





    
