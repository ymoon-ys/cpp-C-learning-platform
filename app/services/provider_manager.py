import requests
import logging
import threading
from typing import Dict, List, Optional, Any
from app.services.ai_providers import get_provider, PROVIDER_REGISTRY
from app.services.ai_providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

PROVIDER_DISPLAY_INFO = {
    'minimax': {'name': 'CAIgpt 云端版 (Minimax)', 'type': 'cloud', 'description': 'Minimax M2.7 云端大模型，稳定可靠'},
    'ollama': {'name': 'CAIgpt 本地版 (Ollama)', 'type': 'local', 'description': '本地 qwen3:8b 模型，隐私安全，无需联网'},
    'qwen': {'name': '通义千问', 'type': 'cloud', 'description': '阿里云大模型'},
}


class ProviderManager:
    """
    多 AI Provider 管理器

    功能：
    - 管理多个 AI Provider 实例
    - 支持手动切换和自动降级
    - 健康检查（检测 Provider 是否在线）
    - 线程安全的 Provider 缓存

    注意：此管理器不依赖 Flask current_app，所有配置通过参数传入
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._active_provider_name: Optional[str] = None
        self._config: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> 'ProviderManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ProviderManager()
        return cls._instance

    def update_config(self, config: Dict[str, Any]):
        """更新配置（应在请求上下文中调用）"""
        self._config = dict(config) if config else {}

    def _create_provider(self, name: str) -> Optional[BaseAIProvider]:
        try:
            provider = get_provider(name, self._config)
            self._providers[name] = provider
            return provider
        except Exception as e:
            logger.error(f"Failed to create provider '{name}': {e}")
            return None

    def get_provider(self, name: str = None) -> Optional[BaseAIProvider]:
        if name is None:
            name = self.get_active_provider_name()

        if name in self._providers:
            return self._providers[name]

        provider = self._create_provider(name)
        return provider

    def get_active_provider_name(self) -> str:
        if self._active_provider_name:
            return self._active_provider_name
        return self._config.get('AI_PROVIDER', 'minimax').lower()

    def get_active_provider(self) -> Optional[BaseAIProvider]:
        name = self.get_active_provider_name()
        provider = self.get_provider(name)

        if provider is None and self._config.get('AI_FALLBACK_ENABLED', True):
            provider = self.auto_fallback()

        return provider

    def switch_provider(self, name: str) -> bool:
        if name not in PROVIDER_REGISTRY:
            logger.error(f"Unknown provider: {name}")
            return False

        provider = self.get_provider(name)
        if provider is None:
            logger.error(f"Failed to initialize provider: {name}")
            return False

        self._active_provider_name = name
        logger.info(f"Switched active provider to: {name}")
        return True

    def auto_fallback(self) -> Optional[BaseAIProvider]:
        fallback_order_str = self._config.get('AI_FALLBACK_ORDER', 'minimax,ollama,qwen')
        fallback_order = [p.strip() for p in fallback_order_str.split(',')]

        current_name = self.get_active_provider_name()
        if current_name in fallback_order:
            idx = fallback_order.index(current_name)
            fallback_order = fallback_order[idx + 1:] + fallback_order[:idx]

        for name in fallback_order:
            try:
                provider = self.get_provider(name)
                if provider and self.check_health(name):
                    logger.info(f"Auto fallback to provider: {name}")
                    self._active_provider_name = name
                    return provider
            except Exception as e:
                logger.warning(f"Provider '{name}' fallback failed: {e}")
                continue

        logger.error("All providers failed in auto fallback")
        return None

    def check_health(self, name: str) -> bool:
        if name == 'ollama':
            return self._check_ollama_health()
        elif name == 'minimax':
            return bool(self._config.get('MINIMAX_API_KEY', ''))
        elif name == 'qwen':
            return bool(self._config.get('QWEN_API_KEY', ''))
        return False

    def _check_ollama_health(self) -> bool:
        try:
            base_url = self._config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_providers(self) -> List[Dict[str, Any]]:
        result = []
        for name, info in PROVIDER_DISPLAY_INFO.items():
            is_active = (name == self.get_active_provider_name())
            is_healthy = self.check_health(name)
            result.append({
                'key': name,
                'name': info['name'],
                'type': info['type'],
                'description': info['description'],
                'is_active': is_active,
                'is_healthy': is_healthy,
                'available': is_healthy,
            })
        return result

    def get_current_model_info(self) -> Dict[str, Any]:
        name = self.get_active_provider_name()
        info = PROVIDER_DISPLAY_INFO.get(name, {'name': name, 'type': 'unknown', 'description': ''})
        is_healthy = self.check_health(name)

        model_name = ''
        if name == 'minimax':
            model_name = self._config.get('MINIMAX_MODEL', 'MiniMax-M2.7')
        elif name == 'ollama':
            model_name = self._config.get('OLLAMA_MODEL', 'qwen3-coder:30b')
        elif name == 'qwen':
            model_name = self._config.get('QWEN_MODEL', 'qwen-turbo')

        return {
            'provider': name,
            'name': info['name'],
            'model': model_name,
            'type': info['type'],
            'description': info['description'],
            'is_healthy': is_healthy,
        }

    def chat(self, messages: List[Dict], **kwargs) -> str:
        provider = self.get_active_provider()
        if provider is None:
            raise Exception("No available AI provider")
        return provider.chat(messages, **kwargs)

    def chat_stream(self, messages: List[Dict], **kwargs):
        provider = self.get_active_provider()
        if provider is None:
            raise Exception("No available AI provider")
        return provider.chat_stream(messages, **kwargs)

    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        provider = self.get_active_provider()
        if provider is None:
            raise Exception("No available AI provider")
        return provider.analyze_code(code, context, **kwargs)
