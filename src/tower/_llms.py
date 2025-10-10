from typing import List, Union

from ollama import chat, pull
from ollama import ChatResponse
from ollama import ResponseError
from ollama import list as ollama_list_models

from huggingface_hub import InferenceClient, ChatCompletionOutput
from huggingface_hub import HfApi
from huggingface_hub.utils import RepositoryNotFoundError

from ._context import TowerContext

# TODO: add vllm back in when we have a way to use it
LOCAL_INFERENCE_ROUTERS = [
    "ollama",
]

INFERENCE_ROUTERS = LOCAL_INFERENCE_ROUTERS + ["hugging_face_hub"]

RAW_MODEL_FAMILIES = [
    "all-minilm",
    "aya",
    "aya-expanse",
    "athene-v2",
    "bakllava",
    "bge-large",
    "bge-m3",
    "cogito",
    "codegemma",
    "codegeex4",
    "codeqwen",
    "codestral",
    "codeup",
    "codellama",
    "command-a",
    "command-r",
    "command-r-plus",
    "command-r7b",
    "deepcoder",
    "deepseek-coder",
    "deepseek-coder-v2",
    "deepseek-llm",
    "deepseek-r1",
    "deepseek-v2",
    "deepseek-v2.5",
    "deepseek-v3",
    "deepscaler",
    "devstral",
    "dbrx",
    "dolphin-mistral",
    "dolphin-mixtral",
    "dolphin-phi",
    "dolphin3",
    "dolphincoder",
    "exaone-deep",
    "exaone3.5",
    "everythinglm",
    "falcon",
    "falcon3",
    "gemma",
    "gemma2",
    "gemma3",
    "gemma3n",
    "glm4",
    "goliath",
    "granite-code",
    "granite-embedding",
    "granite3-dense",
    "granite3-guardian",
    "granite3-moe",
    "granite3.1-dense",
    "granite3.1-moe",
    "granite3.2",
    "granite3.2-vision",
    "granite3.3",
    "hermes3",
    "internlm2",
    "lafrican",
    "llama-pro",
    "llama-guard3",
    "llama2",
    "llama2-chinese",
    "llama2-uncensored",
    "llama3",
    "llama3-chatqa",
    "llama3-groq-tool-use",
    "llama3-gradient",
    "llama3.1",
    "llama3.2",
    "llama3.2-vision",
    "llama3.3",
    "llama4",
    "llava",
    "llava-llama3",
    "llava-phi3",
    "magicoder",
    "magistral",
    "marco-o1",
    "mathstral",
    "meditron",
    "medllama2",
    "megadolphin",
    "minicpm-v",
    "mistral",
    "mistral-large",
    "mistral-nemo",
    "mistral-openorca",
    "mistral-small",
    "mistral-small3.1",
    "mistral-small3.2",
    "mistrallite",
    "moondream",
    "mxbai-embed-large",
    "nemotron",
    "nemotron-mini",
    "neural-chat",
    "nexusraven",
    "notus",
    "nous-hermes",
    "nous-hermes2",
    "nous-hermes2-mixtral",
    "nomic-embed-text",
    "notux",
    "olmo2",
    "opencoder",
    "openchat",
    "openthinker",
    "openhermes",
    "orca-mini",
    "orca2",
    "paraphrase-multilingual",
    "phi",
    "phi3",
    "phi3.5",
    "phi4",
    "phi4-mini",
    "phi4-mini-reasoning",
    "phi4-reasoning",
    "phind-codellama",
    "qwen",
    "qwen2",
    "qwen2-math",
    "qwen2.5",
    "qwen2.5-coder",
    "qwen2.5vl",
    "qwen3",
    "qwq",
    "r1-1776",
    "reader-lm",
    "reflection",
    "sailor2",
    "samatha-mistral",
    "shieldgemma",
    "smallthinker",
    "smollm",
    "smollm2",
    "snowflake-arctic-embed",
    "snowflake-arctic-embed2",
    "solar",
    "solar-pro",
    "sqlcoder",
    "stable-beluga",
    "stable-code",
    "stablelm-zephyr",
    "stablelm2",
    "starcoder",
    "starcoder2",
    "starling-lm",
    "sunbeam",
    "tulu3",
    "tinydolphin",
    "tinyllama",
    "vicuna",
    "wizard-math",
    "wizard-vicuna",
    "wizard-vicuna-uncensored",
    "wizardcoder",
    "wizardlm",
    "wizardlm-uncensored",
    "wizardlm2",
    "xwinlm",
    "yarn-llama2",
    "yarn-mistral",
    "yi",
    "yi-coder",
    "zephyr",
]


