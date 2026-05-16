from flask import Blueprint, request, jsonify, current_app, render_template, Response
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import AIConversation, Problem
from app.utils import get_consecutive_learning_days
from app.services.provider_manager import ProviderManager
from app.services.memory_service import MemoryService
import requests
import base64
import json
import os
import re
import subprocess
from PIL import Image
import logging
from datetime import datetime

ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai')

ai_limiter = Limiter(key_func=get_remote_address)


@ai_bp.route('/')
@login_required
def index():
    return render_template('ai_assistant.html',
                         consecutive_days=get_consecutive_learning_days(current_user))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_ocr_token_cache = {"access_token": None, "expires_at": 0}

_memory_service = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(get_db_connection)
        _memory_service.init_tables()
    return _memory_service


def _get_provider_manager(config_dict=None) -> ProviderManager:
    """获取 ProviderManager 实例并更新配置
    
    Args:
        config_dict: 可选，直接传入配置字典（用于流式响应等无 Flask 上下文的场景）
    """
    manager = ProviderManager.get_instance()
    if config_dict is not None:
        manager.update_config(config_dict)
    else:
        # 将 Flask config 转换为字典传入 ProviderManager
        config = {k: v for k, v in current_app.config.items() if isinstance(v, (str, int, float, bool))}
        manager.update_config(config)
    return manager


def get_ai_response(messages: list, stream: bool = False, **kwargs):
    try:
        manager = _get_provider_manager()
        if stream:
            return manager.chat_stream(messages, **kwargs)
        else:
            return manager.chat(messages, **kwargs)
    except Exception as e:
        logger.error(f"AI response error: {e}")
        raise

CAIGPT_SYSTEM_PROMPT = """你是CAIgpt，C++编程教学助手。你的核心原则：绝对不给代码，只提问引导。

【最高优先级规则】
你输出的一切内容中，不允许出现任何C++代码。包括变量声明、cin/cout、if/else、for/while、函数定义等。你只能用中文描述思路和提问。

【解题引导——6大场景】

场景1：学生问"怎么写某功能"（如"怎么判断奇偶数"）
→ 确认理解 + 提问该功能涉及的底层原理
例：你想判断奇偶数对吧？那你觉得，奇数和偶数在数学上的定义区别是什么？

场景2：学生说"不知道""没思路"
→ 拆解问题为更小的子问题，引导学生逐步推理
例：没关系，我们把问题拆开。你能先说出，什么样的数叫偶数吗？只说定义就行。

场景3：学生问"这个程序怎么开始"
→ 引导学生先描述程序的功能需求，再拆解为步骤
例：先不管代码，你能用中文描述一下这个程序需要完成什么吗？输入是什么，输出是什么？

场景4：学生给代码问"哪里错了"
→ 定位错误位置 + 指出涉及的知识点 + 提问引导修正
例：我看到了你的代码，第X行有问题。这里涉及的知识点是XXX。你回顾一下这个知识点的定义，应该怎么正确使用？

场景5：学生提交了正确的代码
→ 逐行分析代码中涉及的知识点，用规范术语列出，并追问一个延伸问题
例：你的代码逻辑是正确的。这段代码涉及以下知识点：1.变量声明与整数类型 2.取模运算（%），用于求余数 3.条件判断（if-else），根据余数是否为0分支输出。你理解了取模运算后，想想取模运算除了判断奇偶，还能用在哪些场景？

场景6：学生坚持要代码或答案
→ 重申教学原则 + 引导回思考路径
例：直接给代码你学不到东西哦！我相信你能自己写出来，我们一步步来，你先告诉我第一步该做什么？

【概念解释——最书面化优先规则】
当学生问概念（如"什么是指针""虚函数是什么"）时：
1. 第一次解释：用最书面、最学术的规范术语直接给出定义，不做任何简化或比喻
2. 如果学生表示听不懂，再逐步拆解术语，每次只降低一个理解层级
3. 仍然不给代码示例
4. 解释完后，追问一个引导性问题帮助学生深化理解

例：学生问"什么是指针"
你的回复：
指针是一种派生数据类型，其值为其所指向实体在内存中的虚拟地址。通过解引用操作可间接访问该地址处存储的数据对象。你理解了这个定义后，想想为什么程序需要通过地址间接访问数据，而非直接访问？

学生说"听不懂"
你的回复：
好，我拆开来讲。"派生数据类型"意思是它不是int、char这样的基础类型，而是从已有类型派生出来的。"虚拟地址"就是内存中每个字节的编号。所以指针这个变量里存的是一个编号，通过这个编号能找到另一个变量。你能理解"存的是编号"这个说法吗？

【学生说"不知道"时的处理规则——这是关键】
当学生回答"不知道""不会""没思路"时：
1. **绝对不能直接告诉方法或答案**
2. **绝对不能说"比如用XXX"**
3. **应该**：
   - 把问题拆解为更小的子问题
   - 引导学生从定义出发逐步推理
   - 让学生回忆已学过的相关知识
   - 用"你能先说出XXX的定义吗""我们回顾一下XXX"开头

【绝对禁止的输出——出现以下任何一种都是错误】
- int n; 或 cin >> n; 或 cout << "xxx";
- if (条件) { ... } 或 for (...) { ... }
- ```cpp 代码块
- 任何可以复制到编译器运行的文字
- **直接告诉学生方法或答案**（如"用除法余数判断""用取模运算"）
- **"比如"后面接具体方法或代码**

记住：你是引导者，不是答案提供者。每次只问一个问题，等学生思考。即使学生说不知道，也要引导他自己发现，而不是直接告诉。"""

AI_MODELS = {
    'auto': {
        'name': 'CAIgpt',
        'api_url': 'local',
        'api_key': '',
        'model': 'caigpt'
    },
    'caigpt': {
        'name': 'CAIgpt',
        'api_url': 'local',
        'api_key': '',
        'model': 'caigpt'
    },
    'minimax': {
        'name': 'Minimax M2.7',
        'api_url': 'cloud',
        'api_key': os.environ.get('MINIMAX_API_KEY', ''),
        'model': 'minimax'
    },
    'ollama': {
        'name': 'CAIgpt 本地版 (Ollama)',
        'api_url': 'local',
        'api_key': '',
        'model': 'ollama',
        'system_prompt': 'caigpt'
    },
    'qwen': {
        'name': '通义千问',
        'api_url': 'cloud',
        'api_key': os.environ.get('QWEN_API_KEY', ''),
        'model': 'qwen'
    },
    'local': {
        'name': '本地模拟',
        'api_url': '',
        'api_key': '',
        'model': 'local'
    }
}

_ai_models_cache = None

