import sys
sys.path.append('/content/asistant-agent-bot')
from Dialog.utils import DialogueLoader
from AsistantAgent import AssistantAgent
from huggingface_hub import login
import json
if __name__ == "__main__":
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    BLUE = "\033[34m"
    dial_iterator = DialogueLoader().load_dialogue(True)
    max_dial = 10
    file_path = "key.json"
    with open(file_path, 'r') as file:
        oai_key = json.load(file)["api_key"]
    with open(file_path, 'r') as file:
            hf_api_token = json.load(file)["hf_token"]
            login(token=hf_api_token)
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
    system_llama = AssistantAgent(
        cache_dir=".",
        oai_key=oai_key,
        model_name="meta-llama/Meta-Llama-3-8B-Instruct",
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
                prev_dial_history = current_dial_history + [f"{role}{utterance['text']}"]
                system.resetDialogueHistory()
                system.seedDialogueHistory(current_dial_history)
                system_llama.resetDialogueHistory()
                system_llama.seedDialogueHistory(current_dial_history)
                print(f"Current_dial_history:{current_dial_history}")
                response = system.gen_utterance(utterance["text"])
                response_llama = system.gen_utterance(utterance["text"])
                current_dial_history = prev_dial_history
                print(f"{MAGENTA}System_response(gpt):{response}{RESET}")
                print(f"{BLUE}System_response(LLAMA):{response_llama}{RESET}")
                print(f"{GREEN}GT_response: {gt_dial.woz_dialog[utterance_no+1]}{RESET}")
            else:
                current_dial_history.append(f"{role}{utterance['text']}")
