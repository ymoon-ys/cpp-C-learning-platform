import requests
import json
from typing import Optional, Dict, Any, List, Generator
from .base import BaseAIProvider
import logging
import os

logger = logging.getLogger(__name__)


class QwenProvider(BaseAIProvider):
    """通义千问（阿里云）Provider - 使用 OpenAI 兼容格式"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model = config.get('model', 'qwen-turbo')
        self.timeout = int(config.get('timeout', '120'))

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Non-streaming chat with Qwen"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                error_msg = f"Qwen API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.Timeout:
            raise TimeoutError("Qwen request timeout")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Qwen at {self.base_url}")
        except Exception as e:
            logger.error(f"Qwen chat error: {str(e)}")
            raise

    def chat_stream(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """Streaming chat with Qwen - yields content chunks"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }

        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            stream=True
        )

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data_str)

                            if ('choices' in chunk_data and 
                                len(chunk_data['choices']) > 0 and 
                                'delta' in chunk_data['choices'][0] and 
                                'content' in chunk_data['choices'][0]['delta']):
                                
                                yield chunk_data['choices'][0]['delta']['content']

                        except json.JSONDecodeError:
                            continue
        else:
            error_msg = f"Qwen stream error: {response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        """Analyze code using Qwen"""
        messages = [{
            'role': 'system',
            'content': '你是一个专业的C++编程助手，擅长分析代码、找出问题并提供改进建议。请用中文回答。'
        }, {
            'role': 'user',
            'content': f"{context}\n\n请分析以下C++代码，指出问题并提供改进建议：\n\n```cpp\n{code}\n```"
        }]

        return self.chat(messages)