def normalize_model_family(name: str) -> str:
    """
    Normalize a model family name by removing '-' and '.' characters.
    Args:
        name (str): The model family name to normalize.
    Returns:
        str: The normalized model family name.
    """
    return name.replace("-", "").replace(".", "").lower()


MODEL_FAMILIES = {normalize_model_family(name): name for name in RAW_MODEL_FAMILIES}

# the %-ge of memory that we can use for inference
# TODO: add this back in when implementing memory checking for LLMs
# MEMORY_THRESHOLD = 0.8


def parse_parameter_size(size_str: str) -> float:
    """
    Convert parameter size string (e.g., '8.0B', '7.2B') to number of parameters.
    """
    if not size_str:
        return 0
    multiplier = {"B": 1e9, "M": 1e6, "K": 1e3}
    size_str = size_str.upper()
    for suffix, mult in multiplier.items():
        if suffix in size_str:
            return float(size_str.replace(suffix, "")) * mult
    return float(size_str)


def resolve_model_name(ctx: TowerContext, requested_model: str) -> str:
    """
    Resolve the model name based on the inference router and requested model.

    Args:
        ctx (TowerContext): The context containing the inference router and other settings.
        requested_model (str): The name of the model requested by the user.

    Returns:
        str: The resolved model name.

    Raises:
        ValueError: If the inference router specified in the context is not supported.
    """
    if ctx.inference_router not in INFERENCE_ROUTERS:
        raise ValueError(f"Inference router {ctx.inference_router} not supported.")

    if ctx.inference_router == "ollama":
        return resolve_ollama_model_name(ctx, requested_model)
    elif ctx.inference_router == "hugging_face_hub":
        return resolve_hugging_face_hub_model_name(ctx, requested_model)


def get_local_ollama_models() -> List[dict]:
    """
    Get a list of locally installed Ollama models with their details.
    Returns a list of dictionaries containing:
    - name: model name with tag
    - model_family: model family without tag
    - size: model size in bytes
    - parameter_size: number of parameters
    - quantization_level: quantization level if specified
    """
    try:
        models = ollama_list_models()
        model_list = []
        for model in models["models"]:
            model_name = model.get("model", "")
            model_family = model_name.split(":")[0]
            size = model.get("size", 0)
            details = model.get("details", {})
            parameter_size = details.get("parameter_size", "")
            quantization_level = details.get("quantization_level", "")

            model_list.append(
                {
                    "model": model_name,
                    "model_family": model_family,
                    "size": size,
                    "parameter_size": parameter_size,
                    "quantization_level": quantization_level,
                }
            )
        return model_list
    except Exception as e:
        raise RuntimeError(f"Failed to list Ollama models: {str(e)}")


