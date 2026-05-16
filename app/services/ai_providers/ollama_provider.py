import requests
import json
import re
from typing import Optional, Dict, Any, List, Generator
from .base import BaseAIProvider
import logging

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Ollama local model provider (for CAIgpt)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = config.get('OLLAMA_MODEL', 'qwen3:8b')
        self.teaching_mode = config.get('OLLAMA_TEACHING_MODE', 'true').lower() == 'true'

    def _filter_teaching_response(self, text: str) -> str:
        """Filter out code blocks and C++ syntax from teaching mode responses"""
        if not self.teaching_mode:
            return text

        has_code_block = bool(re.search(r'```\s*(?:cpp|c\+\+|c|python|java)?', text))

        code_line_count = 0
        code_line_patterns = [
            r'^\s*(int|float|double|char|bool|void|string|long|short|unsigned|auto|const|static)\s+\w+.*?[;{]\s*$',
            r'^\s*(cin|cout|cerr|std::)\s*.{0,80}[;]\s*$',
            r'^\s*(if|else|for|while|do|switch|case|return|break|continue)\s*[\(].*?[;{}]\s*$',
            r'^\s*(#include|#define|#pragma)\s+.*$',
            r'^\s*using\s+(namespace|std)\s+.*$',
            r'^\s*\w+\s*=\s*.*[;]\s*$',
        ]
        for line in text.split('\n'):
            for pattern in code_line_patterns:
                if re.match(pattern, line.strip()):
                    code_line_count += 1
                    break

        if has_code_block or code_line_count >= 3:
            first_question = ''
            for line in text.split('\n'):
                stripped = line.strip()
                if stripped.endswith(('？', '?')) and len(stripped) > 5:
                    first_question = stripped
                    break

            if first_question:
                return first_question + '\n\n先自己想想，我等你的思路！'
            else:
                return "这个问题很好！你能先用自己的话描述一下你的思路吗？我们先理清逻辑，再考虑怎么实现。"

        text = re.sub(r'```\s*\n.*?```', '', text, flags=re.DOTALL)

        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            is_code = False
            for pattern in code_line_patterns:
                if re.match(pattern, line.strip()):
                    is_code = True
                    break
            if not is_code:
                filtered_lines.append(line)

        text = '\n'.join(filtered_lines)

        text = re.sub(r'(你需要用|你可以用|你应该写|可以这样写|写法如下|代码如下|示例如下)[^。\n]*[。\n]', '', text)
        text = re.sub(r'(std::)?(cin|cout|cerr|endl)\s*([<>{();,]|>>|<<)', '', text)
        text = re.sub(r'第[一二三四五六七八九十\d]+步[：:]\s*(如何|怎么|怎样)[^？?\n]*[？?\n]?', '', text)

        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'^\s*[-*]\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*###?\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()

        if not text or len(text) < 10:
            return "这个问题很好！你能先用自己的话描述一下你的思路吗？我们一起一步步来分析。"

        return text

    def _inject_no_think(self, messages: List[Dict]) -> List[Dict]:
        """Inject /no_think tag for qwen3 models to disable thinking mode"""
        result = []
        for msg in messages:
            new_msg = dict(msg)
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if '/no_think' not in content:
                    new_msg['content'] = content + ' /no_think'
            result.append(new_msg)
        return result

    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Non-streaming chat with Ollama"""
        url = f"{self.base_url}/api/chat"

        messages = self._inject_no_think(messages)

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=None)

            if response.status_code == 200:
                result = response.json()
                raw_content = result.get('message', {}).get('content', '')
                return self._filter_teaching_response(raw_content)
            else:
                error_msg = f"Ollama API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            logger.error(f"Ollama chat error: {str(e)}")
            raise

    def chat_stream(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """Streaming chat with Ollama - yields content chunks with teaching mode filtering"""
        url = f"{self.base_url}/api/chat"

        messages = self._inject_no_think(messages)

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, timeout=None, stream=True)
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")

        if response.status_code == 200:
            if not self.teaching_mode:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if 'message' in chunk_data:
                                content = chunk_data['message'].get('content', '')
                                if content:
                                    yield content
                            if chunk_data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                buffer = ""
                in_code_block = False
                code_fence_count = 0

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if 'message' in chunk_data:
                                content = chunk_data['message'].get('content', '')
                                if content:
                                    buffer += content

                                    while buffer:
                                        if in_code_block:
                                            end_idx = buffer.find('```')
                                            if end_idx != -1:
                                                buffer = buffer[end_idx + 3:]
                                                in_code_block = False
                                            else:
                                                buffer = ""
                                                break
                                        else:
                                            start_idx = buffer.find('```')
                                            if start_idx != -1:
                                                before = buffer[:start_idx]
                                                if before.strip():
                                                    filtered = self._filter_inline_code(before)
                                                    if filtered:
                                                        yield filtered
                                                buffer = buffer[start_idx + 3:]
                                                in_code_block = True
                                            else:
                                                safe_end = len(buffer)
                                                if len(buffer) > 20:
                                                    safe_end = len(buffer) - 10
                                                chunk_to_send = buffer[:safe_end]
                                                filtered = self._filter_inline_code(chunk_to_send)
                                                if filtered:
                                                    yield filtered
                                                buffer = buffer[safe_end:]

                            if chunk_data.get('done', False):
                                if buffer and not in_code_block:
                                    filtered = self._filter_inline_code(buffer)
                                    if filtered:
                                        yield filtered
                                break

                        except json.JSONDecodeError:
                            continue
        else:
            error_msg = f"Ollama stream error: {response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _filter_inline_code(self, text: str) -> str:
        """Filter individual C++ code lines from text (for streaming)"""
        code_line_patterns = [
            r'^\s*(int|float|double|char|bool|void|string|long|short|unsigned|auto|const|static)\s+\w+.*?[;{]\s*$',
            r'^\s*(cin|cout|cerr|std::)\s*.{0,80}[;]\s*$',
            r'^\s*(if|else|for|while|do|switch|case|return|break|continue)\s*[\(].*?[;{}]\s*$',
            r'^\s*(#include|#define|#pragma)\s+.*$',
            r'^\s*using\s+(namespace|std)\s+.*$',
            r'^\s*\w+\s*=\s*.*[;]\s*$',
        ]

        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            is_code = False
            for pattern in code_line_patterns:
                if re.match(pattern, line.strip()):
                    is_code = True
                    break
            if not is_code:
                filtered_lines.append(line)

        result = '\n'.join(filtered_lines)
        return result

    def analyze_code(self, code: str, context: str = '', **kwargs) -> str:
        """Analyze code using Ollama"""
        messages = [{
            'role': 'user',
            'content': f"{context}\n\n请分析以下C++代码，指出问题并提供改进建议：\n\n```cpp\n{code}\n```"
        }]

        return self.chat(messages)
