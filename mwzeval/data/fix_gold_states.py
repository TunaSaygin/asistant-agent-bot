import json
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(dir_path, "gold_states.json")
with open(data_path,"r") as f:
    gold_states = json.load(f)

for dial_key in gold_states.keys():
    dialogue_turns = gold_states[dial_key]
    for turn in dialogue_turns:
        if "train" in turn.keys() and "arrive" in turn["train"].keys():
            turn["train"]["arriveby"] = turn["train"].pop("arrive")
write_path = os.path.join(dir_path,"gold_states_fixed.json")            
with open(write_path,"w") as write_file:
    json.dump(gold_states,write_file,indent=6)