import argparse
import tqdm
import Dialog.utils
from UserAgent import UserAgent
from  AsistantAgent import AssistantAgent
import json
from gpt3_verbose_thought import GPT3Thought
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database_path", type=str, default="multiwoz_database")
    parser.add_argument("--dataset", type=str, default="multiwoz")
    parser.add_argument("--split", type=str, default='test')
    parser.add_argument("--single_domain", action='store_true')
    parser.add_argument("--restrict_domains", type=str)
    parser.add_argument("--dials_total", type=int, default=5)
    parser.add_argument("--max_turns_per_dial", type=int, default=5)
    args = parser.parse_args()
    total = args.dials_total
    data_gen = Dialog.utils.DialogueLoader().load_dialogue(args.dials_total)
    file_path = "key.json"
    with open(file_path, 'r') as file:
        oai_key = json.load(file)["api_key"]
    progress_bar = tqdm.tqdm(total=total)

    
    for it, dialog,frame in data_gen:
        if it== args.dials_total:
            break
        turn = 0
        progress_bar.update(1)
        user_agent = UserAgent(dialog.woz_goals,oai_key, dialog.woz_key)
        system_agent = AssistantAgent(
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
        while turn <args.max_turns_per_dial:
            user_response = user_agent.generate_utterance()
            # print("User_response:",user_response)
            dialog.add_uterance(f"Customer: {user_response}")
            user_agent.addDialogue(f"User:{user_response}\n")

            system_response =system_agent.gen_utterance(user_response)
            dialog.add_uterance(f"System:{system_response}")
            user_agent.addDialogue(f"System:{system_response}\n")
            print(f"System_response: {system_response}")
            turn +=1
        system_agent = AssistantAgent(
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
        print("--"*20)
        print("Same dialogue with Taaha's User simulation")
        print("--"*20+"\n")
        user_model = GPT3Thought()
        while True:
            # Get user model response
            thought_response, user_response = user_model.get_response(frame)

            # Update frame
            frame.update_frame({"role": "thought", "content": thought_response})
            frame.update_frame({"role": "user_agent", "content": user_response})

            # Check if the conversation is over
            if user_response == '<COMPLETE_CONVERSATION>':
                break

            # Get client model response
            client_response = system_agent.gen_utterance(frame.dial_history[-1]['content'])
            print("Thought: ", thought_response)
            print("User: ", user_response)
            print("System: ", client_response)

            # Update frame
            frame.update_frame({"role": "tod_system", "content": client_response})
            print("\n")
            # Check if the conversation is over
            if len(frame.dial_history) == 6:
                break

        print("Frames over")
        # Initialize the user-agent model taaha kazi
        
        