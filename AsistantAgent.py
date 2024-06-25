import json
import random
import pickle
import logging
from definitions import MW_FEW_SHOT_DOMAIN_DEFINITIONS, MW_ZERO_SHOT_DOMAIN_DEFINITIONS, SGD_FEW_SHOT_DOMAIN_DEFINITIONS, SGD_ZERO_SHOT_DOMAIN_DEFINITIONS, multiwoz_domain_prompt, sgd_domain_prompt
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
from database import MultiWOZDatabase
from delex import prepareSlotValuesIndependent
from model import (
    FewShotPromptedLLM,
    SimplePromptedLLM,
    FewShotOpenAILLM,
    ZeroShotOpenAILLM,
    FewShotOpenAIChatLLM,
    ZeroShotOpenAIChatLLM,
    FewShotAlpaca,
    ZeroShotAlpaca
    )
logger = logging.getLogger(__name__)
from utils import ExampleFormatter, ExampleRetriever, parse_state
class AssistantAgent:
    def __init__(self,oai_key, cache_dir, model_name, faiss_db, num_examples, dials_total, database_path, dataset, context_size, ontology, output, run_name, use_gt_state, use_gt_domain, use_zero_shot, verbose, goal_data, debug):
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.faiss_db = faiss_db
        self.num_examples = num_examples
        self.dials_total = dials_total
        self.database_path = database_path
        self.dataset = dataset
        self.context_size = context_size
        self.ontology = ontology
        self.output = output
        self.run_name = run_name
        self.use_gt_state = use_gt_state
        self.use_gt_domain = use_gt_domain
        self.use_zero_shot = use_zero_shot
        self.verbose = verbose
        self.goal_data = goal_data
        self.debug = debug
        if 'tk-instruct-3b' in self.model_name:
            model_name = 'tk-3B'
        elif 'tk-instruct-11b' in self.model_name:
            model_name = 'tk-11B'
        elif 'opt-iml-1.3b' in self.model_name:
            model_name = 'opt-iml-1.3b'
        elif 'opt-iml-30b' in self.model_name:
            model_name = 'opt-iml-30b'
        elif 'NeoXT' in self.model_name:
            model_name = 'GPT-NeoXT-20b'
        elif 'gpt-3.5' in self.model_name:
            model_name = 'ChatGPT'
        elif self.model_name == 'alpaca':
            model_name = 'Alpaca-LoRA'
        else:
            model_name = 'GPT3.5'
        if self.model_name.startswith("text-"):
            self.model_factory = ZeroShotOpenAILLM if self.use_zero_shot else FewShotOpenAILLM
            self.model = self.model_factory(self.model_name,oai_key)
            self.domain_model = ZeroShotOpenAILLM(self.model_name,oai_key)
        elif self.model_name.startswith("gpt-"):
            self.model_factory = ZeroShotOpenAIChatLLM if self.use_zero_shot else FewShotOpenAIChatLLM
            self.model = self.model_factory(self.model_name,oai_key)
            self.domain_model = ZeroShotOpenAIChatLLM(self.model_name,oai_key)
        elif any([n in self.model_name for n in ['opt', 'NeoXT']]):
            tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=self.cache_dir)
            model_w = AutoModelForCausalLM.from_pretrained(self.model_name,
                                                        low_cpu_mem_usage=True,
                                                        cache_dir=self.cache_dir,
                                                        device_map="auto",
                                                        load_in_8bit=True)
            model_factory = SimplePromptedLLM if self.use_zero_shot else FewShotPromptedLLM
            model = self.model_factory(model_w, tokenizer, type="causal")
            domain_model = SimplePromptedLLM(model_w, tokenizer, type="causal")
        elif 'alpaca' in self.model_name:
            self.model_factory = ZeroShotAlpaca if self.use_zero_shot else FewShotAlpaca
            self.model = self.model_factory(model_name="Alpaca-LoRA")
            self.domain_model = ZeroShotAlpaca(model_name="Alpaca-LoRA")
        else:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=self.cache_dir)
            model_w = AutoModelForSeq2SeqLM.from_pretrained(self.model_name,
                                                        low_cpu_mem_usage=True,
                                                        cache_dir=self.cache_dir,
                                                        device_map="auto",
                                                        load_in_8bit=True)
            self.model_factory = SimplePromptedLLM if self.use_zero_shot else FewShotPromptedLLM
            self.model = self.model_factory(model_w, tokenizer, type="seq2seq")
            self.domain_model = SimplePromptedLLM(model_w, tokenizer, type="seq2seq")
        with open(faiss_db, 'rb') as f:
            self.faiss_vs = pickle.load(f)
        with open(ontology, 'r') as f:
            self.ontology = json.load(f)
        
        if dataset == 'multiwoz':
            self.domain_prompt = multiwoz_domain_prompt
            self.database = MultiWOZDatabase(database_path)
            state_vs = self.faiss_vs
            #with open('multiwoz-state-update-1turn-only-ctx2.vec', 'rb') as f:
            #   state_vs = pickle.load(f)
            self.delex_dic = prepareSlotValuesIndependent(database_path)
        else:
            self.domain_prompt = sgd_domain_prompt
            self.state_vs = self.faiss_vs
            self.delex_dic = None
        self.example_retriever = ExampleRetriever(self.faiss_vs)
        self.state_retriever = ExampleRetriever(state_vs)
        self.example_formatter = ExampleFormatter(ontology=self.ontology)

        #dialogue turns
        self.history = []
        self.total_state = {}

    def addDialogueHistory(self,dialogue):
        self.history.append(dialogue)
    def resetDialogueHistory(self):
        self.history=[]
    def gen_utterance(self,user_request):
        retrieve_history = self.history + ["Customer: " + user_request]
        retrieved_examples = self.example_retriever.retrieve("\n".join(retrieve_history[-self.context_size:]), k=20)
        retrieved_domains = [example['domain'] for example in retrieved_examples]
        selected_domain, dp = self.domain_model(self.domain_prompt, predict=True, history="\n".join(self.history[-2:]), utterance=F"Customer: {user_request.strip()}")
        if self.dataset == 'multiwoz':
            available_domains = list(MW_FEW_SHOT_DOMAIN_DEFINITIONS.keys())
        else:
            available_domains = list(SGD_FEW_SHOT_DOMAIN_DEFINITIONS.keys())
        if selected_domain not in available_domains:
            selected_domain = random.choice(available_domains)
        if self.dataset == 'multiwoz':
            domain_definition = MW_ZERO_SHOT_DOMAIN_DEFINITIONS[selected_domain] if self.use_zero_shot else MW_FEW_SHOT_DOMAIN_DEFINITIONS[selected_domain]
        else:
                domain_definition = SGD_ZERO_SHOT_DOMAIN_DEFINITIONS[selected_domain] if self.use_zero_shot else SGD_FEW_SHOT_DOMAIN_DEFINITIONS[selected_domain]
        if self.use_gt_domain:
            selected_domain = self.gt_domain
        retrieved_examples = [example for example in retrieved_examples if example['domain'] == selected_domain]
        num_examples = min(len(retrieved_examples), self.num_examples)
        num_state_examples = 5
        state_examples = [example for example in self.state_retriever.retrieve("\n".join(retrieve_history[-self.context_size:]), k=20) if example['domain'] == selected_domain][:num_state_examples]
        positive_state_examples = self.example_formatter.format(state_examples[:num_state_examples],
                                                            input_keys=["context"],
                                                            output_keys=["state"],
                                                            )
                                                            #use_json=True)
        negative_state_examples = self.example_formatter.format(state_examples[:num_state_examples],
                                                            input_keys=["context"],
                                                            output_keys=["state"],
                                                            corrupt_state=True)
        response_examples = self.example_formatter.format(retrieved_examples[:num_examples],
                                                        input_keys=["context", "full_state", "database"],
                                                        output_keys=["response"],
                                                        use_json=True)
        
        state_prompt = domain_definition.state_prompt
        response_prompt = domain_definition.response_prompt
        try:
            kwargs = {
                "history": "\n".join(self.history),
                "utterance": user_request.strip()
            }
            if not self.use_zero_shot:
                kwargs["positive_examples"] = positive_state_examples
                kwargs["negative_examples"] = [] # negative_state_examples
            state, filled_state_prompt = self.model(state_prompt, predict=True, **kwargs)
        except Exception as e:
            state = "{}"
            print(f"Failed line 282: {e.with_traceback()}")
        parsed_state = parse_state(state, default_domain=selected_domain)
        if selected_domain not in parsed_state:
            parsed_state[selected_domain] = {}
        if not isinstance(parsed_state[selected_domain], dict):
            parsed_state[selected_domain] = {}
        keys_to_remove = [k for k in parsed_state[selected_domain].keys() if k not in domain_definition.expected_slots]
        for k in keys_to_remove:
            del parsed_state[selected_domain][k]
        try:
            print(f"parsed_state:{parsed_state}")
            for domain, ds in parsed_state.items():
                for slot, value in ds.items():
                    pass
        except Exception as e:
            parsed_state = {selected_domain: {}}
            print(f"Failed Parsing: {e.with_traceback()}")
        final_state = {}
        for domain, ds in parsed_state.items():
            if domain in available_domains:
                final_state[domain] = ds
        
        for domain, dbs in final_state.items():
            if domain not in self.total_state:
                self.total_state[domain] = dbs
            else:
                for slot, value in dbs.items():
                    value = str(value)
                    if value not in ['dontcare', 'none', '?', ''] and len(value) > 0:
                        self.total_state[domain][slot] = value
        
        YELLOW = "\033[33m"
        RESET = "\033[0m"
        if self.debug:
            print(f"{YELLOW}",'-' * 100,f"{RESET}")
            print(f"{YELLOW}Question: {user_request}{RESET}", flush=True)
            print(f"{YELLOW}Selected domain: {selected_domain}{RESET}", flush=True)
            logger.info(f"{YELLOW}Raw State: {state}{RESET}")
            print(f"{YELLOW}Raw State: {state}{RESET}", flush=True)
            logger.info(f"{YELLOW}Parsed State: {final_state}{RESET}")
            print(f"{YELLOW}Parsed State: {final_state}{RESET}", flush=True)
            logger.info(f"{YELLOW}Total State: {self.total_state}{RESET}")
            print(f"{YELLOW}Total State: {self.total_state}{RESET}", flush=True)
        if self.dataset == 'multiwoz':
            database_results = {domain: len(self.database.query(domain=domain, constraints=ds))
                                for domain, ds in self.total_state.items() if len(ds) > 0}
        else:
            database_results = ""
        if self.debug:
            logger.info(f"Database Results: {database_results}")
            print(f"{YELLOW}Database Results: {database_results}{RESET}", flush=True)

        try:
            kwargs = {
                "history": "\n".join(self.history),
                "utterance": user_request.strip(),
                "state": json.dumps(self.total_state), #.replace("{", '<').replace("}", '>'),
                "database": str(database_results)
            }
            if not self.use_zero_shot:
                kwargs["positive_examples"] = response_examples
                kwargs["negative_examples"] = []

            # response, filled_prompt = "IDK", "-"
            response, filled_prompt = self.model(response_prompt, predict=True, **kwargs)
        except Exception as e:
            response = ''
            print(f"failed before delexicalise{e.with_traceback()}")
        
        self.history.append("Customer:"+user_request)
        self.history.append("Assistant:"+response)
        return response
            

if __name__ == "__main__":
    file_path = "key.json"
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
    response = system.gen_utterance("Hi, I want to book a train from Cambridge to London")
    print(response)
    response = system.gen_utterance("I want to travel on Tuesday")
    print(response)
    response = system.gen_utterance("What is the travel time?")
    print(response)