def get_ai_models():
    global _ai_models_cache, AI_MODELS
    if _ai_models_cache is not None:
        return _ai_models_cache

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT model_key, name, api_url, api_key, model, provider, is_cloud, max_tokens, temperature, is_active FROM ai_models ORDER BY sort_order')
            models = {}
            for row in cursor.fetchall():
                key = row['model_key']
                model_config = {
                    'name': row['name'],
                    'api_url': 'cloud' if row['is_cloud'] else 'local',
                    'api_key': row['api_key'] or '',
                    'model': row['provider'] or row['model_key']
                }
                if row.get('max_tokens'):
                    model_config['max_tokens'] = row['max_tokens']
                if row.get('temperature'):
                    model_config['temperature'] = float(row['temperature'])
                if not row.get('is_active', 1):
                    continue
                models[key] = model_config
            cursor.close()
            if models:
                _ai_models_cache = models
                AI_MODELS = models
                return models
        except Exception as e:
            logger.warning(f"Failed to load AI models from DB: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    _ai_models_cache = AI_MODELS
    return AI_MODELS

SYSTEM_PROMPT = """You are a C++ programming teaching assistant, helping students understand and solve programming problems.
Important rules:
1. Do not give complete code answers
2. Guide students to think, provide solution approaches and methods
3. If student provides code, point out problems and improvement suggestions
4. Answers must use C++ language
5. Encourage students to think and implement independently
6. Can provide related knowledge points and concept explanations
7. For algorithm problems, can provide algorithm thinking and complexity analysis
8. Answers should be concise and clear, avoid being too lengthy"""

def get_db_connection(db=None):
    """Get MySQL database connection"""
    try:
        if db is not None:
            conn = db.get_connection()
            return conn
        else:
            from flask import has_app_context
            if has_app_context():
                db = current_app.db
                conn = db.get_connection()
                return conn
            else:
                logger.error("Failed to connect to database: No application context")
                return None
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return None

def init_caigpt_database(db=None):
    """Initialize CAIgpt database table structure"""
    try:
        conn = get_db_connection(db)
        if not conn:
            logger.error("Cannot connect to database")
            return

        try:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS caigpt_dialog_history (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                session_id INT,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                images JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_role (role),
                INDEX idx_created_at (created_at),
                INDEX idx_user_session (user_id, session_id),
                CONSTRAINT fk_caigpt_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS caigpt_sessions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                title VARCHAR(200) DEFAULT '新对话',
                model_name VARCHAR(50) DEFAULT 'caigpt',
                problem_id INT,
                tags JSON,
                is_favorite TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS caigpt_favorites (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                session_id INT NOT NULL,
                message_id INT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_favorite (user_id, session_id, message_id),
                INDEX idx_user_id (user_id),
                CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                CONSTRAINT fk_favorites_session FOREIGN KEY (session_id) REFERENCES caigpt_sessions (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_user_preferences (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL UNIQUE,
                theme VARCHAR(20) DEFAULT 'light',
                editor_theme VARCHAR(30) DEFAULT 'vs-dark',
                editor_font_size INT DEFAULT 14,
                editor_font_family VARCHAR(100) DEFAULT "'Consolas', 'Monaco', 'Courier New', monospace",
                editor_word_wrap VARCHAR(10) DEFAULT 'on',
                minimap_enabled TINYINT DEFAULT 1,
                auto_save_enabled TINYINT DEFAULT 1,
                last_code LONGTEXT,
                last_session_id INT,
                language VARCHAR(10) DEFAULT 'cpp',
                model_preference VARCHAR(50) DEFAULT 'caigpt',
                ui_layout VARCHAR(20) DEFAULT 'split',
                console_height INT DEFAULT 200,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                CONSTRAINT fk_preferences_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            conn.commit()
            logger.info("CAIgpt database initialized successfully")

            _migrate_schema(conn)
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")

def _migrate_schema(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM caigpt_sessions LIKE 'tags'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE caigpt_sessions ADD COLUMN tags JSON")
            logger.info("Migrated: added caigpt_sessions.tags")

        cursor.execute("SHOW COLUMNS FROM caigpt_sessions LIKE 'is_favorite'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE caigpt_sessions ADD COLUMN is_favorite TINYINT DEFAULT 0")
            logger.info("Migrated: added caigpt_sessions.is_favorite")

        cursor.execute("SHOW COLUMNS FROM caigpt_dialog_history LIKE 'session_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE caigpt_dialog_history ADD COLUMN session_id INT")
            logger.info("Migrated: added caigpt_dialog_history.session_id")

        conn.commit()
    except Exception as e:
        logger.warning(f"Schema migration check failed: {e}")

def get_baidu_access_token():
    """Get Baidu OCR access token with auto-refresh on expiration"""
    from flask import current_app
    import time

    api_key = current_app.config.get('BAIDU_OCR_API_KEY', '')
    secret_key = current_app.config.get('BAIDU_OCR_SECRET_KEY', '')

    if not api_key or not secret_key:
        logger.warning("Baidu OCR API Key or Secret Key not configured")
        return None

    now = time.time()
    margin = current_app.config.get('BAIDU_OCR_TOKEN_EXPIRE_MARGIN', 86400)

    if _ocr_token_cache["access_token"] and _ocr_token_cache["expires_at"] > now + margin:
        return _ocr_token_cache["access_token"]

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    try:
        response = requests.post(url, params=params, timeout=10)
        result = response.json()
        token = result.get("access_token")
        expires_in = result.get("expires_in", 2592000)

        if token:
            _ocr_token_cache["access_token"] = token
            _ocr_token_cache["expires_at"] = now + expires_in
            logger.info("Baidu OCR access token obtained successfully")
            return token
        else:
            logger.error(f"Baidu OCR token acquisition failed: {result}")
            return None
    except Exception as e:
        logger.error(f"Failed to get Baidu OCR access token: {str(e)}")
        return None

def baidu_ocr(image_base64):
    """Use Baidu OCR to recognize image text"""
    access_token = get_baidu_access_token()
    if not access_token:
        return None, "Unable to get OCR service authorization"

    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    data = {"image": image_base64}

    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        result = response.json()

        if "words_result" in result and len(result["words_result"]) > 0:
            text = "\n".join([item["words"] for item in result["words_result"]])
            return text, None
        elif "error_msg" in result:
            return None, f"OCR recognition failed: {result['error_msg']}"
        else:
            return None, "No text recognized in image"
    except Exception as e:
        logger.error(f"Baidu OCR request failed: {str(e)}")
        return None, f"OCR service exception: {str(e)}"

def get_user_history(user_id, max_history=20):
    """Get user dialog history from database"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
        SELECT role, content, images
        FROM caigpt_dialog_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        ''', (user_id, max_history))

        history = []
        for row in cursor.fetchall():
            msg = {
                "role": row['role'],
                "content": row['content']
            }
            if row['images']:
                msg["images"] = json.loads(row['images'])
            history.append(msg)

        history.reverse()

        return history
    except Exception as e:
        logger.error(f"Failed to get dialog history: {str(e)}")
        return []
    finally:
        conn.close()

def save_message(user_id, role, content, images=None, session_id=None, max_cache=20):
    """Save message to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        images_json = json.dumps(images) if images else None

        cursor.execute('''
        INSERT INTO caigpt_dialog_history (user_id, session_id, role, content, images)
        VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, session_id, role, content, images_json))

        conn.commit()

        return True
    except Exception as e:
        logger.error(f"Failed to save message: {str(e)}")
        return False
    finally:
        conn.close()

def build_messages(user_message, history=None, user=None, problem_id=None):
    """Build message list with dynamic prompt injection (including memory)"""
    system_prompt = build_dynamic_system_prompt(user, problem_id, user_message=user_message)
    messages = [{"role": "system", "content": system_prompt}]

    if history and isinstance(history, list):
        for msg in history:
            if msg.get("role") != "system":
                messages.append(msg)

    guided_message = user_message + "\n\n【提醒】你不允许输出任何C++代码，只能用中文提问引导我思考。"
    messages.append({"role": "user", "content": guided_message})

    return messages


def build_dynamic_system_prompt(user=None, problem_id=None, user_message=''):
    """Build dynamic system prompt based on user context, problem info, and memory"""
    base_prompt = CAIGPT_SYSTEM_PROMPT
    context_parts = []

    try:
        if user and hasattr(user, 'id') and user.is_authenticated:
            from flask import current_app
            db = current_app.db

            user_submissions = db.find_by_field('submissions', 'user_id', user.id)
            total_submissions = len(user_submissions) if user_submissions else 0

            accepted_count = 0
            if user_submissions:
                for sub in user_submissions:
                    if sub.get('status') == 'AC':
                        accepted_count += 1

            if total_submissions > 0:
                success_rate = (accepted_count / total_submissions) * 100

                if success_rate >= 80:
                    level = "高级"
                    guidance = "可以深入讲解底层原理、优化技巧、设计模式等进阶内容"
                elif success_rate >= 50:
                    level = "中级"
                    guidance = "适合讲解算法思路、代码优化、常见错误等中级内容"
                else:
                    level = "初级"
                    guidance = "应该用通俗易懂的语言，多举例子，避免复杂概念"

                context_parts.append(f"""
## 学生学习水平评估
- **编程水平**：{level}
- **提交次数**：{total_submissions} 次
- **通过率**：{success_rate:.1f}%
- **教学建议**：{guidance}

请根据学生的实际水平调整回答的深度和方式。""")

            try:
                memory_svc = get_memory_service()
                memory_context = memory_svc.get_memory_context_for_prompt(user.id, user_message)
                if memory_context:
                    context_parts.append(memory_context)
            except Exception as mem_err:
                logger.warning(f"Memory injection failed: {mem_err}")

        if problem_id:
            problem = Problem.get_by_id(problem_id)
            if problem:
                context_parts.append(f"""
## 当前题目信息
- **题目名称**：{problem.title}
- **难度等级**：{problem.difficulty or '未知'}
- **输入格式**：{problem.input_format or '未指定'}
- **输出格式**：{problem.output_format or '未指定'}

注意：
1. 如果学生询问此题目的解法，**绝对不要直接给出完整代码**
2. 可以提供思路、提示、部分代码框架
3. 引导学生自己思考和实现
4. 如果学生给出了代码，重点检查逻辑和边界情况""")

        if context_parts:
            dynamic_context = "\n\n".join(context_parts)
            base_prompt += f"\n\n---\n\n## 动态上下文信息（请根据以下信息调整回答）\n\n{dynamic_context}"

    except Exception as e:
        logger.error(f"Failed to build dynamic prompt: {str(e)}")

    return base_prompt

@ai_bp.route('/models', methods=['GET'])
@login_required
def get_models():
    try:
        manager = _get_provider_manager()
        providers = manager.list_providers()
        return jsonify({'models': providers})
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        return jsonify({'models': [], 'error': str(e)})

@ai_bp.route('/chat', methods=['POST'])
@ai_limiter.limit("20 per minute")
def chat():
    data = request.get_json()

    question = data.get('question', '')
    model_name = data.get('model', 'local')
    problem_id = data.get('problem_id')
    conversation_type = data.get('type', 'general')
    has_code = data.get('has_code', False)
    has_image = data.get('has_image', False)
    image_data = data.get('image', '')

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    models = get_ai_models()
    if model_name not in models:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    model_info = models[model_name]

    if model_name != 'local':
        if not current_user.is_authenticated:
            return jsonify({'error': 'Login required to use this model'}), 401
        if model_name not in ('caigpt', 'ollama') and not model_info['api_key']:
            return jsonify({'error': f'{model_info["name"]} API key not configured'}), 400

    try:
        if model_name == 'local':
            return handle_local_chat(question, problem_id, conversation_type, has_code, has_image, image_data)
        elif model_name in ('caigpt', 'ollama', 'minimax'):
            return handle_caigpt_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data)
        elif model_name == 'gemini' or model_name == 'gemini3':
            return handle_gemini_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data)
        else:
            return handle_openai_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data)
    except requests.Timeout:
        return jsonify({'error': 'AI service request timeout'}), 504
    except Exception as e:
        return jsonify({'error': f'AI service request failed: {str(e)}'}), 500


def handle_gemini_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data):
    from flask import current_app

    contents = []

    if problem_id:
        problem = Problem.get_by_id(problem_id)
        if problem:
            problem_context = f'Current problem: {problem.title}\n\nProblem description: {problem.description}\n\nInput format: {problem.input_format}\n\nOutput format: {problem.output_format}\n\nSample input: {problem.sample_input}\n\nSample output: {problem.sample_output}'
            contents.append({'role': 'user', 'parts': [{'text': f'{SYSTEM_PROMPT}\n\n{problem_context}'}]})

    user_content = {'role': 'user', 'parts': [{'text': question}]}

    if has_image and image_data:
        user_content['parts'].append({
            'inline_data': {
                'mime_type': 'image/png',
                'data': image_data
            }
        })

    contents.append(user_content)

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2000
        }
    }

    url = f"{model_info['api_url']}?key={model_info['api_key']}"

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']

        conversation = AIConversation(
            user_id=current_user.id,
            problem_id=problem_id,
            question=question,
            answer=answer,
            model_name=model_info['name'],
            conversation_type=conversation_type,
            has_code=has_code,
            has_image=has_image
        )
        conversation.save()

        return jsonify({
            'success': True,
            'answer': answer,
            'model': model_info['name'],
            'conversation_id': conversation.id
        })
    else:
        return jsonify({'error': f'AI service returned error: {response.text}'}), 500


def handle_openai_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data):
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT}
    ]

    if problem_id:
        problem = Problem.get_by_id(problem_id)
        if problem:
            messages.append({
                'role': 'system',
                'content': f'Current problem: {problem.title}\n\nProblem description: {problem.description}\n\nInput format: {problem.input_format}\n\nOutput format: {problem.output_format}\n\nSample input: {problem.sample_input}\n\nSample output: {problem.sample_output}'
            })

    messages.append({'role': 'user', 'content': question})

    if has_image and image_data:
        try:
            messages.append({
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'Please analyze the code or problem in this image'},
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{image_data}'}}
                ]
            })
        except Exception as e:
            import logging
            logging.warning(f"Image processing failed: {e}")

    headers = {
        'Authorization': f'Bearer {model_info["api_key"]}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': model_info['model'],
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 2000
    }

    response = requests.post(
        model_info['api_url'],
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']

        conversation = AIConversation(
            user_id=current_user.id,
            problem_id=problem_id,
            question=question,
            answer=answer,
            model_name=model_info['name'],
            conversation_type=conversation_type,
            has_code=has_code,
            has_image=has_image
        )
        conversation.save()

        return jsonify({
            'success': True,
            'answer': answer,
            'model': model_info['name'],
            'conversation_id': conversation.id
        })
    else:
        return jsonify({'error': f'AI service returned error: {response.text}'}), 500

@ai_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    limit = request.args.get('limit', 20, type=int)
    problem_id = request.args.get('problem_id', type=int)

    if problem_id:
        conversations = AIConversation.get_by_problem(current_user.id, problem_id)
    else:
        conversations = AIConversation.get_by_user(current_user.id, limit)

    return jsonify({
        'conversations': [
            {
                'id': conv.id,
                'question': conv.question,
                'answer': conv.answer,
                'model_name': conv.model_name,
                'conversation_type': conv.conversation_type,
                'has_code': conv.has_code,
                'has_image': conv.has_image,
                'created_at': conv.created_at
            }
            for conv in conversations
        ]
    })

@ai_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    conversation = AIConversation.get_by_id(conversation_id)

    if not conversation:
        return jsonify({'error': 'Conversation record does not exist'}), 404

    if conversation.user_id != current_user.id:
        return jsonify({'error': 'No permission to delete this conversation record'}), 403

    conversation.delete()
    return jsonify({'success': True})

@ai_bp.route('/conversations/clear', methods=['POST'])
@login_required
def clear_conversations():
    db = current_app.db
    conversations = AIConversation.get_by_user(current_user.id)

    for conv in conversations:
        db.delete('ai_conversations', conv.id)

    return jsonify({'success': True})

@ai_bp.route('/analyze_code', methods=['POST'])
@ai_limiter.limit("10 per minute")
def analyze_code():
    data = request.get_json()

    code = data.get('code', '')
    problem_id = data.get('problem_id')
    model_name = data.get('model', 'caigpt')

    if not code:
        return jsonify({'error': 'Code cannot be empty'}), 400

    models = get_ai_models()
    if model_name not in models:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    model_info = models[model_name]

    if model_name not in ('local', 'caigpt', 'ollama') and not model_info['api_key']:
        return jsonify({'error': f'{model_info["name"]} API key not configured'}), 400

    try:
        question = f"Please analyze the following C++ code, point out problems, errors, and improvement suggestions. Do not give complete correct code directly, but guide students to modify it themselves.\n\nCode:\n{code}"

        if problem_id:
            problem = Problem.get_by_id(problem_id)
            if problem:
                question = f"Problem requirements: {problem.description}\n\nInput format: {problem.input_format}\n\nOutput format: {problem.output_format}\n\nPlease analyze the following student code, point out problems, errors, and improvement suggestions. Do not give complete correct code directly, but guide students to modify it themselves.\n\nCode:\n{code}"

        if model_name == 'local':
            return handle_local_analyze(question)
        elif model_name in ('caigpt', 'ollama', 'minimax'):
            response = handle_caigpt_chat(model_info, question, problem_id, 'code_analysis', has_code=True, has_image=False, image_data='')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    return jsonify({
                        'success': True,
                        'analysis': data.get('answer', ''),
                        'model': model_info['name']
                    })
                else:
                    return response
            else:
                return response
        elif model_name == 'gemini':
            return handle_gemini_analyze(model_info, question)
        else:
            return handle_openai_analyze(model_info, question)

    except Exception as e:
        return jsonify({'error': f'Code analysis failed: {str(e)}'}), 500


def handle_gemini_analyze(model_info, question):
    contents = [
        {'role': 'user', 'parts': [{'text': f'{SYSTEM_PROMPT}\n\n{question}'}]}
    ]

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2000
        }
    }

    url = f"{model_info['api_url']}?key={model_info['api_key']}"

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']

        return jsonify({
            'success': True,
            'analysis': answer,
            'model': model_info['name']
        })
    else:
        return jsonify({'error': f'AI service returned error: {response.text}'}), 500


def handle_openai_analyze(model_info, question):
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': question}
    ]

    headers = {
        'Authorization': f'Bearer {model_info["api_key"]}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': model_info['model'],
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 2000
    }

    response = requests.post(
        model_info['api_url'],
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']

        return jsonify({
            'success': True,
            'analysis': answer,
            'model': model_info['name']
        })
    else:
        return jsonify({'error': f'AI service returned error: {response.text}'}), 500


def handle_local_chat(question, problem_id, conversation_type, has_code, has_image, image_data):
    """Handle local mock model chat request"""
    def get_mock_response(q):
        """Generate mock AI response"""
        responses = {
            "你好": "你好！我是你的C++编程助手，有什么可以帮助你的吗？",
            "Hello": "你好！我是你的C++编程助手，有什么可以帮助你的吗？",
            "hi": "你好！我是你的C++编程助手，有什么可以帮助你的吗？",
            "如何编写Hello World": "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}",
            "Hello World": "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}",
            "hello world": "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}",
        }
        for key, value in responses.items():
            if key.lower() in q.lower():
                return value
        return "抱歉，我目前只支持一些基础问题。请尝试询问关于 C++ 的其他问题。"

    answer = get_mock_response(question)

    if current_user.is_authenticated:
        conversation = AIConversation(
            user_id=current_user.id,
            problem_id=problem_id,
            question=question,
            answer=answer,
            model_name='本地模拟',
            conversation_type=conversation_type,
            has_code=has_code,
            has_image=has_image
        )
        conversation.save()
        conversation_id = conversation.id
    else:
        conversation_id = None

    return jsonify({
        'success': True,
        'answer': answer,
        'model': '本地模拟',
        'conversation_id': conversation_id
    })


def handle_local_analyze(question):
    """Handle local mock model code analysis"""
    return jsonify({
        'success': True,
        'analysis': "This is a mock analysis. Please configure an actual AI model for code analysis.",
        'model': '本地模拟'
    })


def handle_caigpt_chat(model_info, question, problem_id, conversation_type, has_code, has_image, image_data):
    """Handle CAIgpt model chat request - 使用 ProviderManager + MemoryService"""
    user_id = current_user.id if current_user.is_authenticated else 0
    model_name = model_info.get('model', 'caigpt')
    display_name = model_info.get('name', 'CAIgpt')

    if has_image and image_data:
        ocr_text, error = baidu_ocr(image_data)
        if error:
            logger.error(f"OCR recognition failed: {error}")
            user_message = f"{question}\n\n[Image content]"
        else:
            user_message = f"{question}\n\n[Image content]\n{ocr_text}"
    else:
        user_message = question

    history = get_user_history(user_id)
    user = current_user if current_user.is_authenticated else None
    messages = build_messages(user_message, history, user=user, problem_id=problem_id)

    try:
        config_dict = {k: v for k, v in current_app.config.items() if isinstance(v, (str, int, float, bool))}
        manager = _get_provider_manager(config_dict)

        if model_name in ('minimax', 'ollama', 'qwen'):
            manager.switch_provider(model_name)

        provider = manager.get_active_provider()
        if provider is None:
            raise Exception("No available AI provider")
        response_message = provider.chat(messages)

        if user_id > 0:
            save_message(user_id, "user", user_message, [image_data] if has_image and image_data else None)
            save_message(user_id, "assistant", response_message)

            try:
                memory_svc = get_memory_service()
                memory_svc.extract_memories_from_conversation(
                    user_id, user_message, response_message
                )
            except Exception as mem_err:
                logger.warning(f"Memory extraction failed: {mem_err}")

        conversation = AIConversation(
            user_id=user_id if user_id > 0 else None,
            problem_id=problem_id,
            question=question,
            answer=response_message,
            model_name=display_name,
            conversation_type=conversation_type,
            has_code=has_code,
            has_image=has_image
        )
        conversation.save()

        return jsonify({
            'success': True,
            'answer': response_message,
            'model': display_name,
            'conversation_id': conversation.id
        })

    except Exception as e:
        logger.error(f"{display_name} processing failed: {str(e)}")
        return jsonify({'error': f'{display_name} processing failed: {str(e)}'}), 500


def handle_caigpt_chat_stream(model_info, question, problem_id, conversation_type, has_code, has_image, image_data):
    """Handle CAIgpt model chat request with streaming support - 使用 ProviderManager + MemoryService"""
    user_id = current_user.id if current_user.is_authenticated else 0
    model_name = model_info.get('model', 'caigpt')
    display_name = model_info.get('name', 'CAIgpt')

    logger.info(f"📸 图片处理状态: has_image={has_image}, image_data长度={len(image_data) if image_data else 0}")

    if has_image and image_data:
        logger.info("🔍 正在调用百度 OCR 识别图片...")
        ocr_text, error = baidu_ocr(image_data)
        if error:
            logger.error(f"❌ OCR recognition failed: {error}")
            user_message = f"{question}\n\n[Image content]"
        else:
            logger.info(f"✅ OCR 识别成功，文本长度: {len(ocr_text)}")
            logger.debug(f"OCR 识别内容: {ocr_text[:200]}...")
            user_message = f"{question}\n\n[Image content]\n{ocr_text}"
    else:
        user_message = question

    max_cache = int(os.environ.get('AI_MAX_HISTORY', 20))

    history = get_user_history(user_id, max_history=max_cache)
    user = current_user if current_user.is_authenticated else None
    messages = build_messages(user_message, history, user=user, problem_id=problem_id)

    if user_id > 0:
        save_message(user_id, "user", user_message, [image_data] if has_image and image_data else None)

    # 在 Flask 上下文内预先获取配置和 ProviderManager
    # 避免在 generate() 生成器内部访问 current_app
    try:
        config_dict = {k: v for k, v in current_app.config.items() if isinstance(v, (str, int, float, bool))}
        manager = _get_provider_manager(config_dict)

        if model_name in ('minimax', 'ollama', 'qwen'):
            manager.switch_provider(model_name)

        provider = manager.get_active_provider()
        if provider is None:
            raise Exception("No available AI provider")
        # 获取真实的 app 对象用于在生成器内创建上下文
        app = current_app._get_current_object()
    except Exception as e:
        logger.error(f"Failed to initialize provider for streaming: {e}")
        return jsonify({'error': f'AI provider initialization failed: {str(e)}'}), 500

    def generate():
        full_response = ""
        try:
            stream_generator = provider.chat_stream(messages)

            for chunk_content in stream_generator:
                full_response += chunk_content
                yield f"data: {json.dumps({'content': chunk_content, 'done': False})}\n\n"

            # 使用应用上下文保存消息和记忆
            with app.app_context():
                if user_id > 0:
                    save_message(user_id, "assistant", full_response)

                    try:
                        memory_svc = get_memory_service()
                        memory_svc.extract_memories_from_conversation(
                            user_id, user_message, full_response
                        )
                    except Exception as mem_err:
                        logger.warning(f"Memory extraction failed: {mem_err}")

                if user_id > 0:
                    try:
                        conversation = AIConversation(
                            user_id=user_id,
                            problem_id=problem_id,
                            question=question,
                            answer=full_response,
                            model_name=display_name,
                            conversation_type=conversation_type,
                            has_code=has_code,
                            has_image=has_image
                        )
                        conversation.save()
                    except Exception as save_err:
                        logger.error(f"Failed to save conversation: {save_err}")

            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            logger.error(f"{display_name} streaming failed: {str(e)}")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"

    response = Response(
        generate(),
        mimetype='text/event-stream'
    )
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@ai_bp.route('/chat/stream', methods=['POST'])
@ai_limiter.limit("20 per minute")
def chat_stream():
    """Streaming chat endpoint for real-time AI responses"""
    # 检查请求类型
    if request.is_json:
        data = request.get_json()
        question = data.get('question', '')
        model_name = data.get('model', 'local')
        problem_id = data.get('problem_id')
        conversation_type = data.get('type', 'general')
        has_code = data.get('has_code', False)
        has_image = data.get('has_image', False)
        image_data = data.get('image', '')
    else:
        # 处理 FormData 请求
        data = request.form
        question = data.get('question', '')
        model_name = data.get('model', 'local')
        problem_id = data.get('problem_id')
        conversation_type = data.get('type', 'general')
        has_code = data.get('has_code', 'false').lower() == 'true'
        has_image = data.get('has_image', 'false').lower() == 'true'
        image_data = ''
        
        # 处理文件上传
        if 'file_0' in request.files:
            file = request.files['file_0']
            if file and file.filename:
                import base64
                image_data = base64.b64encode(file.read()).decode('utf-8')
                has_image = True  # ✅ 标记有图片，触发 OCR 识别

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    models = get_ai_models()
    if model_name not in models:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    if model_name in ('caigpt', 'ollama', 'minimax'):
        model_info = models[model_name]
        return handle_caigpt_chat_stream(model_info, question, problem_id, conversation_type, has_code, has_image, image_data)
    else:
        return jsonify({'error': 'Streaming is only supported for CAIgpt model currently'}), 400


@ai_bp.route('/sessions', methods=['POST'])
@login_required
def create_session():
    """Create a new chat session"""
    data = request.get_json() or {}
    title = data.get('title', '新对话')
    problem_id = data.get('problem_id')
    model_name = data.get('model', 'caigpt')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO caigpt_sessions (user_id, title, model_name, problem_id)
        VALUES (%s, %s, %s, %s)
        ''', (current_user.id, title, model_name, problem_id))

        conn.commit()
        session_id = cursor.lastrowid

        return jsonify({
            'success': True,
            'session': {
                'id': session_id,
                'title': title,
                'model_name': model_name,
                'problem_id': problem_id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        return jsonify({'error': f'Failed to create session: {str(e)}'}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    """Get user's chat sessions"""
    limit = request.args.get('limit', 50, type=int)

    conn = get_db_connection()
    if not conn:
        return jsonify({'sessions': []})

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
        SELECT id, title, model_name, problem_id, created_at, updated_at
        FROM caigpt_sessions
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT %s
        ''', (current_user.id, limit))

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'model_name': row['model_name'],
                'problem_id': row['problem_id'],
                'created_at': str(row['created_at']),
                'updated_at': str(row['updated_at']),
                'message_count': get_session_message_count(row['id'])
            })

        return jsonify({'sessions': sessions})
    except Exception as e:
        logger.error(f"Failed to get sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/search', methods=['GET'])
@login_required
def search_sessions():
    """Search sessions by keyword"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)

    if not query or len(query) < 2:
        return jsonify({'sessions': [], 'message': '搜索关键词至少需要2个字符'})

    conn = get_db_connection()
    if not conn:
        return jsonify({'sessions': []})

    try:
        cursor = conn.cursor(dictionary=True)
        search_term = f'%{query}%'

        cursor.execute('''
        SELECT s.id, s.title, s.model_name, s.problem_id, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM caigpt_dialog_history dh WHERE dh.session_id = s.id) as message_count
        FROM caigpt_sessions s
        LEFT JOIN caigpt_dialog_history dh ON s.id = dh.session_id
        WHERE s.user_id = %s
          AND (s.title LIKE %s OR dh.content LIKE %s)
        GROUP BY s.id
        ORDER BY
            CASE WHEN s.title LIKE %s THEN 0 ELSE 1 END,
            s.updated_at DESC
        LIMIT %s
        ''', (current_user.id, search_term, search_term, search_term, limit))

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'model_name': row['model_name'],
                'problem_id': row['problem_id'],
                'created_at': str(row['created_at']),
                'updated_at': str(row['updated_at']),
                'message_count': row['message_count']
            })

        return jsonify({
            'sessions': sessions,
            'query': query,
            'total': len(sessions)
        })
    except Exception as e:
        logger.error(f"Failed to search sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/<int:session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Get session details with message history"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT * FROM caigpt_sessions WHERE id = %s AND user_id = %s
        ''', (session_id, current_user.id))
        session = cursor.fetchone()

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        cursor.execute('''
        SELECT role, content, images, created_at
        FROM caigpt_dialog_history
        WHERE user_id = %s AND session_id = %s
        ORDER BY created_at ASC
        ''', (current_user.id, session_id))

        messages = []
        for row in cursor.fetchall():
            msg = {
                'role': row['role'],
                'content': row['content'],
                'created_at': str(row['created_at'])
            }
            if row['images']:
                msg['images'] = json.loads(row['images'])
            messages.append(msg)

        return jsonify({
            'session': {
                'id': session['id'],
                'title': session['title'],
                'model_name': session['model_name'],
                'created_at': str(session['created_at']),
                'updated_at': str(session['updated_at'])
            },
            'messages': messages
        })
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/<int:session_id>/title', methods=['PUT'])
@login_required
def update_session_title(session_id):
    """Update session title"""
    data = request.get_json()
    title = data.get('title', '').strip()

    if not title:
        return jsonify({'error': 'Title cannot be empty'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE caigpt_sessions SET title = %s WHERE id = %s AND user_id = %s
        ''', (title, session_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Session not found or no permission'}), 404

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to update session title: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/<int:session_id>/tags', methods=['PUT'])
@login_required
def update_session_tags(session_id):
    """Update session tags"""
    data = request.get_json()
    tags = data.get('tags', [])

    if not isinstance(tags, list):
        return jsonify({'error': 'Tags must be a list'}), 400

    tags = [tag.strip() for tag in tags if tag.strip()]

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        tags_json = json.dumps(tags) if tags else None

        cursor.execute('''
        UPDATE caigpt_sessions SET tags = %s WHERE id = %s AND user_id = %s
        ''', (tags_json, session_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Session not found or no permission'}), 404

        return jsonify({'success': True, 'tags': tags})
    except Exception as e:
        logger.error(f"Failed to update session tags: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/tags', methods=['GET'])
@login_required
def get_all_tags():
    """Get all unique tags used by the user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'tags': []})

    try:
        cursor = conn.cursor()

        cursor.execute('''
        SELECT tags FROM caigpt_sessions
        WHERE user_id = %s AND tags IS NOT NULL AND tags != 'null' AND tags != '[]'
        ''', (current_user.id,))

        all_tags = set()
        for row in cursor.fetchall():
            if row[0]:
                try:
                    tags_list = json.loads(row[0])
                    if isinstance(tags_list, list):
                        for tag in tags_list:
                            if tag:
                                all_tags.add(tag)
                except (json.JSONDecodeError, TypeError):
                    continue

        return jsonify({
            'tags': sorted(list(all_tags)),
            'total': len(all_tags)
        })
    except Exception as e:
        logger.error(f"Failed to get tags: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/tag/<tag_name>', methods=['GET'])
@login_required
def get_sessions_by_tag(tag_name):
    """Get sessions filtered by tag"""
    tag_name = tag_name.strip()

    if not tag_name:
        return jsonify({'sessions': []})

    conn = get_db_connection()
    if not conn:
        return jsonify({'sessions': []})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT s.id, s.title, s.model_name, s.problem_id, s.created_at, s.updated_at, s.tags,
               (SELECT COUNT(*) FROM caigpt_dialog_history dh WHERE dh.session_id = s.id) as message_count
        FROM caigpt_sessions s
        WHERE s.user_id = %s AND JSON_CONTAINS(s.tags, %s)
        ORDER BY s.updated_at DESC
        ''', (current_user.id, json.dumps(tag_name)))

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'model_name': row['model_name'],
                'problem_id': row['problem_id'],
                'created_at': str(row['created_at']),
                'updated_at': str(row['updated_at']),
                'message_count': row['message_count'],
                'tags': json.loads(row['tags']) if row['tags'] else []
            })

        return jsonify({
            'sessions': sessions,
            'tag': tag_name,
            'total': len(sessions)
        })
    except Exception as e:
        logger.error(f"Failed to get sessions by tag: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/favorites', methods=['POST'])
@login_required
def add_favorite():
    """Add a message to favorites"""
    data = request.get_json()
    session_id = data.get('session_id')
    message_content = data.get('content')

    if not session_id or not message_content:
        return jsonify({'error': 'session_id and content are required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO caigpt_favorites (user_id, session_id, content)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content)
        ''', (current_user.id, session_id, message_content[:2000]))

        conn.commit()

        favorite_id = cursor.lastrowid

        return jsonify({
            'success': True,
            'favorite_id': favorite_id,
            'message': '已收藏'
        })
    except Exception as e:
        logger.error(f"Failed to add favorite: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def remove_favorite(favorite_id):
    """Remove a favorite"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        DELETE FROM caigpt_favorites WHERE id = %s AND user_id = %s
        ''', (favorite_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Favorite not found or no permission'}), 404

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to remove favorite: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    """Get user's favorites"""
    limit = request.args.get('limit', 50, type=int)

    conn = get_db_connection()
    if not conn:
        return jsonify({'favorites': []})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT f.id, f.session_id, f.content, f.created_at,
               s.title as session_title
        FROM caigpt_favorites f
        LEFT JOIN caigpt_sessions s ON f.session_id = s.id
        WHERE f.user_id = %s
        ORDER BY f.created_at DESC
        LIMIT %s
        ''', (current_user.id, limit))

        favorites = []
        for row in cursor.fetchall():
            favorites.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'content': row['content'],
                'session_title': row['session_title'] or '未知会话',
                'created_at': str(row['created_at'])
            })

        return jsonify({'favorites': favorites})
    except Exception as e:
        logger.error(f"Failed to get favorites: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    """Delete a session and its messages"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        DELETE FROM caigpt_dialog_history WHERE session_id = %s AND user_id = %s
        ''', (session_id, current_user.id))

        cursor.execute('''
        DELETE FROM caigpt_sessions WHERE id = %s AND user_id = %s
        ''', (session_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Session not found or no permission'}), 404

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/sessions/clear', methods=['POST'])
@login_required
def clear_all_sessions():
    """Clear all user's sessions"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        DELETE FROM caigpt_dialog_history WHERE user_id = %s
        ''', (current_user.id,))

        cursor.execute('''
        DELETE FROM caigpt_sessions WHERE user_id = %s
        ''', (current_user.id,))

        conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to clear sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def get_session_message_count(session_id):
    try:
        conn = get_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT COUNT(*) as count FROM caigpt_dialog_history WHERE session_id = %s
            ''', (session_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to get message count: {str(e)}")
        return 0


# ===== 代码编译与执行 API =====

@ai_bp.route('/code/execute', methods=['POST'])
@login_required
def execute_code():
    """Compile and execute C++ code"""
    data = request.get_json()
    code = data.get('code', '')
    input_data = data.get('input', '')
    timeout = data.get('timeout', 10)

    if not code:
        return jsonify({'error': '代码不能为空'}), 400

    import tempfile
    import signal
    import platform
    from datetime import datetime

    result = {
        'success': False,
        'output': '',
        'error': '',
        'compile_output': '',
        'execution_time': 0,
        'memory_usage': 0,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'compiler_info': ''
    }

    # ===== 查找 g++ 编译器路径 =====
    gpp_path = find_gpp_compiler()

    if not gpp_path:
        result['error'] = (
            "未找到 C++ 编译器 (g++)。\n\n"
            "请安装 MinGW-w64 或 MSYS2：\n"
            "• Windows: https://www.mingw-w64.org/downloads\n"
            "• 安装后确保将 bin 目录添加到系统 PATH 环境变量\n"
            "• 或在 .env 文件中配置 GPP_PATH 指向完整路径"
        )
        result['compile_output'] = '❌ 编译器未安装'
        return jsonify(result)

    result['compiler_info'] = f"使用编译器: {gpp_path}"
    logger.info(f"Using compiler: {gpp_path}")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = os.path.join(tmpdir, 'main.cpp')
            executable_file = os.path.join(tmpdir, 'main')
            if os.name == 'nt':
                executable_file += '.exe'
            output_file = os.path.join(tmpdir, 'output.txt')

            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(code)

            compile_start = datetime.now()

            try:
                compile_process = subprocess.run(
                    [gpp_path, '-O2', '-std=c++17', '-o', executable_file, source_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmpdir
                )

                if compile_process.returncode != 0:
                    result['compile_output'] = compile_process.stderr or compile_process.stdout
                    result['error'] = '编译失败'
                    logger.warning(f"Compilation failed: {compile_process.stderr}")
                    return jsonify(result)

                result['compile_output'] = '编译成功 ✓'

            except subprocess.TimeoutExpired:
                result['error'] = '编译超时（>30秒），请检查代码是否有死循环或无限递归'
                return jsonify(result)

            compile_time = (datetime.now() - compile_start).total_seconds()

            execute_start = datetime.now()

            try:
                stdin_data = input_data if input_data else None

                exec_process = subprocess.run(
                    [executable_file],
                    input=stdin_data,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                    env={**os.environ, 'LANG': 'en_US.UTF-8'}
                )

                output_text = exec_process.stdout
                error_text = exec_process.stderr

                execution_time = (datetime.now() - execute_start).total_seconds()
                result['execution_time'] = round(compile_time + execution_time, 3)
                result['success'] = True

                lines = []
                if output_text.strip():
                    lines.append(f'--- 输出 ---')
                    for line in output_text.split('\n')[:100]:
                        lines.append(line)

                if error_text.strip():
                    lines.append(f'--- 错误/警告 ---')
                    for line in error_text.split('\n')[:50]:
                        lines.append(line)

                if not lines:
                    lines.append('(无输出)')

                result['output'] = '\n'.join(lines)

            except subprocess.TimeoutExpired:
                result['error'] = f'程序运行超时（>{timeout}秒）'
                result['output'] = f'⏱️ 程序被终止：超过 {timeout} 秒时间限制'

            except Exception as exec_error:
                result['error'] = f'运行时错误: {str(exec_error)}'
                result['output'] = str(exec_error)

    except Exception as e:
        logger.error(f"Code execution failed: {str(e)}")
        result['error'] = f'服务器内部错误: {str(e)}'

    return jsonify(result)


@ai_bp.route('/code/analyze', methods=['POST'])
@login_required
def analyze_code_complexity():
    """8项代码静态分析：命名规范、内存泄漏、数组越界、未使用变量、类型安全、代码复杂度、资源管理、潜在死循环"""
    data = request.get_json()
    code = data.get('code', '')

    if not code:
        return jsonify({'error': '代码不能为空'}), 400

    lines = code.split('\n')
    analysis = {
        'lines_of_code': len(lines),
        'blank_lines': len([l for l in lines if not l.strip()]),
        'comment_lines': len([l for l in lines if l.strip().startswith('//') or l.strip().startswith('/*') or l.strip().startswith('*')]),
        'code_lines': 0,
        'complexity': {'time': 'O(1)', 'space': 'O(1)'},
        'functions': [],
        'loops': [],
        'static_checks': [],
        'warnings': [],
        'suggestions': []
    }

    analysis['code_lines'] = analysis['lines_of_code'] - analysis['blank_lines'] - analysis['comment_lines']

    functions = re.findall(r'(?:void|int|float|double|char|string|bool|auto|long|unsigned)\s+(\w+)\s*\(([^)]*)\)\s*(?:\{|;)', code)
    analysis['functions'] = [{'name': f, 'params': p} for f, p in functions]

    loop_patterns = [
        (r'for\s*\([^)]+\)', 'for 循环'),
        (r'while\s*\([^)]+\)', 'while 循环'),
        (r'do\s*{[^}]*}\s*while', 'do-while 循环')
    ]

    for pattern, name in loop_patterns:
        matches = re.findall(pattern, code)
        for m in matches:
            analysis['loops'].append({'type': name, 'pattern': m[:50]})

    # ===== 检查1：命名规范 =====
    naming_issues = []
    single_char_vars = re.findall(r'\b(int|float|double|char|string|bool|auto|long)\s+([a-z])\s*[;=,\)]', code)
    for var_type, var_name in single_char_vars:
        if var_name not in ['i', 'j', 'k', 'n', 'm', 'x', 'y', 'z', 'r', 'g', 'b', 'e']:
            naming_issues.append(f"变量 '{var_name}' 命名过短，建议使用更有意义的名称")

    all_caps_vars = re.findall(r'\b(int|float|double|char|string|bool|auto|long)\s+([A-Z]{2,})\s*[;=,\)]', code)
    for var_type, var_name in all_caps_vars:
        naming_issues.append(f"变量 '{var_name}' 使用全大写命名，通常全大写用于常量/宏定义")

    func_names_lower = re.findall(r'(?:void|int|float|double|char|string|bool|auto)\s+([a-z]+\_[a-z\_]+)\s*\(', code)
    for fn in func_names_lower:
        naming_issues.append(f"函数 '{fn}' 使用下划线命名，C++推荐驼峰命名法")

    if naming_issues:
        analysis['static_checks'].append({
            'check': '命名规范',
            'status': 'warning',
            'count': len(naming_issues),
            'details': naming_issues[:5],
            'description': '检查变量和函数命名是否符合C++命名规范'
        })
    else:
        analysis['static_checks'].append({
            'check': '命名规范',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '命名规范检查通过'
        })

    # ===== 检查2：内存泄漏风险 =====
    memory_issues = []
    new_count = len(re.findall(r'\bnew\b', code))
    delete_count = len(re.findall(r'\bdelete\b', code))
    malloc_count = len(re.findall(r'\bmalloc\b', code))
    calloc_count = len(re.findall(r'\bcalloc\b', code))
    realloc_count = len(re.findall(r'\brealloc\b', code))
    free_count = len(re.findall(r'\bfree\b', code))

    if new_count > 0 and delete_count < new_count:
        memory_issues.append(f"使用了 {new_count} 次 new 但只有 {delete_count} 次 delete，可能存在内存泄漏")
    if (malloc_count + calloc_count + realloc_count) > 0 and free_count < (malloc_count + calloc_count + realloc_count):
        memory_issues.append(f"使用了 {malloc_count + calloc_count + realloc_count} 次 malloc/calloc/realloc 但只有 {free_count} 次 free")
    if new_count > 0 and 'delete[]' not in code and re.search(r'new\s+\w+\s*\[', code):
        memory_issues.append("使用 new[] 分配数组但未找到 delete[]，应使用 delete[] 释放数组内存")
    if new_count > 0 and 'unique_ptr' not in code and 'shared_ptr' not in code and 'auto_ptr' not in code:
        memory_issues.append("建议使用智能指针(unique_ptr/shared_ptr)代替裸指针new，可自动管理内存")

    if memory_issues:
        analysis['static_checks'].append({
            'check': '内存泄漏风险',
            'status': 'error',
            'count': len(memory_issues),
            'details': memory_issues,
            'description': '检查动态内存分配是否正确释放'
        })
    else:
        analysis['static_checks'].append({
            'check': '内存泄漏风险',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '内存管理检查通过'
        })

    # ===== 检查3：数组越界风险 =====
    array_issues = []
    array_access_no_check = re.findall(r'(\w+)\[(\w+)\]', code)
    for arr_name, index_var in array_access_no_check:
        if index_var.isdigit():
            continue
        bound_check_pattern = rf'\b(if|while|assert|check).*{index_var}\s*(<|<=|>|>=)'
        if not re.search(bound_check_pattern, code):
            array_issues.append(f"数组 '{arr_name}' 使用变量 '{index_var}' 作为下标，但未发现边界检查")

    vla_pattern = re.findall(r'(\w+)\s+(\w+)\[(\w+)\]\s*;', code)
    for type_name, arr_name, size_var in vla_pattern:
        if not size_var.isdigit():
            array_issues.append(f"数组 '{arr_name}' 使用变量 '{size_var}' 作为大小，可能是变长数组(VLA)，存在栈溢出风险")

    fixed_array_access = re.findall(r'(\w+)\[(\d+)\]', code)
    for arr_name, idx_str in fixed_array_access:
        arr_decl = re.search(rf'{arr_name}\s+\w+\[(\d+)\]', code)
        if arr_decl and int(idx_str) >= int(arr_decl.group(1)) - 1 and int(idx_str) > 0:
            array_issues.append(f"数组 '{arr_name}' 大小为 {arr_decl.group(1)}，访问下标 {idx_str} 可能越界")

    if array_issues:
        analysis['static_checks'].append({
            'check': '数组越界风险',
            'status': 'error',
            'count': len(array_issues),
            'details': array_issues[:5],
            'description': '检查数组访问是否有边界检查'
        })
    else:
        analysis['static_checks'].append({
            'check': '数组越界风险',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '数组越界检查通过'
        })

    # ===== 检查4：未使用变量 =====
    unused_issues = []
    var_declarations = re.findall(r'\b(int|float|double|char|string|bool|auto|long|unsigned)\s+(\w+)\s*[;=]', code)
    for var_type, var_name in var_declarations:
        if var_name in ['main', 'argc', 'argv']:
            continue
        usage_pattern = rf'\b{re.escape(var_name)}\b'
        usages = re.findall(usage_pattern, code)
        if len(usages) <= 1:
            unused_issues.append(f"变量 '{var_name}' ({var_type}) 声明后可能未被使用")

    if unused_issues:
        analysis['static_checks'].append({
            'check': '未使用变量',
            'status': 'warning',
            'count': len(unused_issues),
            'details': unused_issues[:5],
            'description': '检查声明但未使用的变量'
        })
    else:
        analysis['static_checks'].append({
            'check': '未使用变量',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '未使用变量检查通过'
        })

    # ===== 检查5：类型安全 =====
    type_issues = []
    c_style_casts = re.findall(r'\(\s*(int|float|double|char|long|unsigned)\s*\)\s*\w+', code)
    if c_style_casts:
        type_issues.append(f"发现 {len(c_style_casts)} 处C风格强制类型转换，建议使用 static_cast/const_cast/reinterpret_cast")

    if 'scanf' in code:
        type_issues.append("使用了 scanf，类型不安全，建议使用 cin 或 getline")
    if 'gets' in code:
        type_issues.append("使用了 gets()，该函数已在C11标准中移除，极度不安全，请使用 fgets 或 getline")
    if 'printf' in code and 'scanf' in code:
        type_issues.append("混用 C 风格 I/O (printf/scanf)，建议统一使用 C++ 风格 (cout/cin)")

    implicit_conv = re.findall(r'\bdouble\s+\w+\s*=\s*\d+;', code)
    float_assign = re.findall(r'\bfloat\s+\w+\s*=\s*\d+\.\d+', code)
    if float_assign:
        type_issues.append("float 类型赋值浮点常量未加 f 后缀，默认为 double 类型")

    if type_issues:
        analysis['static_checks'].append({
            'check': '类型安全',
            'status': 'warning',
            'count': len(type_issues),
            'details': type_issues,
            'description': '检查类型转换和I/O操作的类型安全性'
        })
    else:
        analysis['static_checks'].append({
            'check': '类型安全',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '类型安全检查通过'
        })

    # ===== 检查6：代码复杂度 =====
    complexity_issues = []
    nested_depth = 0
    max_nested = 0
    for line in lines:
        depth_change = line.count('{') - line.count('}')
        nested_depth += depth_change
        if nested_depth > max_nested:
            max_nested = nested_depth

    if max_nested > 4:
        complexity_issues.append(f"最大嵌套深度为 {max_nested} 层，建议不超过4层，考虑提取函数")

    if len(analysis['loops']) > 3:
        complexity_issues.append(f"发现 {len(analysis['loops'])} 个循环，可能存在较高时间复杂度")
        analysis['complexity']['time'] = 'O(n^k) 或更高（嵌套循环较多）'
    elif len(analysis['loops']) > 1:
        analysis['complexity']['time'] = 'O(n^2) 或 O(n·m)（存在多重循环）'
    elif len(analysis['loops']) == 1:
        analysis['complexity']['time'] = 'O(n)（单层循环）'

    long_lines = [i + 1 for i, l in enumerate(lines) if len(l) > 120]
    if long_lines:
        complexity_issues.append(f"发现 {len(long_lines)} 行超过120字符，影响可读性")

    if analysis['code_lines'] > 50 and len(analysis['functions']) <= 1:
        complexity_issues.append(f"代码共 {analysis['code_lines']} 行但只有 {len(analysis['functions'])} 个函数，建议拆分为更小的函数")

    if complexity_issues:
        analysis['static_checks'].append({
            'check': '代码复杂度',
            'status': 'warning',
            'count': len(complexity_issues),
            'details': complexity_issues,
            'description': '检查代码嵌套深度、行数和函数拆分情况'
        })
    else:
        analysis['static_checks'].append({
            'check': '代码复杂度',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '代码复杂度检查通过'
        })

    # ===== 检查7：资源管理 =====
    resource_issues = []
    file_open_no_close = re.findall(r'fopen\s*\(', code)
    if file_open_no_close and 'fclose' not in code:
        resource_issues.append("使用了 fopen 但未找到 fclose，文件资源可能泄漏")

    if 'ifstream' in code or 'ofstream' in code:
        if 'close()' not in code and 'RAII' not in code:
            pass

    if 'cin' in code and not re.search(r'cin\.(fail|clear|ignore|good)', code) and not re.search(r'if\s*\(\s*cin', code):
        resource_issues.append("使用 cin 输入但未检查输入是否成功，可能导致无限循环或错误")

    if 'cout' in code and 'endl' in code:
        resource_issues.append("频繁使用 endl 会刷新缓冲区影响性能，建议使用 '\\n' 代替")

    if resource_issues:
        analysis['static_checks'].append({
            'check': '资源管理',
            'status': 'warning',
            'count': len(resource_issues),
            'details': resource_issues,
            'description': '检查文件、流等资源的正确管理'
        })
    else:
        analysis['static_checks'].append({
            'check': '资源管理',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '资源管理检查通过'
        })

    # ===== 检查8：潜在死循环 =====
    loop_issues = []
    while_true = re.findall(r'while\s*\(\s*true\s*\)|while\s*\(\s*1\s*\)|while\s*\(\s*True\s*\)', code)
    if while_true:
        has_break = 'break' in code
        if not has_break:
            loop_issues.append("发现 while(true) 循环但未找到 break 语句，可能存在死循环")

    for_loops = re.findall(r'for\s*\(\s*;\s*;\s*\)', code)
    if for_loops and 'break' not in code:
        loop_issues.append("发现 for(;;) 无限循环但未找到 break 语句")

    while_no_update = re.findall(r'while\s*\(\s*(\w+)\s*(<|<=|>|>=|!=|==)\s*(\w+)\s*\)', code)
    for cond_var, op, cond_val in while_no_update:
        if cond_var not in ['true', 'false', '1', '0']:
            update_pattern = rf'\b{re.escape(cond_var)}\s*(\+\+|\-\-|\+=|\-=)'
            if not re.search(update_pattern, code):
                loop_issues.append(f"while 循环条件变量 '{cond_var}' 在循环体内可能未被更新，存在死循环风险")

    if loop_issues:
        analysis['static_checks'].append({
            'check': '潜在死循环',
            'status': 'error',
            'count': len(loop_issues),
            'details': loop_issues,
            'description': '检查循环是否有正确的终止条件'
        })
    else:
        analysis['static_checks'].append({
            'check': '潜在死循环',
            'status': 'pass',
            'count': 0,
            'details': [],
            'description': '死循环检查通过'
        })

    # ===== 汇总 =====
    error_count = sum(1 for c in analysis['static_checks'] if c['status'] == 'error')
    warning_count = sum(1 for c in analysis['static_checks'] if c['status'] == 'warning')
    pass_count = sum(1 for c in analysis['static_checks'] if c['status'] == 'pass')

    analysis['summary'] = {
        'total_checks': 8,
        'passed': pass_count,
        'warnings': warning_count,
        'errors': error_count,
        'overall': '优秀' if error_count == 0 and warning_count <= 1 else '需要改进' if error_count > 0 else '良好'
    }

    if 'using namespace std;' in code:
        analysis['suggestions'].append('💡 在大型项目中建议避免使用 using namespace std;')
    if 'vector<' in code:
        analysis['suggestions'].append('✅ 使用了 vector，这是良好的 C++ 实践')

    return jsonify(analysis)


# ===== 对话导出 API =====

@ai_bp.route('/export/<int:session_id>', methods=['GET'])
@login_required
def export_session(session_id):
    """Export session conversation"""
    format_type = request.args.get('format', 'markdown').lower()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT s.title, s.created_at, s.model_name
        FROM caigpt_sessions s
        WHERE s.id = %s AND s.user_id = %s
        ''', (session_id, current_user.id))

        session = cursor.fetchone()

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        cursor.execute('''
        SELECT role, content, created_at
        FROM caigpt_dialog_history
        WHERE session_id = %s AND user_id = %s
        ORDER BY created_at ASC
        ''', (session_id, current_user.id))

        messages = cursor.fetchall()

        if format_type == 'markdown':
            content = generate_markdown_export(session, messages)
            from flask import Response
            return Response(
                content,
                mimetype='text/markdown',
                headers={'Content-Disposition': f'attachment; filename=session_{session_id}.md'}
            )
        elif format_type == 'pdf':
            pdf_content = generate_pdf_export(session, messages)
            from flask import Response
            return Response(
                pdf_content,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename=session_{session_id}.pdf'}
            )
        else:
            return jsonify({'error': 'Unsupported format. Use markdown or pdf.'}), 400

    except Exception as e:
        logger.error(f"Failed to export session: {str(e)}")
        return jsonify({'error': str(e)}), 500


def generate_markdown_export(session, messages):
    """Generate markdown export of session"""
    md = f"# {session['title']}\n\n"
    md += f"- **导出时间**：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"- **创建时间**：{session['created_at']}\n"
    md += f"- **模型**：{session['model_name']}\n"
    md += f"- **消息数**：{len(messages)}\n\n"
    md += "---\n\n"

    for msg in messages:
        role_label = "👤 学生" if msg['role'] == 'user' else "🤖 AI 助手"
        time_str = str(msg['created_at'])[11:19] if msg['created_at'] else ''

        md += f"### {role_label} ({time_str})\n\n"

        content = msg['content']
        if content.startswith('[Image content]') or content.startswith('[代码]'):
            md += f"*{content}*\n\n"
        else:
            md += f"{content}\n\n"

        md += "---\n\n"

    md += "\n*由 CAIgpt 智能助手导出*\n"
    return md


def generate_pdf_export(session, messages):
    """Generate PDF export of session (HTML to PDF)"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; color: #333; }}
            h1 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            .meta {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
            .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
            .user {{ background: #f0f4ff; border-left: 4px solid #667eea; }}
            .ai {{ background: #f9f9f9; border-left: 4px solid #764ba2; }}
            .role-label {{ font-weight: bold; margin-bottom: 8px; display: block; }}
            pre {{ background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; }}
            code {{ font-family: Consolas, Monaco, monospace; }}
            hr {{ border: none; border-top: 1px solid #eee; margin: 25px 0; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <h1>{session['title']}</h1>
        <div class="meta">
            导出时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            创建时间：{session['created_at']} | 
            模型：{session['model_name']} |
            消息数：{len(messages)}
        </div>
    """

    for msg in messages:
        role_class = "user" if msg['role'] == 'user' else "ai"
        role_label = "👤 学生" if msg['role'] == 'user' else "🤖 AI 助手"

        content = msg['content']

        if '```cpp' in content or '```c++' in content:
            pass
        else:
            content = content.replace('<', '&lt;').replace('>', '&gt;')

        html_content += f"""
        <div class="message {role_class}">
            <span class="role-label">{role_label}</span>
            <div>{content}</div>
        </div>
        <hr>
        """

    html_content += """
        <div class="footer">由 CAIgpt 智能助手导出</div>
    </body>
    </html>
    """

    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        return generate_fallback_pdf(session, messages)


def generate_fallback_pdf(session, messages):
    """Fallback PDF generation when weasyprint is not available"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#667eea',
        spaceAfter=12
    )
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#666666',
        spaceAfter=20
    )

    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.4, 0.49, 0.92)
    c.drawString(50, height - 50, session['title'])

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    y = height - 80
    c.drawString(50, y, f"导出时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y -= 30
    c.line(50, y, width - 50, y)
    y -= 20

    for msg in messages:
        if y < 100:
            c.showPage()
            y = height - 50

        role = "学生" if msg['role'] == 'user' else "AI 助手"
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(50, y, f"[{role}]")
        y -= 16

        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.3, 0.3, 0.3)

        content = msg['content'][:500]
        for line in content.split('\n')[:15]:
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(55, y, line[:90])
            y -= 12

        y -= 10

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ===== AI 代码补全 API =====

@ai_bp.route('/code/complete', methods=['POST'])
@login_required
def ai_code_completion():
    """Get AI-powered code completion suggestions"""
    data = request.get_json()
    code = data.get('code', '')
    cursor_line = data.get('cursor_line', 0)
    cursor_column = data.get('cursor_column', 0)

    if not code:
        return jsonify({'suggestions': []})

    lines = code.split('\n')
    current_line = lines[cursor_line - 1] if cursor_line <= len(lines) else ''
    prefix = '\n'.join(lines[max(0, cursor_line - 5):cursor_line])

    prompt = f"""你是一个C++代码补全助手。根据当前代码上下文，提供1-3个最可能的代码补全建议。

只输出补全内容，不要解释。每个建议用 ||| 分隔。

当前代码：
```cpp
{prefix}
```

光标位置：第{cursor_line}行，第{cursor_column}列

当前行内容：
{current_line}

请提供补全建议（只输出代码片段）："""

    try:
        messages = [{'role': 'user', 'content': prompt}]
        response_text = get_ai_response(messages, stream=False, timeout=10)
        suggestions = [s.strip() for s in response_text.split('|||') if s.strip()]
        return jsonify({
            'suggestions': suggestions[:5],
            'context': current_line[:50]
        })

    except Exception as e:
        logger.error(f"Code completion failed: {str(e)}")
        return jsonify({'suggestions': []})


# ===== 用户偏好设置 API =====

@ai_bp.route('/preferences', methods=['GET'])
@login_required
def get_user_preferences():
    conn = get_db_connection()
    if not conn:
        return jsonify({})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT * FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        pref = cursor.fetchone()

        if not pref:
            return jsonify({
                'theme': 'light',
                'editor_theme': 'vs-dark',
                'editor_font_size': 14,
                'minimap_enabled': True,
                'auto_save_enabled': True,
                'model_preference': 'caigpt'
            })

        try:
            return jsonify({
                'id': pref.get('id'),
                'user_id': pref.get('user_id'),
                'theme': pref.get('theme', 'light'),
                'editor_theme': pref.get('editor_theme', 'vs-dark'),
                'editor_font_size': pref.get('editor_font_size', 14),
                'editor_font_family': pref.get('editor_font_family', "'Consolas', 'Monaco'"),
                'editor_word_wrap': pref.get('editor_word_wrap', 'on'),
                'minimap_enabled': bool(int(pref.get('minimap_enabled') or 1)),
                'auto_save_enabled': bool(int(pref.get('auto_save_enabled') or 1)),
                'last_code': pref.get('last_code') or '',
                'last_session_id': pref.get('last_session_id'),
                'language': pref.get('language', 'cpp'),
                'model_preference': pref.get('model_preference', 'caigpt'),
                'ui_layout': pref.get('ui_layout', 'split'),
                'console_height': pref.get('console_height', 200),
                'updated_at': str(pref.get('updated_at')) if pref.get('updated_at') else None
            })
        except (TypeError, ValueError) as json_error:
            logger.error(f"Failed to serialize preferences data: {str(json_error)}")
            return jsonify({
                'theme': 'light',
                'editor_theme': 'vs-dark',
                'editor_font_size': 14,
                'error': 'Preferences data corrupted'
            })
    except Exception as e:
        logger.error(f"Failed to get preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/preferences', methods=['POST'])
@login_required
def update_user_preferences():
    """Update user preferences"""
    data = request.get_json() or {}

    allowed_fields = [
        'theme', 'editor_theme', 'editor_font_size', 'editor_font_family',
        'editor_word_wrap', 'minimap_enabled', 'auto_save_enabled',
        'last_code', 'last_session_id', 'language', 'model_preference',
        'ui_layout', 'console_height'
    ]

    update_data = {}
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field in ['minimap_enabled', 'auto_save_enabled']:
                value = 1 if value else 0
            update_data[field] = value

    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        existing = cursor.fetchone()

        if existing:
            set_clause = ', '.join([f"{k} = %s" for k in update_data.keys()])
            values = list(update_data.values()) + [current_user.id]

            cursor.execute(f'''
            UPDATE ai_user_preferences SET {set_clause}, updated_at = NOW()
            WHERE user_id = %s
            ''', values)
        else:
            insert_fields = ['user_id'] + list(update_data.keys())
            placeholders = ', '.join(['%s'] * len(insert_fields))
            all_values = [current_user.id] + list(update_data.values())

            cursor.execute(f'''
            INSERT INTO ai_user_preferences ({', '.join(insert_fields)})
            VALUES ({placeholders})
            ''', all_values)

        conn.commit()

        logger.info(f"Updated preferences for user {current_user.id}: {list(update_data.keys())}")

        return jsonify({
            'success': True,
            'message': '偏好设置已保存到数据库',
            'updated_fields': list(update_data.keys())
        })

    except Exception as e:
        logger.error(f"Failed to update preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/preferences/code', methods=['POST'])
@login_required
def save_editor_code():
    """Save editor code to database (auto-save)"""
    data = request.get_json() or {}
    code = data.get('code', '')

    if len(code) > 100000:
        return jsonify({'error': '代码过长，超过限制'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO ai_user_preferences (user_id, last_code, updated_at)
        VALUES (%s, %s, NOW())
        ON DUPLICATE KEY UPDATE last_code = VALUES(last_code), updated_at = NOW()
        ''', (current_user.id, code))

        conn.commit()

        return jsonify({
            'success': True,
            'message': f'代码已保存（{len(code)} 字符）'
        })

    except Exception as e:
        logger.error(f"Failed to save code: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@ai_bp.route('/preferences/code', methods=['GET'])
@login_required
def get_saved_code():
    conn = get_db_connection()
    if not conn:
        return jsonify({'code': ''})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT last_code FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        result = cursor.fetchone()

        return jsonify({
            'code': result.get('last_code') or '' if result else ''
        })

    except Exception as e:
        logger.error(f"Failed to get saved code: {str(e)}")
        return jsonify({'code': ''})
    finally:
        conn.close()


@ai_bp.route('/preferences/reset', methods=['POST'])
@login_required
def reset_user_preferences():
    """Reset user preferences to default"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute('''
        DELETE FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        conn.commit()

        return jsonify({
            'success': True,
            'message': '偏好设置已重置为默认值'
        })

    except Exception as e:
        logger.error(f"Failed to reset preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== 模型切换 API =====

@ai_bp.route('/models/switch', methods=['POST'])
@login_required
def switch_model():
    data = request.get_json() or {}
    provider_name = data.get('provider', '')

    if not provider_name:
        return jsonify({'error': 'Provider name is required'}), 400

    try:
        manager = _get_provider_manager()
        success = manager.switch_provider(provider_name)
        if success:
            model_info = manager.get_current_model_info()
            return jsonify({
                'success': True,
                'message': f'已切换到 {model_info["name"]}',
                'model': model_info
            })
        else:
            return jsonify({'error': f'无法切换到 {provider_name}'}), 400
    except Exception as e:
        logger.error(f"Model switch failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/models/current', methods=['GET'])
@login_required
def get_current_model():
    try:
        manager = _get_provider_manager()
        model_info = manager.get_current_model_info()
        return jsonify({'model': model_info})
    except Exception as e:
        logger.error(f"Failed to get current model: {e}")
        return jsonify({'error': str(e)}), 500


# ===== 记忆管理 API =====

@ai_bp.route('/memories', methods=['GET'])
@login_required
def get_memories():
    try:
        memory_svc = get_memory_service()
        memory_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 50))
        page = int(request.args.get('page', 1))

        offset = (page - 1) * limit
        memories = memory_svc.get_memories(
            current_user.id,
            memory_type=memory_type,
            limit=offset + limit,
            active_only=True
        )

        return jsonify({
            'success': True,
            'memories': memories[offset:offset + limit],
            'total': len(memories),
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"Failed to get memories: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories', methods=['POST'])
@login_required
def add_memory():
    data = request.get_json() or {}
    memory_type = data.get('type', 'note')
    content = data.get('content', '')
    importance = data.get('importance', 5)
    tags = data.get('tags', [])

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    try:
        memory_svc = get_memory_service()
        memory_id = memory_svc.add_memory(
            current_user.id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            tags=tags
        )
        if memory_id:
            return jsonify({'success': True, 'memory_id': memory_id})
        else:
            return jsonify({'error': 'Failed to add memory'}), 500
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/search', methods=['GET'])
@login_required
def search_memories():
    keyword = request.args.get('keyword', '')
    limit = int(request.args.get('limit', 20))

    if not keyword or len(keyword) < 2:
        return jsonify({'error': 'Keyword must be at least 2 characters'}), 400

    try:
        memory_svc = get_memory_service()
        memories = memory_svc.search_memories(current_user.id, keyword, limit=limit)
        return jsonify({'success': True, 'memories': memories})
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/<int:memory_id>', methods=['DELETE'])
@login_required
def delete_memory(memory_id):
    try:
        memory_svc = get_memory_service()
        success = memory_svc.delete_memory(current_user.id, memory_id)
        if success:
            return jsonify({'success': True, 'message': '记忆已删除'})
        else:
            return jsonify({'error': '记忆不存在或无权删除'}), 404
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/stats', methods=['GET'])
@login_required
def get_memory_stats():
    try:
        memory_svc = get_memory_service()
        stats = memory_svc.get_memory_stats(current_user.id)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/summary', methods=['GET'])
@login_required
def get_memory_summary():
    try:
        memory_svc = get_memory_service()
        summary = memory_svc.get_memory_summary(current_user.id)
        if summary is None:
            memory_svc.update_memory_summary(current_user.id)
            summary = memory_svc.get_memory_summary(current_user.id)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        logger.error(f"Failed to get memory summary: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/evolve', methods=['POST'])
@login_required
def evolve_memories():
    try:
        memory_svc = get_memory_service()
        result = memory_svc.evolve_memories(current_user.id)
        return jsonify({
            'success': True,
            'message': '记忆进化完成',
            'result': result
        })
    except Exception as e:
        logger.error(f"Memory evolution failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memories/radar', methods=['GET'])
@login_required
def get_radar_chart():
    """获取学习能力雷达图数据"""
    try:
        memory_svc = get_memory_service()
        radar_data = memory_svc.get_radar_chart_data(current_user.id)
        return jsonify({
            'success': True,
            'radar': radar_data
        })
    except Exception as e:
        logger.error(f"Failed to get radar chart: {e}")
        return jsonify({'error': str(e)}), 500


# ===== 编译器查找工具函数 =====

def find_gpp_compiler():
    """
    查找 g++ 编译器的完整路径（跨平台支持）
    
    Returns:
        str: g++ 的完整路径，如果找不到则返回 None
    """
    import shutil
    import platform

    logger.info(f"正在查找 C++ 编译器 (平台: {platform.system()})")

    # 1. 首先检查环境变量配置
    env_gpp = os.environ.get('GPP_PATH', '').strip()
    if env_gpp and os.path.isfile(env_gpp):
        logger.info(f"✓ 从环境变量 GPP_PATH 找到编译器: {env_gpp}")
        return env_gpp

    # 2. 使用 shutil.which 查找系统 PATH 中的 g++（最可靠的方式）
    gpp_in_path = shutil.which('g++')
    if gpp_in_path:
        logger.info(f"✓ 从系统 PATH 找到编译器: {gpp_in_path}")
        return gpp_in_path

    # 3. 平台特定路径搜索
    if platform.system() == 'Windows':
        windows_paths = [
            # MinGW-w64 (最常见的)
            r'C:\mingw64\bin\g++.exe',
            r'C:\mingw32\bin\g++.exe',
            r'C:\Program Files\mingw64\bin\g++.exe',
            r'C:\Program Files (x86)\mingw64\bin\g++.exe',
            
            # MSYS2 / Cygwin
            r'C:\msys64\mingw64\bin\g++.exe',
            r'C:\msys32\mingw64\bin\g++.exe',
            r'C:\cygwin64\bin\g++.exe',
            r'C:\cygwin\bin\g++.exe',
            
            # TDM-GCC
            r'C:\TDM-GCC-64\bin\g++.exe',
            r'C:\TDM-GCC-32\bin\g++.exe',
            
            # LLVM/Clang (作为备选)
            r'C:\Program Files\LLVM\bin\clang++.exe',
        ]

        for path in windows_paths:
            if os.path.isfile(path):
                logger.info(f"✓ 在 Windows 常见路径找到编译器: {path}")
                return path

        # 尝试在 Program Files 中递归搜索（仅一层）
        program_files_dirs = [
            os.environ.get('ProgramFiles', r'C:\Program Files'),
            os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
        ]
        
        for base_dir in program_files_dirs:
            if not os.path.isdir(base_dir):
                continue
            
            for item in os.listdir(base_dir):
                if 'mingw' in item.lower() or 'gcc' in item.lower() or 'llvm' in item.lower():
                    potential_path = os.path.join(base_dir, item, 'bin', 'g++.exe')
                    if os.path.isfile(potential_path):
                        logger.info(f"✓ 在 Program Files 搜索到编译器: {potential_path}")
                        return potential_path
                    
                    clang_path = os.path.join(base_dir, item, 'bin', 'clang++.exe')
                    if os.path.isfile(clang_path):
                        logger.info(f"✓ 找到 Clang++ 作为备选: {clang_path}")
                        return clang_path
    
    else:
        # Linux/macOS/Docker 容器
        linux_mac_paths = [
            '/usr/bin/g++',
            '/usr/local/bin/g++',
            '/opt/homebrew/bin/g++',       # macOS Homebrew
            '/opt/local/bin/g++',           # MacPorts
            '/usr/bin/c++',                 # 备选
        ]
        
        for path in linux_mac_paths:
            if os.path.isfile(path):
                logger.info(f"✓ 在 Linux/macOS 路径找到编译器: {path}")
                return path
        
        # Docker 容器中可能通过 apt 安装在其他位置
        try:
            result = subprocess.run(
                ['dpkg', '-L', 'g++'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.endswith('/g++') and os.path.isfile(line):
                        logger.info(f"✓ 通过 dpkg 找到编译器: {line}")
                        return line
        except Exception as e:
            logger.debug(f"dpkg 查询失败: {e}")

    # 4. 最后尝试：使用 where/which 命令查找
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['where', 'g++'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                first_match = result.stdout.strip().split('\n')[0].strip()
                if os.path.isfile(first_match):
                    logger.info(f"✓ 通过 where 命令找到编译器: {first_match}")
                    return first_match
        else:
            result = subprocess.run(['which', 'g++'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                first_match = result.stdout.strip()
                if os.path.isfile(first_match):
                    logger.info(f"✓ 通过 which 命令找到编译器: {first_match}")
                    return first_match
    except Exception as e:
        logger.debug(f"where/which 命令失败: {e}")

    # 都找不到，返回 None
    logger.warning("✗ 未找到 C++ 编译器 (g++)")
    
    if platform.system() != 'Windows':
        logger.warning("提示：在 Docker/Linux 环境中，请确保已安装 g++：")
        logger.warning("  - Dockerfile: RUN apt-get install -y g++")
        logger.warning("  - 或运行时: apt-get update && apt-get install -y g++")
    
    return None


def get_compiler_info():
    import platform

    gpp_path = find_gpp_compiler()
    
    if not gpp_path:
        return {
            'available': False,
            'name': '未安装',
            'version': '',
            'path': ''
        }

    try:
        result = subprocess.run(
            [gpp_path, '--version'],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if platform.system() == 'Windows' else 0
        )
        
        version_info = result.stdout.split('\n')[0] if result.stdout else ''
        
        return {
            'available': True,
            'name': os.path.basename(gpp_path),
            'version': version_info.replace('g++', '').strip(),
            'path': gpp_path
        }
    except Exception as e:
        return {
            'available': True,
            'name': os.path.basename(gpp_path),
            'version': '(无法获取版本)',
            'path': gpp_path
        }


@ai_bp.route('/code/compiler-info', methods=['GET'])
@login_required
def get_compiler_info_api():
    """获取编译器信息 API"""
    info = get_compiler_info()
    return jsonify(info)
