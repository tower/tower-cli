from typing import List

from ollama import chat, pull
from ollama import ChatResponse
from ollama import ResponseError

from huggingface_hub import InferenceClient, ChatCompletionOutput

from ._context import TowerContext

"""
OLLAMA_MODELS and HUGGING_FACE_MODELS are dictionaries that map published model
names to the internal names used by Tower when routing LLM requests to the
underlying provider.
"""
OLLAMA_MODELS = {
    "deepseek-r1": "deepseek-r1:14b",
}

HUGGING_FACE_MODELS = {
    "deepseek-r1": "deepseek-ai/DeepSeek-R1",
}

def extract_model_name(ctx: TowerContext, supported_model: str) -> str:
    """
    extract_model_name maps the relevant supported model into a model for the
    underlying LLM provider that we want to use.
    """
    if ctx.is_local():
        if supported_model not in OLLAMA_MODELS:
            raise ValueError(f"Model {supported_model} not supported for Ollama.")
        return OLLAMA_MODELS[supported_model]
    else:
        if supported_model not in HUGGING_FACE_MODELS:
            raise ValueError(f"Model {supported_model} not supported for Hugging Face Hub.")
        return HUGGING_FACE_MODELS[supported_model]

class Llm:
    def __init__(self, context: TowerContext, model_name: str, max_tokens: int = 1000):
        """
        Wraps up interfacing with a language model in the Tower system.
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.context = context

    def inference(self, messages: List) -> str:
        """
        Simulate the inference process of a language model.
        In a real-world scenario, this would involve calling an API or using a library to get the model's response.
        """
        model_name = extract_model_name(self.context, self.model_name)

        if self.context.is_local():
            # Use Ollama for local inference using Apple GPUs
            response = infer_with_ollama(
                ctx = self.context,
                model = model_name,
                messages = messages
            )
        else:
            max_tokens = self.max_tokens
            response = infer_with_hugging_face_hub(
                ctx = self.context,
                model = model_name,
                messages = messages, 
                max_tokens=max_tokens
            )

        return response

    def prompt(self, prompt: str) -> str:
        """
        Prompt a language model with a string. This basically will format the
        relevant messages internally to send to the model.
        """
        return self.inference([{
            "role": "user",
            "content": prompt,
        }])

def llms(model_name: str) -> Llm:
    ctx = TowerContext.build()
    return Llm(
        context = ctx,
        model_name=model_name
    )

def extract_ollama_message(resp: ChatResponse) -> str:
    return resp.message.content

def extract_hugging_face_hub_message(resp: ChatCompletionOutput) -> str:
    return resp.choices[0].message.content

def infer_with_ollama(ctx: TowerContext, model: str, messages: list, is_retry: bool = False) -> str:
    try:
        response: ChatResponse = chat(model=model, messages=messages)
        return extract_ollama_message(response)
    except ResponseError as e:
        if e.status_code == 404 and not is_retry:
            # Assume the model doesn't exist. We pull it, which once it exists
            # (or if it exists) will start it for us.
            pull(model=model)

            # Retry the inference after the model hasbeen pulled.
            return infer_with_ollama(ctx, model, messages, is_retry=True)

        # Couldn't figure out what the error was, so we'll just raise it accordingly.
        raise e

def infer_with_hugging_face_hub(ctx: TowerContext, model: str, messages: List, **kwargs) -> str:
    """
    Uses the Hugging Face Hub API to perform inference. Will use configuration
    supplied by the environment to determine which client to connect to and all
    that.
    """
    client = InferenceClient(
        provider=ctx.hugging_face_provider,
        api_key=ctx.hugging_face_api_key
    )

    completion = client.chat_completion(messages,
        model=model,
        max_tokens=kwargs.get("max_tokens", 1000),
    )

    return extract_hugging_face_hub_message(completion)
