from .base import BaseAIProvider
from .ollama_provider import OllamaProvider
from .qwen_provider import QwenProvider

__all__ = ['BaseAIProvider', 'OllamaProvider', 'QwenProvider']


def get_provider(provider_name: str, config: Dict) -> BaseAIProvider:
    """Factory function to get AI provider instance"""
    providers = {
        'ollama': OllamaProvider,
        'caigpt': OllamaProvider,
        'qwen': QwenProvider,
        'tongyi': QwenProvider,
        'dashscope': QwenProvider,
    }

    provider_class = providers.get(provider_name.lower())

    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    return provider_class(config)