def resolve_ollama_model_name(ctx: TowerContext, requested_model: str) -> str:
    """
    Resolve the Ollama model name to use.
    """
    local_models = get_local_ollama_models()
    local_model_names = [model["model"] for model in local_models]

    # TODO: add this back in when implementing memory checking for LLMs
    # memory = get_available_memory()
    # memory_threshold = memory['available'] * MEMORY_THRESHOLD

    if normalize_model_family(requested_model) in MODEL_FAMILIES:
        # Filter models by family
        matching_models = [
            model for model in local_models if model["model_family"] == requested_model
        ]

        # TODO: add this back in when implementing memory checking for LLMs
        # Filter models by memory
        # if check_for_memory:
        #    matching_models = [model for model in matching_models if model['size'] < memory_threshold]

        # Return the model with the largest parameter size
        if matching_models:
            best_model = max(
                matching_models, key=lambda x: parse_parameter_size(x["parameter_size"])
            )["model"]
            return best_model
        else:
            # TODO: add this back in when implementing memory checking for LLMs
            # raise ValueError(f"No models in family {requested_model} fit in available memory ({memory['available'] / (1024**3):.2f} GB) with max memory threshold {MEMORY_THRESHOLD} or are not available locally. Please pull a model first using 'ollama pull {requested_model}'")
            raise ValueError(
                f"No models found with name {requested_model}. Please pull a model first using 'ollama pull {requested_model}'"
            )
    elif requested_model in local_model_names:
        return requested_model
    else:
        raise ValueError(
            f"No models found with name {requested_model}. Please pull a model first using 'ollama pull {requested_model}'"
        )


def resolve_hugging_face_hub_model_name(ctx: TowerContext, requested_model: str) -> str:
    """
    Resolve the Hugging Face Hub model name to use.
    Returns a list of models with their inference provider mappings.
    """
    api = HfApi(token=ctx.inference_router_api_key)

    models = None

    try:
        model_info = api.model_info(requested_model, expand="inferenceProviderMapping")
        models = [model_info]
    except RepositoryNotFoundError as e:
        # If model_info fails, it means the model does not exist under this exact name
        # Therefore, fall back to "search" and look for models that partially match the name
        # In Hugging Face Hub terminology Repository = Model / Dataset / Space.
        pass
    except Exception as e:
        # for the rest of the errors, we will raise an error
        raise RuntimeError(
            f"Error while getting model_info for {requested_model}: {str(e)}"
        )

    # If inference_provider is specified, search by inference provider
    # We will use "search" instead of "filter" because only search allows searching inside the model name
    # TODO: Add more filtering options e.g. by number of parameters, so that we do not have to retrieve so many models
    # TODO: We need to retrieve >1 model because "search" returns a full text match in both model IDs and Descriptions

    if models is None:
        if ctx.inference_provider is not None:
            models = api.list_models(
                search=f"{requested_model}",
                # filter=f"inference_provider:{ctx.inference_provider}",
                # this is supposed to work in recent HF versions, but it doesn't work for me
                # we will do the filtering manually below
                expand="inferenceProviderMapping",
                limit=20,
            )
        else:
            models = api.list_models(
                search=f"{requested_model}", expand="inferenceProviderMapping", limit=20
            )

    # Create a list of models with their inference provider mappings
    model_list = []
    try:
        for model in models:
            # Handle the case where inference_provider_mapping might be None or empty
            inference_provider_mapping = (
                getattr(model, "inference_provider_mapping", []) or []
            )

            model_info = {
                "model_name": model.id,
                "inference_provider_mapping": inference_provider_mapping,
            }

            # If inference_provider is specified, only add models that support it
            if ctx.inference_provider is not None:
                if ctx.inference_provider not in [
                    mapping.provider for mapping in inference_provider_mapping
                ]:
                    continue

            # Check that requested_model is partially contained in model.id
            if normalize_model_family(requested_model) not in normalize_model_family(
                model.id
            ):
                continue

            model_list.append(model_info)
    except Exception as e:
        raise RuntimeError(f"Error while iterating: {str(e)}")

    if not model_list:
        raise ValueError(
            f"No models found with name {requested_model} on Hugging Face Hub"
        )

    return model_list[0]["model_name"]


