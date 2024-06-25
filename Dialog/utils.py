import json
import random

class WozDialogue:
    def __init__(self,woz_dialog, woz_key, woz_goals) -> None:
        self.simulation_history = []
        self.woz_dialog = woz_dialog
        self.woz_key = woz_key
        self.woz_goals = woz_goals
    def add_uterance(self,utterance):
        self.simulation_history.append(utterance)
    def printSimulation(self):
        print(f"Dialogue woz_key:{self.woz_key}")
        for sim_utterance in self.simulation_history:
            print(sim_utterance)
    def printWoz_Dialog(self):
        print(f"Dialogue woz_key:{self.woz_key}")
        for turn,woz_utterance in enumerate(self.woz_dialog):
            print(f"{"User:" if turn%2==0 else "Asistant:"}{woz_utterance["text"]}")
    

class DialogueLoader:
    def __init__(self,woz21_file = "MWOZ/") -> None:
        with open("goal_mwoz_data.json") as f:
            self.mwoz = json.load(f)
    def load_dialogue(self,shuffle, max_dialogues=10):
        dialogues = list(self.mwoz.values())
        random.shuffle(dialogues)
        random.shuffle(dialogues)
        for dial_no, dialogue in enumerate(dialogues):
            if dial_no >= max_dialogues:
                break
            yield dial_no, WozDialogue(dialogue["log"],dialogue["key"],dialogue["goals"])
        

