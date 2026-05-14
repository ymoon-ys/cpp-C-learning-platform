from .base import BaseAIProvider
from .ollama_provider import OllamaProvider
from .qwen_provider import QwenProvider
from .minimax_provider import MinimaxProvider

__all__ = ['BaseAIProvider', 'OllamaProvider', 'QwenProvider', 'MinimaxProvider']

PROVIDER_REGISTRY = {
    'ollama': OllamaProvider,
    'caigpt': OllamaProvider,
    'qwen': QwenProvider,
    'tongyi': QwenProvider,
    'dashscope': QwenProvider,
    'minimax': MinimaxProvider,
}


def get_provider(provider_name: str, config: dict = None) -> BaseAIProvider:
    """Factory function to get AI provider instance"""
    provider_class = PROVIDER_REGISTRY.get(provider_name.lower())

    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    return provider_class(config or {})
