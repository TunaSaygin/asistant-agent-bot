from typing import Any, Dict
import os
# import openai outdated
from openai import OpenAI

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


