from .base import BaseAIProvider
from .ollama_provider import OllamaProvider

__all__ = ['BaseAIProvider', 'OllamaProvider']


def get_provider(provider_name: str, config: Dict) -> BaseAIProvider:
    """Factory function to get AI provider instance"""
    providers = {
        'ollama': OllamaProvider,
        'caigpt': OllamaProvider,
    }

    provider_class = providers.get(provider_name.lower())

    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    return provider_class(config)
