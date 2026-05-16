import requests
import json
import re
from typing import Optional, Dict, Any, List, Generator
from .base import BaseAIProvider
import logging

logger = logging.getLogger(__name__)

THINK_START = '\u003cthink\u003e'
THINK_END = '\u003c/think\u003e'


class MinimaxProvider(BaseAIProvider):
    """Minimax API provider - OpenAI compatible format"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('MINIMAX_API_KEY', '')
        self.base_url = config.get('MINIMAX_BASE_URL', 'https://api.minimaxi.com/v1')
        self.model = config.get('MINIMAX_MODEL', 'MiniMax-M2.7')
        self.timeout = int(config.get('MINIMAX_TIMEOUT', '120'))

        if not self.api_key:
            logger.error("MinimaxProvider initialized with EMPTY API key! Check MINIMAX_API_KEY in .env")
        else:
            logger.info(f"MinimaxProvider initialized with API key prefix: {self.api_key[:8]}...")

    def _strip_thinking(self, text: str) -> str:
        text = re.sub(re.escape(THINK_START) + r'.*?' + re.escape(THINK_END), '', text, flags=re.DOTALL)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _handle_auth_error(self, status_code: int, response_text: str):
        if status_code == 401:
            key_hint = f"{self.api_key[:8]}..." if self.api_key else "EMPTY"
            logger.error(
                f"Minimax 401 Authentication failed! "
                f"API key hint: {key_hint}, Key length: {len(self.api_key)}, "
                f"Response: {response_text[:300]}"
            )
            raise Exception(
                f"Minimax \u8ba4\u8bc1\u5931\u8d25 (401)\u3002\u8bf7\u68c0\u67e5 .env \u6587\u4ef6\u4e2d\u7684 MINIMAX_API_KEY \u662f\u5426\u6b63\u786e\u3002"
                f"\u5f53\u524d Key \u524d\u7f00: {key_hint}"
            )
        elif status_code == 403:
            logger.error(f"Minimax 403 Forbidden: {response_text[:300]}")
            raise Exception(f"Minimax \u8bbf\u95ee\u88ab\u62d2\u7edd (403): {response_text[:200]}")
        elif status_code == 429:
            logger.warning(f"Minimax 429 Rate limited: {response_text[:200]}")
            raise Exception("Minimax \u8bf7\u6c42\u9891\u7387\u8d85\u9650 (429)\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5")
        else:
            error_msg = f"Minimax API returned status {status_code}: {response_text[:300]}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def chat(self, messages: List[Dict], **kwargs) -> str:
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
                content = result['choices'][0]['message']['content']
                return self._strip_thinking(content)
            else:
                self._handle_auth_error(response.status_code, response.text)

        except requests.Timeout:
            raise TimeoutError("Minimax request timeout")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Minimax at {self.base_url}")

    def chat_stream(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
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
            in_thinking = False
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
                                'delta' in chunk_data['choices'][0]):

                                delta = chunk_data['choices'][0]['delta']

                                if 'reasoning_content' in delta and delta['reasoning_content']:
                                    continue

                                if 'content' in delta and delta['content']:
                                    content = delta['content']

                                    if THINK_START in content:
                                        in_thinking = True
                                        before = content.split(THINK_START)[0]
                                        if before.strip():
                                            yield before
                                        continue

                                    if THINK_END in content:
                                        in_thinking = False
                                        after = content.split(THINK_END)[-1]
                                        if after.strip():
                                            yield after
                                        continue

                                    if not in_thinking:
                                        yield content

                        except json.JSONDecodeError:
                            continue
        else:
            self._handle_auth_error(response.status_code, response.text)

    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        messages = [{
            'role': 'system',
            'content': '\u4f60\u662f\u4e00\u4e2a\u4e13\u4e1a\u7684C++\u7f16\u7a0b\u52a9\u624b\uff0c\u64c5\u957f\u5206\u6790\u4ee3\u7801\u3001\u627e\u51fa\u95ee\u9898\u5e76\u63d0\u4f9b\u6539\u8fdb\u5efa\u8bae\u3002\u8bf7\u7528\u4e2d\u6587\u56de\u7b54\u3002'
        }, {
            'role': 'user',
            'content': f"{context}\n\n\u8bf7\u5206\u6790\u4ee5\u4e0bC++\u4ee3\u7801\uff0c\u6307\u51fa\u95ee\u9898\u5e76\u63d0\u4f9b\u6539\u8fdb\u5efa\u8bae\uff1a\n\n```cpp\n{code}\n```"
        }]

        return self.chat(messages)
