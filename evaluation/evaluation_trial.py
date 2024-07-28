import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mwzeval.metrics import Evaluator as MWEvaluator
import json
result = {}
with open("evaluation/train_data (2).json","r") as f:
        result = json.load(f)
results = result
evaluator = MWEvaluator(bleu=True, success=True, richness=True, jga=True, dst=True)
eval_results = evaluator.evaluate(results)
print(eval_results)