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

dialog_history_cache = {}

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

CAIGPT_SYSTEM_PROMPT = """
你是 **CAIgpt**，一位专为中国大学生设计的 C++ 编程教学智能助手。你拥有长期记忆能力，能记住每位学生的学习历程、薄弱环节和偏好，提供真正个性化的辅导。

---

## 一、核心身份

- **角色**：C++ 编程私教 + 代码审查专家 + 学习陪伴者
- **使命**：让每个学生通过"思考→实践→反思"的循环真正掌握 C++
- **底线原则**：**绝不直接替学生完成作业或给出完整可运行的答案代码**
- **风格**：简洁专业、循循善诱、因材施教

---

## 二、场景化交互规则

### 场景1：学生提出问题（未给出代码）

**目标**：引导思考，激发自主解题能力。

1. **第一步：问题确认**
   - 用自己的话复述问题核心，确认理解无误
   - 提问："我理解你想解决的是 [问题核心]，对吗？"

2. **第二步：引导思考**
   - 提出引导性问题，逐步拆解问题
   - 每次只推进一个步骤，等待学生回应
   - 话术："要解决这个问题，你觉得第一步应该考虑什么？"

3. **第三步：提供思路框架**
   - 给出伪代码或算法思路（非 C++ 代码）
   - 标注关键判断点和循环逻辑
   - 话术："你可以按这个思路试试，遇到卡点随时告诉我"

4. **严格禁止**：
   - ❌ 一次性输出"问题分析+引导思考+解题思路+代码框架+流程图"
   - ❌ 提供任何可直接运行的代码
   - ✅ 只输出当前阶段的引导内容，等待学生回应后再推进

### 场景2：学生给出了自己的解题答案/思路

**目标**：提供可视化思考工具，强化理解。

1. **第一步：肯定与确认**
   - 先肯定学生的思考："你的思路很有价值，我们来一起把它可视化。"
   - 根据学生的答案，生成一个**详细的流程图**（用文字描述），解释每一步的判断和逻辑

2. **第二步：引导深化**
   - 提问："这个流程图和你最初的想法有什么不同？有没有可以优化的地方？"
   - **禁止**提供任何可直接运行的代码

### 场景3：学生给出代码片段

**目标**：精准纠错，结合知识点，不直接给正确代码。

1. **第一步：定位错误**
   - 明确指出代码片段中的语法错误或逻辑问题
   - 如"这里缺少了分号"、"这个判断条件逻辑反了"

2. **第二步：关联知识点**
   - 解释错误背后的 C++ 知识点
   - 如"在 C++ 中，变量必须先声明后使用"、"`=`是赋值运算符，`==`才是比较运算符"

3. **第三步：提供修改方向**
   - 给出修改思路："你可以尝试在这个地方添加一个判断，确保输入的合法性。"
   - 如果代码正确，提示下一步："这段代码逻辑正确，可以考虑如何优化性能或添加异常处理。"
   - **禁止**直接补全或重写代码

### 场景4：学生给出整段代码

**目标**：全面分析，提供理解，而非直接纠错。

1. **第一步：整体评估**
   - 先给出整体评价："我理解了你的代码，它的核心逻辑是……"
   - 如果存在错误，按场景3的规则进行纠错
   - 如果没有错误，提供理解和优化建议："你的代码实现了功能，我们可以从可读性和效率上进行一些优化，比如……"
   - **禁止**直接提供优化后的完整代码

### 场景5：学生坚持要答案

**目标**：坚守原则，委婉拒绝，回归引导。

1. **话术模板**：
   - "直接给答案会错过思考的乐趣，我们一起拆解这道题的逻辑吧，你会更有成就感！"
   - "学习的关键在于过程，我可以帮你一步步分析，但答案需要你自己写出来哦。"
   - "我相信你已经有思路了，我们来验证一下你的想法怎么样？"

2. **行动**：立即将对话拉回场景1或场景3，重新开始引导

---

## 三、代码类型（新代码开发）

当学生开始编写一段新的 C++ 代码时：

1. **纠错模式**：如果代码有错，按场景3的规则处理
2. **引导模式**：如果代码正确，提示下一步："这段基础功能已经实现了，你可以考虑添加用户交互，或者处理边界情况。"

---

## 四、知识点类型

当学生提问 C++ 知识点时：

1. **详细解答**：清晰定义该知识点，解释其作用、用法和注意事项
2. **知识衍生**：提供相关拓展内容：
   - 讲解"指针"时，衍生到"引用"和"动态内存分配"
   - 讲解"类"时，衍生到"封装"、"继承"和"多态"
3. **示例辅助**：提供极简的代码片段辅助说明，但**绝不提供完整可运行的程序**

---

## 五、记忆与个性化

你拥有长期记忆能力，能记住每位学生的：
- **知识掌握情况**：已掌握/未掌握的知识点
- **薄弱环节**：经常出错的语法或逻辑
- **学习偏好**：喜欢通过示例/图解/类比等方式学习
- **常见错误**：重复犯的错误模式

**记忆使用规则**：
- 如果记忆显示学生之前学过某知识点，不要重复基础解释，直接进阶
- 如果记忆显示学生在某方面反复出错，主动提醒并加强该方面练习
- 如果记忆显示学生偏好某种学习方式，优先使用该方式

---

## 六、回答格式规范

1. **必须使用 Markdown 格式**，结构清晰
2. **所有 C++ 代码**必须使用 ` ```cpp ... ``` ` 包裹
3. 代码片段要有**注释**，解释关键步骤
4. 知识点讲解使用**通俗语言**，避免过于学术化

---

## 七、技术配置

- **语言**：C++（C++11/14/17 标准）
- **编译器假设**：g++ (MinGW/GCC)
- **代码风格**：Google C++ Style Guide（简化版）

---

## 八、禁止事项

1. **禁止**直接给出竞赛题/作业的完整可运行代码
2. **禁止**使用 Python 或其他非 C++ 语言作为主要示例
3. **禁止**在未确认需求时一次性输出大量代码
4. **禁止**忽略学生上传的文件内容
5. **禁止**一次性输出完整的问题分析+解题思路+代码框架+流程图
6. **禁止**直接补全或重写学生的代码（只指出方向）

---

## 九、兜底规则

- **无法识别**：当无法识别图片内容或信息不足时，应说："我需要更清晰的图片或文字描述，才能为你提供 C++ 相关的引导。"
- **话题切换**：当发现学生问题与上下文无关时，先确认再处理，避免答非所问
- **超纲问题**：如果问题超出 C++ 范围，礼貌说明并尝试关联到 C++ 知识

---

现在，请以 CAIgpt 的身份开始与学生对话。记住你的核心使命：**让学生通过自己的思考掌握 C++，而不是依赖你给出的答案。**
"""

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
                images TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_session (user_id, session_id)
            )
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
                INDEX idx_user_id (user_id)
            )
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
                INDEX idx_user_id (user_id)
            )
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
                last_code TEXT,
                last_session_id INT,
                language VARCHAR(10) DEFAULT 'cpp',
                model_preference VARCHAR(50) DEFAULT 'caigpt',
                ui_layout VARCHAR(20) DEFAULT 'split',
                console_height INT DEFAULT 200,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id)
            )
            ''')

            conn.commit()
            logger.info("CAIgpt database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")

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
    if user_id in dialog_history_cache:
        return dialog_history_cache[user_id]

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

        dialog_history_cache[user_id] = history
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

        cache_key = user_id if not session_id else f"{user_id}_{session_id}"
        if cache_key not in dialog_history_cache:
            dialog_history_cache[cache_key] = []
        msg = {"role": role, "content": content}
        if images:
            msg["images"] = images
        dialog_history_cache[cache_key].append(msg)

        if len(dialog_history_cache[cache_key]) > max_cache:
            dialog_history_cache[cache_key] = dialog_history_cache[cache_key][-max_cache:]

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

    messages.append({"role": "user", "content": user_message})

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

    if model_name not in AI_MODELS:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    model_info = AI_MODELS[model_name]

    if model_name != 'local':
        if not current_user.is_authenticated:
            return jsonify({'error': 'Login required to use this model'}), 401
        if model_name != 'caigpt' and not model_info['api_key']:
            return jsonify({'error': f'{model_info["name"]} API key not configured'}), 400

    try:
        if model_name == 'local':
            return handle_local_chat(question, problem_id, conversation_type, has_code, has_image, image_data)
        elif model_name == 'caigpt' or model_name == 'ollama':
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

    if model_name not in AI_MODELS:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    model_info = AI_MODELS[model_name]

    if model_name != 'local' and model_name != 'caigpt' and not model_info['api_key']:
        return jsonify({'error': f'{model_info["name"]} API key not configured'}), 400

    try:
        question = f"Please analyze the following C++ code, point out problems, errors, and improvement suggestions. Do not give complete correct code directly, but guide students to modify it themselves.\n\nCode:\n{code}"

        if problem_id:
            problem = Problem.get_by_id(problem_id)
            if problem:
                question = f"Problem requirements: {problem.description}\n\nInput format: {problem.input_format}\n\nOutput format: {problem.output_format}\n\nPlease analyze the following student code, point out problems, errors, and improvement suggestions. Do not give complete correct code directly, but guide students to modify it themselves.\n\nCode:\n{code}"

        if model_name == 'local':
            return handle_local_analyze(question)
        elif model_name == 'caigpt':
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
        response_message = get_ai_response(messages, stream=False)

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

    if model_name not in AI_MODELS:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    if model_name == 'caigpt' or model_name == 'ollama':
        model_info = AI_MODELS[model_name]
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

        if session_id in dialog_history_cache:
            del dialog_history_cache[session_id]

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

        dialog_history_cache.clear()

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
                stdin_data = input_data.encode('utf-8') if input_data else None

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
    """Analyze code complexity and provide visualization data"""
    data = request.get_json()
    code = data.get('code', '')

    if not code:
        return jsonify({'error': '代码不能为空'}), 400

    analysis = {
        'lines_of_code': len(code.split('\n')),
        'blank_lines': len([l for l in code.split('\n') if not l.strip()]),
        'comment_lines': len([l for l in code.split('\n') if l.strip().startswith('//')]),
        'code_lines': 0,
        'complexity': {'time': 'O(1)', 'space': 'O(1)'},
        'functions': [],
        'loops': [],
        'warnings': [],
        'suggestions': []
    }

    analysis['code_lines'] = analysis['lines_of_code'] - analysis['blank_lines'] - analysis['comment_lines']

    functions = re.findall(r'(?:void|int|float|double|char|string|bool|auto)\s+(\w+)\s*\(([^)]*)\)\s*(?:\{|;)', code)
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

    if any(x in code.lower() for x in ['malloc', 'calloc', 'realloc', 'free']):
        analysis['warnings'].append('检测到动态内存分配，注意内存泄漏风险')

    if 'new ' in code and 'delete ' not in code and '* new' not in code.replace('*delete', ''):
        analysis['warnings'].append('使用了 new 但未找到对应的 delete，可能存在内存泄漏')

    if 'scanf' in code or 'gets' in code:
        analysis['warnings'].append('使用了不安全的输入函数，建议使用更安全的替代方案')

    if len(analysis['loops']) > 3:
        analysis['complexity']['time'] = 'O(n^k) 或更高（嵌套循环较多）'

    if any('vector<' in code for _ in range(1)):
        analysis['suggestions'].append('✅ 使用了 vector，这是良好的 C++ 实践')

    if 'using namespace std;' in code:
        analysis['suggestions'].append('💡 在大型项目中建议避免使用 using namespace std;')

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
            'code': result.get('last_code') or ''
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
            limit=limit,
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
