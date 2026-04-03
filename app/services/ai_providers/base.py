from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.api_url = config.get('api_url', '')
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', '')

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat messages and return response"""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[Dict], **kwargs):
        """Stream chat responses (yield chunks)"""
        pass

    @abstractmethod
    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        """Analyze code and return suggestions"""
        pass

    def build_system_prompt(self, base_prompt: str, user_context: Dict = None) -> str:
        """Build system prompt with optional context injection"""
        prompt = base_prompt

        if user_context:
            if user_context.get('problem'):
                problem = user_context['problem']
                prompt += f"\n\n## 当前题目\n{problem.get('title', '')}\n{problem.get('description', '')}"

            if user_context.get('user_level'):
                prompt += f"\n\n## 学生水平\n该学生的C++水平：{user_context['user_level']}"

        return prompt

    def handle_error(self, error: Exception, default_message: str = "AI service error") -> str:
        """Handle and log errors consistently"""
        logger.error(f"{self.name} error: {str(error)}")

        if isinstance(error, TimeoutError):
            return f"{self.name} request timeout. Please try again."
        elif isinstance(error, ConnectionError):
            return f"Cannot connect to {self.name} service."
        else:
            return f"{default_message}: {str(error)}"
