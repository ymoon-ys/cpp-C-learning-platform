import os
from dotenv import load_dotenv
load_dotenv()

print("=== 环境变量检查 ===")
env_key = os.environ.get('MINIMAX_API_KEY', '')
print(f"MINIMAX_API_KEY: {env_key[:20]}...{env_key[-10:]}" if env_key else "MINIMAX_API_KEY: (空)")
env_url = os.environ.get('MINIMAX_BASE_URL', '')
print(f"MINIMAX_BASE_URL: {env_url}")
env_model = os.environ.get('MINIMAX_MODEL', '')
print(f"MINIMAX_MODEL: {env_model}")
env_provider = os.environ.get('AI_PROVIDER', '')
print(f"AI_PROVIDER: {env_provider}")
print()

print("=== API 连接测试 ===")
import requests
headers = {
    'Authorization': f'Bearer {env_key}',
    'Content-Type': 'application/json'
}
payload = {
    "model": env_model or "MiniMax-M2.7",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 20
}
url = f"{env_url}/chat/completions" if env_url else "https://api.minimaxi.com/v1/chat/completions"
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"URL: {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        content = result['choices'][0]['message']['content']
        print(f"Response: {content[:100]}")
        print("✅ Minimax API 连接成功！")
    else:
        print(f"Error: {resp.text[:300]}")
except Exception as e:
    print(f"Connection error: {e}")