class Llm:
    """
    This class provides a unified interface for interacting with language models through
    different inference providers (e.g. Ollama for local inference, Hugging Face Hub for remote).
    It abstracts away model name resolution, inference provider selection, and local/remote inference API differences
    to provide a consistent interface for text generation tasks.

    The class supports both chat-based interactions (similar to OpenAI Chat Completions API)
    and simple prompt-based interactions (similar to legacy OpenAI Completions API).

    This class is typically instantiated through the llms() factory function rather than
    directly.

    Attributes:
        context (TowerContext): The Tower context containing configuration and settings.
        requested_model_name (str): The original model name requested by the user.
        model_name (str): The resolved model name after provider-specific resolution.
        max_tokens (int): Maximum number of tokens to generate in responses.
        inference_router (str): The inference router to use (e.g., "ollama", "hugging_face_hub").
        inference_provider (str): The inference provider (same as router when in local mode).
        inference_router_api_key (str): API key for the inference router if required.

    Example:
        # Create an Llm instance (typically done via the llms() factory function)
        llm = tower.llms("llama3.2", max_tokens=1000)

        # Use for chat completions
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
        response = llm.complete_chat(messages)

        # Use for simple prompts
        response = llm.prompt("What is the capital of France?")

    """

    def __init__(self, context: TowerContext, model_name: str, max_tokens: int = 1000):
        """
        Wraps up interfacing with a language model in the Tower system.
        """
        self.requested_model_name = model_name
        self.max_tokens = max_tokens
        self.context = context

        self.inference_router = context.inference_router
        self.inference_router_api_key = context.inference_router_api_key
        self.inference_provider = context.inference_provider

        if self.inference_router is None and self.context.is_local():
            self.inference_router = "ollama"

        # for local routers, the service is also the router
        if self.inference_router in LOCAL_INFERENCE_ROUTERS:
            self.inference_provider = self.inference_router

        # Check that we know this router. This will also check that router was set when not in local mode.
        if context.inference_router not in INFERENCE_ROUTERS:
            raise ValueError(
                f"Inference router {context.inference_router} not supported."
            )

        self.model_name = resolve_model_name(self.context, self.requested_model_name)

    def complete_chat(
        self, messages: List, **kwargs
    ) -> Union[str, ChatResponse, ChatCompletionOutput]:
        """
        Mimics the OpenAI Chat Completions API by sending a list of messages to the language model
        and returning the generated response.

        This function provides a unified interface for chat-based interactions with different
        language model providers (Ollama, Hugging Face Hub, etc.) while maintaining compatibility
        with the OpenAI Chat Completions API format.

        Args:
            messages: A list of message dictionaries, each containing 'role' and 'content' keys.
                     Follows the OpenAI Chat Completions API message format.
            **kwargs: Additional parameters to pass to the underlying chat completion API.
                     Common parameters include:
                     - tools: List of tool definitions for function calling
                     - tool_choice: Control which tool to use
                     - temperature: Sampling temperature
                     - top_p: Nucleus sampling parameter

        Returns:
            Union[str, ChatResponse, ChatCompletionOutput]: The generated response from the language model.
            Returns a string when no tools are used, or the full response object when tools are involved.

        Example:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ]
            response = llm.complete_chat(messages)

            # With tools
            tools = [{"type": "function", "function": {...}}]
            response = llm.complete_chat(messages, tools=tools)
        """

        if self.inference_router == "ollama":
            # Use Ollama for local inference
            response = complete_chat_with_ollama(
                ctx=self.context, model=self.model_name, messages=messages, **kwargs
            )
        elif self.inference_router == "hugging_face_hub":
            # Set max_tokens in kwargs if not already present
            if "max_tokens" not in kwargs:
                kwargs["max_tokens"] = self.max_tokens
            response = complete_chat_with_hugging_face_hub(
                ctx=self.context,
                model=self.model_name,
                messages=messages,
                **kwargs,
            )

        return response

    def prompt(self, prompt: str) -> str:
        """
        Mimics the old-style OpenAI Completions API (not Chat Completions!) by sending a single prompt string
        to the language model and returning the generated response.

        This function provides a simple interface for single-prompt interactions, similar to the
        legacy OpenAI /v1/completions endpoint. It internally converts the prompt to a chat message
        format and uses the complete_chat method.

        Args:
            prompt: A single string containing the prompt to send to the language model.

        Returns:
            str: The generated response from the language model.

        Example:
            response = llm.prompt("What is the capital of France?")
        """
        return self.complete_chat(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )


