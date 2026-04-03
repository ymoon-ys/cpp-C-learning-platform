import requests
import json
from typing import Optional, Dict, Any, List, Generator
from flask import current_app
from .base import BaseAIProvider
import logging

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Ollama local model provider (for CAIgpt)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = current_app.config.get('OLLAMA_MODEL', 'qwen3-coder:30b')
        self.timeout = current_app.config.get('OLLAMA_TIMEOUT', 120)

    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Non-streaming chat with Ollama"""
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                error_msg = f"Ollama API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.Timeout:
            raise TimeoutError("Ollama request timeout")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            logger.error(f"Ollama chat error: {str(e)}")
            raise

    def chat_stream(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """Streaming chat with Ollama - yields content chunks"""
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }

        response = requests.post(url, json=payload, timeout=self.timeout, stream=True)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line.decode('utf-8'))

                        if 'message' in chunk_data and 'content' in chunk_data['message']:
                            yield chunk_data['message']['content']

                        if chunk_data.get('done', False):
                            break

                    except json.JSONDecodeError:
                        continue
        else:
            error_msg = f"Ollama stream error: {response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        """Analyze code using Ollama"""
        messages = [{
            'role': 'user',
            'content': f"{context}\n\n请分析以下C++代码，指出问题并提供改进建议：\n\n```cpp\n{code}\n```"
        }]

        return self.chat(messages)
