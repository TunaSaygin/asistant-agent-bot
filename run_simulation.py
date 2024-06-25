import argparse
import tqdm
from loaders import load_mwoz
import Dialog.utils
from UserAgent import UserAgent
import AsistantAgent
import json
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database_path", type=str, default="multiwoz_database")
    parser.add_argument("--dataset", type=str, default="multiwoz")
    parser.add_argument("--split", type=str, default='test')
    parser.add_argument("--single_domain", action='store_true')
    parser.add_argument("--restrict_domains", type=str)
    parser.add_argument("--dials_total", type=int, default=5)
    args = parser.parse_args()
    total = args.dials_total
    data_gen = Dialog.utils.DialogueLoader().load_dialogue(args.dials_total)
    file_path = "key.json"
    with open(file_path, 'r') as file:
        oai_key = json.load(file)["api_key"]
    tn = 0
    progress_bar = tqdm.tqdm(total=total)
    for it, dialog in enumerate(data_gen):
        user_agent = UserAgent(dialog.woz_goals,oai_key)
        user_response = user_agent.generate_utterance()
        print("User_response:",user_response)
        