def llms(model_name: str, max_tokens: int = 1000) -> Llm:
    """
    This factory function creates an Llm instance configured with the specified model parameters.
    It automatically resolves the model name based on the available inference providers
    (Ollama for local inference, Hugging Face Hub for remote).
    The max_tokens parameter is used to set the maximum number of tokens to generate in responses.

    Args:
        model_name: Can be a model family name (e.g., "llama3.2", "gemma3.2", "deepseek-r1")
                    or a specific model identifier (e.g., "deepseek-r1:14b", "deepseek-ai/DeepSeek-R1-0528").
                    The function will automatically resolve the exact model name based on
                    available models in the configured inference provider.
        max_tokens: Maximum number of tokens to generate in responses. Defaults to 1000.

    Returns:
        Llm: A configured language model instance that can be used for text generation,
             chat completions, and other language model interactions.

    Raises:
        ValueError: If the configured inference router is not supported or if the model
                   cannot be resolved.

    Example:
        # Create a language model instance
        llm = llms("llama3.2", max_tokens=500)

        # Use for chat completions
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
        response = llm.complete_chat(messages)

    """
    ctx = TowerContext.build()
    return Llm(context=ctx, model_name=model_name, max_tokens=max_tokens)


def extract_ollama_message(resp: ChatResponse) -> str:
    return resp.message.content


def extract_hugging_face_hub_message(resp: ChatCompletionOutput) -> str:
    return resp.choices[0].message.content


def complete_chat_with_ollama(
    ctx: TowerContext, model: str, messages: list, is_retry: bool = False, **kwargs
) -> Union[str, ChatResponse]:

    # TODO: remove the try/except and don't pull the model if it doesn't exist. sso 7/20/25
    # the except code is not reachable right now because we always call this function with a model that exists
    try:
        response: ChatResponse = chat(model=model, messages=messages, **kwargs)
        # If tools were used, return the full response object so caller can access tool_calls
        if kwargs.get("tools") is not None:
            return response
        return extract_ollama_message(response)
    except ResponseError as e:
        if e.status_code == 404 and not is_retry:
            # Assume the model doesn't exist. We pull it, which once it exists
            # (or if it exists) will start it for us.
            pull(model=model)

            # Retry the inference after the model has been pulled.
            return complete_chat_with_ollama(
                ctx, model, messages, is_retry=True, **kwargs
            )

        # Couldn't figure out what the error was, so we'll just raise it accordingly.
        raise e


def complete_chat_with_hugging_face_hub(
    ctx: TowerContext, model: str, messages: List, **kwargs
) -> Union[str, ChatCompletionOutput]:
    """
    Uses the Hugging Face Hub API to perform inference. Will use configuration
    supplied by the environment to determine which client to connect to and all
    that.
    """
    client = InferenceClient(
        provider=ctx.inference_provider, api_key=ctx.inference_router_api_key
    )

    # Extract max_tokens separately since we set a default
    max_tokens = kwargs.pop("max_tokens", 1000)

    completion = client.chat_completion(
        messages, model=model, max_tokens=max_tokens, **kwargs
    )

    # If tools were used, return the full response object so caller can access tool_calls
    if kwargs.get("tools") is not None:
        return completion
    return extract_hugging_face_hub_message(completion)


# TODO: add this back in when implementing memory checking for LLMs
# def get_available_memory() -> dict:
#     """
#     Get available system memory information.
#     Returns a dictionary containing:
#     - total: total physical memory in bytes
#     - available: available memory in bytes
#     - used: used memory in bytes
#     - percent: memory usage percentage
#     """
#     try:
#         memory = psutil.virtual_memory()
#         return {
#             'total': memory.total,
#             'available': memory.available,
#             'used': memory.used,
#             'percent': memory.percent
#         }
#     except Exception as e:
#         raise RuntimeError(f"Failed to get memory information: {str(e)}")
