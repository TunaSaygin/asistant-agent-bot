import json
import random

class WozDialogue:
    def __init__(self,woz_dialog,woz_key ,woz_goals) -> None:
        self.simulation_history = []
        self.woz_dialog = woz_dialog
        self.woz_key = woz_key
        self.woz_goals = woz_goals
    def add_uterance(self,utterance):
        self.simulation_history.append(utterance)
    def printSimulation(self):
        print(f"Dialog no {self.woz_key}")
        for sim_utterance in self.simulation_history:
            print(sim_utterance)
    def printWoz_Dialog(self):
        print(f"Dialog no {self.woz_key}")
        for turn,woz_utterance in enumerate(self.woz_dialog):
            print(f"{'User:' if turn%2==0 else 'Asistant:'}{woz_utterance['text']}")
    

class DialogueLoader:
    def __init__(self,woz21_file = "../MWOZ/MultiWOZ_2.1/data.json") -> None:
        with open(woz21_file,"r") as f:
            self.mwoz = json.load(f)
    def load_dialogue(self,shuffle, max_dialogues=10):
        dialogues = list(self.mwoz.items())  # Get items as (key, value) pairs
        if shuffle:
            random.shuffle(dialogues)
        for dial_no, (key, dialogue) in enumerate(dialogues):
            if dial_no >= max_dialogues:
                break
            print(f"Key: {key}, Dialogue: {dialogue}")
            yield dial_no, WozDialogue(dialogue["log"],key ,dialogue["goal"]["message"])

loader = DialogueLoader()
dialogues = loader.load_dialogue(True,1)
for dial_no, dialogue in dialogues:
  print(f"dial_no:{dial_no}")
  dialogue.printWoz_Dialog()
  break
