from Dialog.utils import DialogueLoader
from AsistantAgent import AssistantAgent
import json
if __name__ == "__main__":
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    dial_iterator = DialogueLoader().load_dialogue(True)
    max_dial = 10
    file_path = "../key.json"
    with open(file_path, 'r') as file:
        oai_key = json.load(file)["api_key"]
    system = AssistantAgent(
        cache_dir=".",
        oai_key=oai_key,
        model_name="gpt-3.5-turbo-0613",
        faiss_db="multiwoz-context-db.vec",
        num_examples=2,
        dials_total=100,
        database_path="multiwoz_database",
        dataset="multiwoz",
        context_size=3,
        ontology="ontology.json",
        output="results",
        run_name="",
        use_gt_state=False,
        use_gt_domain=False,
        use_zero_shot=True,
        verbose=True,
        goal_data=None,
        debug=True,# Placeholder, adjust based on actual usage
    )
    for dial_number, gt_dial, _ in dial_iterator:
        if max_dial == dial_number:
            break
        print(f"---------Dial Key {gt_dial.woz_key}------------")
        current_dial_history = []
        for utterance_no, utterance in enumerate(gt_dial.woz_dialog):
            role = "User: " if utterance_no%2==0 else "System: "
            if utterance_no%2==0:
                prev_dial_history = current_dial_history + [f"{role}{utterance}"]
                system.resetDialogueHistory()
                system.seedDialogueHistory(current_dial_history)
                print(f"Current_dial_history:{current_dial_history}")
                response = system.gen_utterance(utterance)
                current_dial_history = prev_dial_history
                print(f"{MAGENTA}System_response:{response}{RESET}")
                print(f"{GREEN}GT_response: {gt_dial.woz_dialog[utterance_no+1]}{RESET}")
            else:
                current_dial_history.append(f"{role}{utterance}")
