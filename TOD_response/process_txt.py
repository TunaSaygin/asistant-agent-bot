from datetime import date
import re
import json

def parse_json_like_string(s):
    if not s:
        return s

     # Replace single quotes with double quotes
    s = s.replace("'", '"')

    # Fix common formatting issues
    s = re.sub(r',\s*([}\]])', r'\1', s)  # Remove extra commas before the closing braces
    s = re.sub(r',\s*}', '}', s)  # Ensure no trailing commas
    s = re.sub(r',\s*]', ']', s)
    
    # Add quotes around keys
    s = re.sub(r'(\w+):', r'"\1":', s)
     # Ensure times in key-value pairs are quoted correctly
    s = re.sub(r'(?<=:\s)(\d+:\d+)(?=\s*[,}])', r'"\1"', s)
    # # Fix double quotes within strings
    # s = re.sub(r'""', '"', s)
    
  # Handle cases like "19:30" not within strings
    s = re.sub(r'(?<!")(\d+:\d+)(?!,")', r'"\1"', s)  # Ensure time values are quoted
    
    # Ensure strings are properly formatted
    s = re.sub(r'([:,])\s*"', r'\1 "', s)  # Add space after colons and commas if missing
    s = re.sub(r'"\s*([:,])', r'" \1', s)  # Add space before colons and commas if missing
    
     # Handle time formatting specifically
    s = re.sub(r'(\d+)"\s*:\s*(\d+)', r'\1:\2', s)
     # Correct the improper double quote
    s = re.sub(r'(\w)"(\w)', r'\1\'\2', s)  # Fix cases like "I"d" to "I'd"
     # Escape any remaining invalid backslashes
    s = s.replace('\\"', '"')
    s = s.replace("\\'", "'")
     # Fix double quotes within strings
    s = re.sub(r'""(\d+:\d+)"', r'"\1"', s)  # Ensure time values are properly quoted
    s = re.sub(r'""(\w+)"', r'"\1"', s)
    text = 'There are multiple trains headed to cambridge sunday after "21:00. Where are you leaving from?"'

    # Define the regular expression pattern to find and remove quotes around standalone time formats in the "text" field only
    pattern = re.compile(r'(?<=after )"(\d{2}:\d{2})"(?=\.)')
    s = re.sub("\"\d{2}:\d{2}\s*(\w+|.)",r'\g<0>',s)
    # Replace the matches in the string
    # corrected_text = pattern.sub(r'\1', s)
    # print(f"{s}\n\n")
    # print(corrected_text)
    return s

def parse_dialogue_block(block):
    dialogue = {}

    # Extract Dialogue ID
    dialogue_id_match = re.search(r'(\w+\.json)', block)
    if dialogue_id_match:
        dialogue['id'] = dialogue_id_match.group(1)

    # Extract GPT responses
    gpt_responses = re.findall(r'System_response\(gpt\):(.*?)\n', block)
    dialogue['gpt_responses'] = [resp.strip() for resp in gpt_responses]

    # Extract LLAMA responses
    llama_responses = re.findall(r'System_response\(LLAMA\):(.*?)\n', block)
    dialogue['llama_responses'] = [resp.strip() for resp in llama_responses]

    # Extract GT responses
    pattern = r"GT_response:\s*\{(.*?)(?=\s*(Key:|Current_dial_history:))"
    gt_responses = re.findall(pattern, block, re.DOTALL)
    
    # Extract only the response part, ignoring the stopping keyword
    gt_responses = [resp[0].strip() for resp in gt_responses]
    gt_responses = ['{' + resp for resp in gt_responses]
    
    # Convert GT responses to JSON
    # gt_responses = [json.loads(parse_json_like_string(resp)) for resp in gt_responses]
    dialogue['gt_responses'] = gt_responses

    # Extract parsed states
    parsed_states = re.findall(r"Parsed State:\s*\{(.*?)\}\}", block, re.DOTALL)
    parsed_states = ['{' + state.strip() + '}}' for state in parsed_states]
    # print(f"Parsed_states: {parsed_states[0]}")
    parsed_states = [json.loads(parse_json_like_string(state)) for state in parsed_states]
    dialogue['parsed_states'] = parsed_states

    # Extract total states
    total_states = re.findall(r"Total State:\s*\{(.*?)\}\}", block, re.DOTALL)
    total_states = ['{' + state.strip() + '}}' for state in total_states]
    total_states = [json.loads(parse_json_like_string(state)) for state in total_states]
    dialogue['total_states'] = total_states

    # Extract questions and dialogue history
    questions = re.findall(r"Question:\s*(.*?)\n", block)
    dialogue['questions'] = [q.strip() for q in questions]
    
    current_dial_histories = re.findall(r"Current_dial_history:\[(.*?)\]", block, re.DOTALL)
    dialogue['current_dial_histories'] = [history.strip() for history in current_dial_histories]

    return dialogue
