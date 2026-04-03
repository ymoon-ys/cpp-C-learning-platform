from flask import Blueprint, request, jsonify, current_app, render_template, Response
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import AIConversation, Problem
import requests
import base64
import json
import os
from PIL import Image
import logging
from datetime import datetime

ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai')

# 创建速率限制器
ai_limiter = Limiter(key_func=get_remote_address)


@ai_bp.route('/')
@login_required
def index():
    return render_template('ai_assistant.html')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_ocr_token_cache = {"access_token": None, "expires_at": 0}

dialog_history_cache = {}

CAIGPT_SYSTEM_PROMPT = """
你是一位专业的 C++ 程序设计教学智能助手（基于 Qwen3.0 大模型），你的核心任务是帮助大学生学习 C++ 编程。你的交互风格参考豆包（Doubao）AI 助手：**简洁、专业、高效**。

## 🎯 核心定位

- **角色**：C++ 编程教练 + 代码审查专家
- **原则**：引导思考 > 直接给答案（绝不直接替学生完成作业）
- **风格**：像豆包一样简洁明了，避免冗长说教
- **能力**：
  - ✅ 分析代码问题并提供修改建议
  - ✅ 解释 C++ 知识点（用通俗语言）
  - ✅ 提供解题思路和方法
  - ✅ 支持文件上传分析（代码/图片/PDF）
  - ✅ 生成可直接运行的代码示例

---

## 💬 交互规范

### 1. 回答格式

**必须使用 Markdown 格式**，结构清晰：

```markdown
## 问题分析
（简要说明问题本质）

## 解决方案
（分步骤讲解）

### 代码实现
\`\`\`cpp
// 你的代码
\`\`\`

### 运行结果
（预期输出）

## 扩展思考
（相关知识点或优化建议）
```

### 2. 代码输出规则

- **所有 C++ 代码** 必须使用 ` ```cpp ... ``` ` 包裹
- 代码要有**注释**，解释关键步骤
- 提供**完整可运行**的示例（包含 main 函数）
- 如果学生上传了代码文件，**自动同步到右侧编辑器**

### 3. 文件处理能力

当学生上传文件时：

| 文件类型 | 处理方式 |
|---------|---------|
| `.cpp` `.h` | 分析代码质量、指出问题、提供优化建议 |
| `.txt` `.md` | 解析内容并回答相关问题 |
| 图片 (`.png` `.jpg`) | OCR 识别后分析内容 |
| PDF | 提取文本后进行分析 |

**响应模板**：
```
📎 已收到文件：[文件名] ([大小])

📊 分析结果：
[具体分析内容]

💡 建议：
[改进建议或下一步操作]

✏️ 已将代码同步到编辑器（如果是代码文件）
```

---

## 🎓 分场景处理流程

### 场景 A：学生提问概念/语法

**示例**：
> 学生："指针是什么？"

**回答模板**：
```markdown
## 指针（Pointer）基础

### 定义
指针是存储**内存地址**的变量。

### 核心概念
- **声明**：`int* ptr;` （ptr 是一个指向 int 的指针）
- **取地址**：`&var` （获取变量的内存地址）
- **解引用**：`*ptr` （访问指针指向的值）

### 示例代码
\`\`\`cpp
#include <iostream>
using namespace std;

int main() {
    int num = 42;
    int* ptr = &num;  // ptr 指向 num

    cout << "值: " << *ptr << endl;  // 输出 42
    cout << "地址: " << ptr << endl; // 输出内存地址

    return 0;
}
\`\`\`

### 关键要点
⚠️ 未初始化的指针是危险的！
🔗 相关知识：引用(&)、动态内存(new/delete)
```

---

### 场景 B：学生上传代码请求分析

**示例**：
> 学生：[上传 main.cpp]

**回答模板**：
```markdown
## 📊 代码分析报告

### 基本信息
- **文件**：main.cpp
- **行数**：XX 行
- **复杂度**：O(n)

### ✅ 优点
1. ...
2. ...

### ⚠️ 问题与建议

| # | 位置 | 问题类型 | 当前代码 | 建议修改 |
|---|------|---------|---------|---------|
| 1 | L15 | 内存泄漏 | `new int[n]` | 改为 `vector<int>` 或添加 `delete[]` |
| 2 | L23 | 边界检查缺失 | `arr[i]` | 添加 `if (i < n)` 判断 |

### 🔧 优化后的代码
\`\`\`cpp
// [优化后的完整代码]
\`\`\`

✏️ **已将此代码同步到右侧编辑器**
```

---

### 场景 C：学生要求解题（不给直接答案）

**原则**：引导学生思考，而非直接给出答案

**回答流程**：
1. **理解题目** → 用自己的话复述题目要求
2. **拆解问题** → 将大问题拆成小步骤
3. **提示方向** → 给出关键知识点提示
4. **框架代码** → 提供伪代码或部分实现
5. **鼓励尝试** → 让学生自己完成剩余部分

**话术示例**：
- ❌ "这是答案：..."
- ✅ "这道题的核心是考察 [知识点]。你可以先试试 [第一步]，如果遇到困难再问我！"
- ✅ "我理解你想解决 [问题]。让我们一步步来：首先考虑 [关键点]..."

---

### 场景 D：学生坚持要完整答案

**委婉拒绝 + 引导回归**：
```
我理解你想要完整的解决方案，但直接给你答案会错过学习的机会 😊

让我换个方式帮你：
1️⃣ 我可以给你一个**代码框架**，你需要填空关键部分
2️⃣ 或者我们可以一起**调试**你现有的代码

你更倾向哪种方式？
```

---

## ⚙️ 技术配置

- **模型版本**：Qwen3.0 (8B)
- **语言**：C++ (C++11/14/17 标准)
- **编译器假设**：g++ (MinGW/GCC)
- **代码风格**：Google C++ Style Guide（简化版）

## 🚫 禁止事项

1. **禁止**直接给出竞赛题/作业的完整 AC 代码
2. **禁止**使用 Python 或其他非 C++ 语言作为主要示例
3. **禁止**在未确认需求时一次性输出大量代码
4. **禁止**忽略学生上传的文件内容
5. **禁止**使用过于学术化的术语（要用通俗易懂的语言）

## ✨ 特色功能

当检测到以下情况时，主动提供额外帮助：

- **代码有 bug** → 自动高亮错误行 + 解释原因 + 提供修复
- **性能瓶颈** → 分析时间/空间复杂度 + 优化建议
- **安全问题** → 警告缓冲区溢出、SQL注入等风险
- **最佳实践** → 推荐更现代的 C++ 写法（如用 `auto`、range-for 等）

---

现在，请以这个身份开始与学生对话。记住：你是**专业的、友好的、高效的** C++ 编程助手！
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
    """Build message list with dynamic prompt injection"""
    system_prompt = build_dynamic_system_prompt(user, problem_id)
    messages = [{"role": "system", "content": system_prompt}]

    if history and isinstance(history, list):
        for msg in history:
            if msg.get("role") != "system":
                messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    return messages


def build_dynamic_system_prompt(user=None, problem_id=None):
    """Build dynamic system prompt based on user context and problem info"""
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
                    if sub.get('status') == 'accepted':
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
    models = []
    for model_key, model_info in AI_MODELS.items():
        available = model_key == 'local' or bool(model_info['api_key'])
        models.append({
            'key': model_key,
            'name': model_info['name'],
            'available': available
        })
    return jsonify({'models': models})

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
        elif model_name == 'caigpt':
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
    model_name = data.get('model', 'gemini')

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
        return "抱歉，我 currently only support some basic questions. Please try asking something else about C++."

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
    """Handle CAIgpt model chat request - call Ollama API directly"""
    user_id = current_user.id if current_user.is_authenticated else 0

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
        ollama_url = f"{current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat"
        timeout = current_app.config.get('OLLAMA_TIMEOUT', 60)
        model_name = current_app.config.get('OLLAMA_MODEL', 'qwen3-coder:30b')

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(ollama_url, json=payload, timeout=timeout)
            if response.status_code == 200:
                result = response.json()
                response_message = result['message']['content']
            else:
                logger.error(f"Ollama API returned error: {response.text}")
                response_message = "Sorry, I'm having trouble connecting to the AI service right now. Please try again later."
        except requests.Timeout:
            logger.error("Ollama API request timeout")
            response_message = "Request timeout. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
            response_message = "Cannot connect to local AI service. Please make sure Ollama is running."
        except Exception as e:
            logger.error(f"Request to Ollama API failed: {str(e)}")
            response_message = f"AI service error: {str(e)}"

        if user_id > 0:
            save_message(user_id, "user", user_message, [image_data] if has_image and image_data else None)
            save_message(user_id, "assistant", response_message)

        conversation = AIConversation(
            user_id=user_id if user_id > 0 else None,
            problem_id=problem_id,
            question=question,
            answer=response_message,
            model_name='CAIgpt',
            conversation_type=conversation_type,
            has_code=has_code,
            has_image=has_image
        )
        conversation.save()

        return jsonify({
            'success': True,
            'answer': response_message,
            'model': 'CAIgpt',
            'conversation_id': conversation.id
        })

    except Exception as e:
        logger.error(f"CAIgpt processing failed: {str(e)}")
        return jsonify({'error': f'CAIgpt processing failed: {str(e)}'}), 500


def handle_caigpt_chat_stream(model_info, question, problem_id, conversation_type, has_code, has_image, image_data):
    """Handle CAIgpt model chat request with streaming support"""
    user_id = current_user.id if current_user.is_authenticated else 0

    if has_image and image_data:
        ocr_text, error = baidu_ocr(image_data)
        if error:
            logger.error(f"OCR recognition failed: {error}")
            user_message = f"{question}\n\n[Image content]"
        else:
            user_message = f"{question}\n\n[Image content]\n{ocr_text}"
    else:
        user_message = question

    # 获取配置信息（在应用上下文中）
    ollama_url = f"{current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat"
    timeout = current_app.config.get('OLLAMA_TIMEOUT', 120)
    model_name = current_app.config.get('OLLAMA_MODEL', 'qwen3-coder:30b')
    max_cache = current_app.config.get('AI_MAX_HISTORY', 20)

    # 构建消息（在应用上下文中）
    history = get_user_history(user_id, max_history=max_cache)
    user = current_user if current_user.is_authenticated else None
    messages = build_messages(user_message, history, user=user, problem_id=problem_id)

    def generate():
        full_response = ""
        try:
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": True
            }

            response = requests.post(ollama_url, json=payload, timeout=timeout, stream=True)

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if 'message' in chunk_data and 'content' in chunk_data['message']:
                                chunk_content = chunk_data['message']['content']
                                full_response += chunk_content
                                yield f"data: {json.dumps({'content': chunk_content, 'done': False})}\n\n"

                            if chunk_data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue

                # 直接返回结果，不保存到数据库（避免应用上下文问题）
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
            else:
                error_msg = f"Ollama API error: {response.text}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"

        except requests.Timeout:
            error_msg = "Request timeout. Please try again."
            logger.error("Ollama streaming request timeout")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to local AI service. Please make sure Ollama is running."
            logger.error("Cannot connect to Ollama service for streaming")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            logger.error(f"CAIgpt streaming failed: {str(e)}")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


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

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    if model_name not in AI_MODELS:
        return jsonify({'error': 'Unsupported AI model'}), 400

    if model_name == 'auto':
        model_name = 'caigpt'

    if model_name == 'caigpt':
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
    """Get the number of messages in a session"""
    try:
        conn = get_db_connection()
        if not conn:
            return 0

        cursor = conn.cursor()
        cursor.execute('''
        SELECT COUNT(*) as count FROM caigpt_dialog_history WHERE session_id = %s
        ''', (session_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0
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

    import subprocess
    import tempfile
    import os
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

    import re

    functions = re.findall(r'(?:void|int|float|double|char|string|bool|auto)\s+(\w+)\s*\([^)]*)\s*{', code)
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
        conn.close()

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
    from reportlab.platyparagraph import Paragraph, Spacer
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

    ollama_url = f"{current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate"
    model_name = current_app.config.get('OLLAMA_MODEL', 'qwen3:8b')

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
        response = requests.post(
            ollama_url.replace('/api/chat', '/api/generate'),
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 100,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "stop": ["\n\n", "```", "|||"]
                }
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('response', '').strip()
            suggestions = [s.strip() for s in text.split('|||') if s.strip()]
            return jsonify({
                'suggestions': suggestions[:5],
                'context': current_line[:50]
            })
        else:
            return jsonify({'suggestions': []})

    except Exception as e:
        logger.error(f"Code completion failed: {str(e)}")
        return jsonify({'suggestions': []})


# ===== 用户偏好设置 API =====

@ai_bp.route('/preferences', methods=['GET'])
@login_required
def get_user_preferences():
    """Get current user's preferences"""
    conn = get_db_connection()
    if not conn:
        return jsonify({})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT * FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        pref = cursor.fetchone()
        conn.close()

        if not pref:
            return jsonify({
                'theme': 'light',
                'editor_theme': 'vs-dark',
                'editor_font_size': 14,
                'minimap_enabled': True,
                'auto_save_enabled': True,
                'model_preference': 'caigpt'
            })

        return jsonify({
            'id': pref['id'],
            'user_id': pref['user_id'],
            'theme': pref.get('theme', 'light'),
            'editor_theme': pref.get('editor_theme', 'vs-dark'),
            'editor_font_size': pref.get('editor_font_size', 14),
            'editor_font_family': pref.get('editor_font_family', "'Consolas', 'Monaco'"),
            'editor_word_wrap': pref.get('editor_word_wrap', 'on'),
            'minimap_enabled': bool(pref.get('minimap_enabled', 1)),
            'auto_save_enabled': bool(pref.get('auto_save_enabled', 1)),
            'last_code': pref.get('last_code'),
            'last_session_id': pref.get('last_session_id'),
            'language': pref.get('language', 'cpp'),
            'model_preference': pref.get('model_preference', 'caigpt'),
            'ui_layout': pref.get('ui_layout', 'split'),
            'console_height': pref.get('console_height', 200),
            'updated_at': str(pref.get('updated_at'))
        })
    except Exception as e:
        logger.error(f"Failed to get preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
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
    """Get saved editor code from database"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'code': ''})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
        SELECT last_code FROM ai_user_preferences WHERE user_id = %s
        ''', (current_user.id,))

        result = cursor.fetchone()
        conn.close()

        return jsonify({
            'code': result.get('last_code') or ''
        })

    except Exception as e:
        logger.error(f"Failed to get saved code: {str(e)}")
        return jsonify({'code': ''})
    finally:
        if conn:
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


# ===== 编译器查找工具函数 =====

def find_gpp_compiler():
    """
    查找 g++ 编译器的完整路径（跨平台支持）
    
    Returns:
        str: g++ 的完整路径，如果找不到则返回 None
    """
    import shutil
    import platform

    # 1. 首先检查环境变量配置
    env_gpp = os.environ.get('GPP_PATH', '').strip()
    if env_gpp and os.path.isfile(env_gpp):
        return env_gpp

    # 2. 使用 shutil.which 查找系统 PATH 中的 g++
    gpp_in_path = shutil.which('g++')
    if gpp_in_path:
        return gpp_in_path

    # 3. Windows 特定路径搜索
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
            
            # Visual Studio (需要通过 vcvarsall.bat 设置环境)
            # 这里不直接查找，因为 VS 的 cl.exe 不是 g++
            
            # LLVM/Clang (作为备选)
            r'C:\Program Files\LLVM\bin\clang++.exe',
        ]

        for path in windows_paths:
            if os.path.isfile(path):
                logger.info(f"Found g++ at: {path}")
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
                        logger.info(f"Found g++ at: {potential_path}")
                        return potential_path
                    
                    # 也尝试 clang++
                    clang_path = os.path.join(base_dir, item, 'bin', 'clang++.exe')
                    if os.path.isfile(clang_path):
                        logger.info(f"Found clang++ at: {clang_path} (will use as fallback)")
                        return clang_path

    # 4. Linux/macOS 常见路径
    else:
        linux_mac_paths = [
            '/usr/bin/g++',
            '/usr/local/bin/g++',
            '/opt/homebrew/bin/g++',
            '/opt/local/bin/g++',  # MacPorts
        ]
        
        for path in linux_mac_paths:
            if os.path.isfile(path):
                return path

    # 5. 最后尝试：使用 where/which 命令查找
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
                    return first_match
        else:
            result = subprocess.run(['which', 'g++'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                first_match = result.stdout.strip()
                if os.path.isfile(first_match):
                    return first_match
    except Exception as e:
        logger.debug(f"where/which command failed: {e}")

    # 都找不到，返回 None
    logger.warning("Could not find g++ compiler")
    return None


def get_compiler_info():
    """获取编译器信息（用于前端显示）"""
    gpp_path = find_gpp_compiler()
    
    if not gpp_path:
        return {
            'available': False,
            'name': '未安装',
            'version': '',
            'path': ''
        }

    import subprocess
    
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
