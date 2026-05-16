import requests
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from app.services.ai_providers import get_provider, PROVIDER_REGISTRY
from app.services.ai_providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

PROVIDER_DISPLAY_INFO = {
    'minimax': {'name': 'CAIgpt 云端版 (Minimax)', 'type': 'cloud', 'description': 'Minimax M2.7 云端大模型，稳定可靠'},
    'ollama': {'name': 'CAIgpt 本地版 (Ollama)', 'type': 'local', 'description': '本地 qwen3:8b 模型，隐私安全，无需联网'},
    'qwen': {'name': '通义千问', 'type': 'cloud', 'description': '阿里云大模型'},
}


class _ProviderMetrics:
    """记录每个Provider的性能指标，用于自适应选择"""

    def __init__(self):
        self._lock = threading.RLock()
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def record(self, provider_name: str, success: bool, latency: float):
        with self._lock:
            if provider_name not in self._metrics:
                self._metrics[provider_name] = {
                    'total_requests': 0,
                    'success_count': 0,
                    'total_latency': 0.0,
                    'last_success_time': 0.0,
                    'consecutive_failures': 0,
                }
            m = self._metrics[provider_name]
            m['total_requests'] += 1
            m['total_latency'] += latency
            if success:
                m['success_count'] += 1
                m['last_success_time'] = time.time()
                m['consecutive_failures'] = 0
            else:
                m['consecutive_failures'] += 1

    def get_score(self, provider_name: str) -> float:
        with self._lock:
            m = self._metrics.get(provider_name)
            if not m or m['total_requests'] == 0:
                return 50.0

            success_rate = m['success_count'] / m['total_requests']
            avg_latency = m['total_latency'] / m['total_requests']

            latency_score = max(0, 100 - avg_latency * 2)
            success_score = success_rate * 100
            recency_score = 0
            if m['last_success_time'] > 0:
                elapsed = time.time() - m['last_success_time']
                recency_score = max(0, 100 - elapsed / 60)

            penalty = m['consecutive_failures'] * 20

            score = success_score * 0.5 + latency_score * 0.3 + recency_score * 0.2 - penalty
            return max(0, min(100, score))

    def get_all_scores(self) -> Dict[str, float]:
        with self._lock:
            return {name: self.get_score(name) for name in self._metrics}


_metrics = _ProviderMetrics()


class ProviderManager:
    """
    多 AI Provider 管理器

    功能：
    - 管理多个 AI Provider 实例
    - 支持手动切换和自动降级
    - 自适应负载选择（AdaptiveProvider）
    - 健康检查（检测 Provider 是否在线）
    - 线程安全的 Provider 缓存

    设计模式：
    - Singleton：ProviderManager.get_instance() 单例模式
    - Factory：get_provider() 工厂模式创建Provider
    - Strategy：switch_provider() 运行时策略切换
    - Adaptive：get_active_provider() 自适应负载选择

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
        """更新配置并清除缓存的 provider 实例（确保使用最新配置）"""
        new_config = dict(config) if config else {}
        config_changed = (new_config != self._config)
        self._config = new_config
        if config_changed and self._providers:
            logger.info(f"Config updated, clearing {len(self._providers)} cached provider(s)")
            self._providers.clear()

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

        if provider is None:
            provider = self.adaptive_select()

        return provider

    def switch_provider(self, name: str) -> bool:
        if name not in PROVIDER_REGISTRY:
            logger.error(f"Unknown provider: {name}")
            return False

        if name in self._providers:
            del self._providers[name]

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
            fallback_order = fallback_order[idx + 1:]
        else:
            fallback_order = [p for p in fallback_order if p != current_name]

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

    def adaptive_select(self) -> Optional[BaseAIProvider]:
        """
        AdaptiveProvider：根据历史性能指标自适应选择最优Provider
        综合考虑：成功率、平均延迟、最近可用时间、连续失败次数
        """
        scores = _metrics.get_all_scores()
        if not scores:
            return None

        healthy_providers = []
        for name in PROVIDER_REGISTRY:
            if self.check_health(name):
                score = scores.get(name, 50.0)
                healthy_providers.append((name, score))

        if not healthy_providers:
            logger.warning("No healthy providers for adaptive selection")
            return None

        healthy_providers.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = healthy_providers[0]

        logger.info(f"Adaptive selection chose '{best_name}' with score {best_score:.1f}")
        self._active_provider_name = best_name
        return self.get_provider(best_name)

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
        scores = _metrics.get_all_scores()
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
                'score': round(scores.get(name, 50.0), 1),
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
            model_name = self._config.get('OLLAMA_MODEL', 'qwen3:8b')
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
        start_time = time.time()
        try:
            result = provider.chat(messages, **kwargs)
            latency = time.time() - start_time
            _metrics.record(self.get_active_provider_name(), success=True, latency=latency)
            return result
        except Exception as e:
            latency = time.time() - start_time
            _metrics.record(self.get_active_provider_name(), success=False, latency=latency)
            raise

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
