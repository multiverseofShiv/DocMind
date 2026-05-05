from __future__ import annotations
from functools import lru_cache
import tiktoken

_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.005, "output": 0.025},
    "llama3-8b-groq": {"input": 0.00005, "output": 0.00008},
    "llama3-70b-groq": {"input": 0.00059, "output": 0.00079},
    "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
    "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "llama-3-groq-8b-tool-use": {"input": 0.00006, "output": 0.00009},
    "llama-3-groq-70b-tool-use": {"input": 0.00065, "output": 0.00085},
}

_DEFAULT_PRICE = {"input": 0.0, "output": 0.0}

@lru_cache(maxsize=4)
def _get_encoder(encoding_name: str = "cl100k_base"):
    return tiktoken.get_encoding(encoding_name)

def count_tokens(text: str, model: str = "llama-3.1-8b-instant") -> int:
    if not text:
        return 0
    try:
        # tiktoken only natively supports OpenAI model names
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for Llama/Claude models to the standard OpenAI encoding
        enc = _get_encoder("cl100k_base")
    
    # FIX: disallowed_special=() prevents crashes when the LLM output 
    # contains strings like <|endoftext|>
    return len(enc.encode(text, disallowed_special=()))


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    price = _PRICING.get(model, _DEFAULT_PRICE)
    # Most providers price per 1,000 tokens (which your math reflects)
    # Note: If your prices in _PRICING are per 1M tokens, change 1000 to 1000000
    return (input_tokens / 1000) * price["input"] + (output_tokens / 1000) * price["output"]