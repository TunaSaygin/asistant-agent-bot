import json
from typing import Any, Dict
import os
from huggingface_hub import login
import torch
# import openai outdated
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from prompts import FewShotPrompt, SimpleTemplatePrompt

class SimplePromptedLLM:
    def __init__(self, model, tokenizer, type='seq2seq'):
        self.model = model
        self.tokenizer = tokenizer
        self.type = type

    def __call__(self, prompt: SimpleTemplatePrompt, predict=True, **kwargs: Any):
        filled_prompt = prompt(**kwargs)
        prediction = self._predict(filled_prompt, **kwargs) if predict else None
        return prediction, filled_prompt

    def _predict(self, text, **kwargs):
        input_ids = self.tokenizer.encode(text,return_tensors="pt").to(self.model.device)
        max_length = max_new_tokens = 50
        if self.type == 'causal':
            max_length = input_ids.shape[1] + max_length
        output = self.model.generate(input_ids,
                                     do_sample=True,
                                     top_p=0.9,
                                     max_new_tokens=max_new_tokens,
                                     temperature=0.1)
        if self.type == 'causal':
            output = output[0, input_ids.shape[1]:]
        else:
            output = output[0]
        output = self.tokenizer.decode(output, skip_special_tokens=True)
        return output


class FewShotPromptedLLM(SimplePromptedLLM):
    def __init__(self, model, tokenizer, type='seq2seq'):
        super().__init__(model, tokenizer, type)

    def __call__(self, prompt: FewShotPrompt, positive_examples: list[Dict], negative_examples: list[Dict], predict=True, **kwargs: Any):
        filled_prompt = prompt(positive_examples, negative_examples, **kwargs)
      #  if len(filled_prompt) > 500:
       #     filled_prompt = prompt(positive_examples[:1], negative_examples[:1], **kwargs)
        prediction = self._predict(filled_prompt, **kwargs) if predict else None
        return prediction, filled_prompt
    
class FewShotLLAMAFactory:
    def __init__(self) -> None:
        self._authenticate
    def _authenticate(self):
        # Replace 'YOUR_HF_API_TOKEN' with your actual Hugging Face API token
        file_path = "key.json"
        with open(file_path, 'r') as file:
            hf_api_token = json.load(file)["hf_token"]
            login(token=hf_api_token)
    def _get_model(self, model_id,is_8bit = False):
        if is_8bit:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_use_double_quant=True,
                bnb_8bit_quant_type="nf4",
                bnb_8bit_compute_dtype=torch.bfloat16
            )
        else:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config = bnb_config,
            device_map = "auto",
            cache_dir = "cache"
        )
        return model
    def _get_tokenizer(self, model_id,stop_tokens=True):
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        tokenizer.pad_token_id = (
                tokenizer.eos_token_id
            )    
        return tokenizer
    def build(self):
        tokenizer = self._get_tokenizer(model_id="meta-llama/Meta-Llama-3-8B-Instruct")
        model = self._get_model(model_id="meta-llama/Meta-Llama-3-8B-Instruct")
        return FewShotPromptedLLAMA3(model,tokenizer)
class FewShotPromptedLLAMA3(FewShotPromptedLLM):
    def __init__(self, model, tokenizer, type='seq2seq'):
        super().__init__(model, tokenizer, type)
        self.MAX_LEN = 100
        self.model = model
        self.tokenizer = tokenizer
    def _predict(self,text,**kwargs):
        formatted_prmpt = self._convert_prmpt2LLAMA3(text)
        inputs = self.tokenizer(formatted_prmpt, return_tensors="pt")
        
        # Generate response
        output_sequences = self.model.generate(
            input_ids=inputs['input_ids'],
            max_length=self.MAX_LEN,
            **kwargs
        )
        
        # Decode the generated text
        generated_text = self.tokenizer.decode(output_sequences[0], skip_special_tokens=True)
        
        return generated_text

    def _get_model(self, model_id,is_8bit = True):
        if is_8bit:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_use_double_quant=True,
                bnb_8bit_quant_type="nf4",
                bnb_8bit_compute_dtype=torch.bfloat16
            )
        else:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config = bnb_config,
            device_map = "auto",
            cache_dir = "cache"
        )
        return model
    def get_tokenizer(self, model_id,stop_tokens=True):
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        tokenizer.pad_token_id = (
                tokenizer.eos_token_id
            )    
        return tokenizer
    def tokenize(self, prompt, add_eos_token=True):
        result = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.MAX_LEN,
            padding=False,
            return_tensors=None,
        )
        if (
            result["input_ids"][-1] != self.tokenizer.eos_token_id
            and len(result["input_ids"]) < self.MAX_LEN
            and add_eos_token
        ):
            result["input_ids"][self.MAX_LEN-1] = self.tokenizer.eos_token_id
            result["attention_mask"][self.MAX_LEN-1] = 1
        
        result["labels"] = result["input_ids"].copy()
        
        return result
    def _convert_prmpt2LLAMA3(self,raw_prmpt):
        split_keyword = "Now"
        parts = raw_prmpt.split(split_keyword, 1)  # Split only on the first occurrence of "Now"

        # First part before "Now"
        first_part = parts[0].strip()

        # Second part after "Now"
        second_part = split_keyword + parts[1].strip()
        return "<|begin_of_text|><|start_header_id|>system<|end_header_id|>"+first_part +  "<|eot_id|> <|start_header_id|>user<|end_header_id|>" + second_part + " <|eot_id|><|start_header_id|>assistant<|end_header_id|>"
class FewShotOpenAILLM(FewShotPromptedLLM):
    def __init__(self, model_name,oai_key):
        super().__init__(None, None)
        self.model_name = model_name
        self.client = OpenAI(
            api_key=oai_key
        )

    def _predict(self, text, **kwargs):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            prompt=text,
            temperature=0,
        )
        return completion.choices[0].text


class FewShotOpenAIChatLLM(FewShotOpenAILLM):
    def _predict(self, text, **kwargs):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": text}
            ],
            temperature=0,
            )
        return completion.choices[0].message.content


class ZeroShotOpenAILLM(SimplePromptedLLM):
    def __init__(self, model_name,oai_key):
        super().__init__(None, None)
        self.model_name = model_name
        self.client = OpenAI(
            api_key=oai_key
        )

    def _predict(self, text, **kwargs):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            prompt=text,
            temperature=0,
        )
        return completion.choices[0].text


class ZeroShotOpenAIChatLLM(ZeroShotOpenAILLM):
    def _predict(self, text, **kwargs):
        try:

            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                 #  {"role": "system", "content": prefix},
                    {"role": "user", "content": text}
                ],
                temperature=0,
                )
            return completion.choices[0].message.content
        except:
            return ""


class FewShotAlpaca(FewShotPromptedLLM):
    def __init__(self, model_name):
        super().__init__(None, None)
        from alpaca import predict as predict_alpaca
        self._predict = predict_alpaca
        self.model_name = model_name

    def _predict(self, text, **kwargs):
        return self._predict(text)


class ZeroShotAlpaca(SimplePromptedLLM):
    def __init__(self, model_name):
        super().__init__(None, None)
        from alpaca import predict as predict_alpaca
        self._predict = predict_alpaca
        self.model_name = model_name

    def _predict(self, text, **kwargs):
        return self._predict(text)