def parse_dialogues(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Split the content at every beginning of "Dial Key" to get individual dialogues
    dialogue_blocks = re.split(r'---------Dial Key ', content)
    
    dialogues = []
    it = 0
    for block in dialogue_blocks:
        # print("-"*15+f"\-------Block {it} -------------------")
        if block.strip():
            # print(block)
            dialogue = parse_dialogue_block(block)
            dialogues.append(dialogue)
            it +=1

    return dialogues

def get_turn(dialogue,woz_data):
    formatted_dialogue = {"key":dialogue["id"],"history":dialogue['current_dial_histories'][-1]}
    actual_data = woz_data[dialogue["id"]]
    formatted_dialogue["GT"] = [{"belief_state":turn["metadata"], "text":turn["text"]} for it,turn in enumerate(actual_data["log"]) if it%2==1]
    formatted_dialogue["GPT"] = [{"belief_state":dialogue["gpt_responses"][i], "text":dialogue["parsed_states"][2*i]} for i in range(len(dialogue["gpt_responses"]))]
    formatted_dialogue["LLAMA"] = [{"belief_state":dialogue["llama_responses"][i], "text":dialogue["parsed_states"][2*i]} for i in range(len(dialogue["llama_responses"]))]
    return formatted_dialogue
def process_string(dialogues,woz_data):
    result = []
    for i in range(1,len(dialogues)):
        result.append(get_turn(dialogues[i],woz_data))
    with open(f"./TOD_response/{str(date.today())}.json","w") as f:
        json.dump(result,f)
    
if __name__ == "__main__":
    # Read the content of the text file
    file_path = 'TOD_response/result.txt'
    dialogues = parse_dialogues(file_path)

    with open(file_path, 'r') as file:
        content = file.read()
    # Let's print the first dialogue to verify
    woz_data = {}
    with open("./TOD_response/data (1).json","r") as f:
        woz_data = json.load(f)
    result = get_turn(dialogues[-1],woz_data)
    import pprint
    pprint.pprint(result)
    process_string(dialogues,woz_data)
    # sample_text = """
    # Parsed State: {'restaurant': {'area': 'center', 'food': 'modern', 'pricerange': 'moderate', 'name': 'Riverside'}}
    # Total State: {'restaurant': {'area': 'center', 'food': 'modern', 'pricerange': 'moderate', 'name': 'Riverside'}}
    # """
    # print(parse_json_like_string("Parsed_states: {'restaurant': {'area': 'center', 'food': 'modern', 'pricerange': 'moderate', 'name': 'Riverside'}"))
    # dialogue = parse_dialogue_block(sample_text)
    # print(json.dumps(dialogue, indent=2))
#     sampled_text = """GT_response: {'text': 'There are 3 choices, 2 moderately priced and 1 expensive. Do you have a preference? ', 'metadata': {'taxi': {'book': {'booked': []}, 'semi': {'leaveAt': '', 'destination': '', 'departure': '', 'arriveBy': ''}}, 'police': {'book': {'booked': []}, 'semi': {}}, 'restaurant': {'book': {'booked': [], 'people': '', 'day': '', 'time': ''}, 'semi': {'food': 'turkish', 'pricerange': 'not mentioned', 'name': 'not mentioned', 'area': 'centre'}}, 'bus': {'book': {'booked': [], 'people': ''}, 'semi': {'leaveAt': '', 'destination': '', 'day': '', 'arriveBy': '', 'departure': ''}}, 'hospital': {'book': {'booked': []}, 'semi': {'department': ''}}, 'hotel': {'book': {'booked': [], 'people': '', 'day': '', 'stay': ''}, 'semi': {'name': '', 'area': '', 'parking': '', 'pricerange': '', 'stars': '', 'internet': '', 'type': ''}}, 'attraction': {'book': {'booked': []}, 'semi': {'type': '', 'name': '', 'area': ''}}, 'train': {'book': {'booked': [], 'people': ''}, 'semi': {'leaveAt': '', 'destination': '', 'day': '', 'arriveBy': '', 'departure': ''}}}, 'dialog_act': {'Restaurant-Select': [['none', 'none']], 'Restaurant-Inform': [['Choice', '3'], ['Choice', '2'], ['Choice', '1'], ['Price', 'moderately priced'], ['Price', 'expensive']]}, 'span_info': [['Restaurant-Inform', 'Choice', '3', 2, 2], ['Restaurant-Inform', 'Choice', '2', 5, 5], ['Restaurant-Inform', 'Choice', '1', 9, 9], ['Restaurant-Inform', 'Price', 'moderately priced', 6, 7], ['Restaurant-Inform', 'Price', 'expensive', 10, 10]]}
# """
#     dialogue = parse_dialogue_block(sampled_text)
#     print(json.dumps(dialogue, indent=2))
#     GT_response = {'text': 'There are 3 choices, 2 moderately priced and 1 expensive. Do you have a preference? ',
#                    'metadata': {'taxi': {'book': {'booked': []}, 'semi': {'leaveAt': '', 'destination': '', 'departure': '', 'arriveBy': ''}}, 'police': {'book': {'booked': []}, 'semi': {}}, 'restaurant': {'book': {'booked': [], 'people': '', 'day': '', 'time': ''}, 'semi': {'food': 'turkish', 'pricerange': 'not mentioned', 'name': 'not mentioned', 'area': 'centre'}}, 'bus': {'book': {'booked': [], 'people': ''}, 'semi': {'leaveAt': '', 'destination': '', 'day': '', 'arriveBy': '', 'departure': ''}}, 'hospital': {'book': {'booked': []}, 'semi': {'department': ''}}, 'hotel': {'book': {'booked': [], 'people': '', 'day': '', 'stay': ''}, 'semi': {'name': '', 'area': '', 'parking': '', 'pricerange': '', 'stars': '', 'internet': '', 'type': ''}}, 'attraction': {'book': {'booked': []}, 'semi': {'type': '', 'name': '', 'area': ''}}, 'train': {'book': {'booked': [], 'people': ''}, 'semi': {'leaveAt': '', 'destination': '', 'day': '', 'arriveBy': '', 'departure': ''}}}, 
#                    'dialog_act': {'Restaurant-Select': [['none', 'none']], 'Restaurant-Inform': [['Choice', '3'], ['Choice', '2'], ['Choice', '1'], ['Price', 'moderately priced'], ['Price', 'expensive']]}, 'span_info': [['Restaurant-Inform', 'Choice', '3', 2, 2], ['Restaurant-Inform', 'Choice', '2', 5, 5], ['Restaurant-Inform', 'Choice', '1', 9, 9], ['Restaurant-Inform', 'Price', 'moderately priced', 6, 7], ['Restaurant-Inform', 'Price', 'expensive', 10, 10]]}    
