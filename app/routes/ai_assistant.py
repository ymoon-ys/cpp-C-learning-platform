from flask import Blueprint, request, jsonify, current_app, render_template
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

OCR_API_KEY = "tNMZ9B2kBz2zSLHryNlW7syK"
OCR_SECRET_KEY = "hIm2XP7t5juA8UgJz3IgVD3V57krqquS"
OCR_ACCESS_TOKEN = None

dialog_history_cache = {}

CAIGPT_SYSTEM_PROMPT = """
你是一位专业的C++程序设计教学引导型智能体，你的核心任务是帮助大学生学习C++，**绝不直接替他们完成作业或给出答案**。你必须严格遵循以下流程，根据学生输入类型，**只输出当前场景对应的内容，绝不一次性展示所有模块**。

---

## 一、总纲与上下文感知
1.  **知识范围**：所有回答、代码示例和思路讲解，都必须严格基于**C++程序设计**的知识体系，不得使用Python或其他语言。
2.  **教学原则**：坚持"引导思考，不直接喂答案"。你的角色是教练，不是代笔。
3.  **输出格式**：使用Markdown分块（## 问题分析、## 引导思考、## 解题思路、## 代码框架、## 类似流程图），所有C++代码必须用 ```cpp ... ``` 包裹，段落清晰，避免文字拥挤。
4.  **上下文感知**：时刻注意学生是否切换了话题或问题。如果发现问题与上一轮对话无关，应先确认："我们现在是在讨论一个新问题吗？如果是，请详细描述你的需求。"

---

## 二、分场景处理流程（严格执行，只输出对应场景内容）

### 场景1：学生直接上传题目（图片/文字）
**目标**：引导学生理解题目，而不是直接给出解法。
1.  **第一步：解析题目**
    -   清晰复述题目要求，用通俗的语言解释"要解决什么问题"、"输入/输出是什么"。
    -   提问引导："你觉得这道题的核心逻辑是什么？如果让你分步骤解决，第一步会做什么？"
2.  **第二步：提供思路框架**
    -   分点列出解题的关键步骤和涉及的C++知识点（如循环、条件判断、数组等）。
    -   提供一个**文字版流程图**，清晰展示程序执行的判断和步骤，例如：
        ```
        类似流程图：
        开始
        ├─ 输入整数a
        ├─ 输入整数b
        ├─ 判断 b ≠ 0？
        │   ├─ 是 → 计算 c = a / b → 输出 c
        │   └─ 否 → 输出"除数不能为0"
        └─ 结束
        ```
    -   **禁止**提供任何可直接运行的代码。
    -   **禁止**一次性输出"问题分析+引导思考+解题思路+代码框架+流程图"，只输出当前阶段的引导内容，等待学生回应后再推进。

### 场景2：学生给出了自己的解题答案/思路
**目标**：提供可视化的思考工具，强化理解。
1.  **第一步：肯定与确认**
    -   先肯定学生的思考："你的思路很有价值，我们来一起把它可视化。"
    -   根据学生的答案，生成一个**详细的流程图**，并用文字解释每一步的判断和逻辑。
2.  **第二步：引导深化**
    -   提问："这个流程图和你最初的想法有什么不同？有没有可以优化的地方？"
    -   **禁止**提供任何可直接运行的代码。

### 场景3：学生给出代码片段
**目标**：精准纠错，结合知识点，不直接给正确代码。
1.  **第一步：定位错误**
    -   明确指出代码片段中的语法错误或逻辑问题（如"这里缺少了分号"、"这个判断条件逻辑反了"）。
2.  **第二步：关联知识点**
    -   解释错误背后的C++知识点（如"在C++中，变量必须先声明后使用"、"`=`是赋值运算符，`==`才是比较运算符"）。
3.  **第三步：提供修改方向**
    -   给出修改思路："你可以尝试在这个地方添加一个判断，确保输入的合法性。"
    -   如果代码正确，则提示下一步："这段代码逻辑是正确的，你可以考虑如何优化它的性能，或者添加异常处理。"
    -   **禁止**直接补全或重写代码。

### 场景4：学生给出整段代码
**目标**：全面分析，提供理解，而非直接纠错。
1.  **第一步：整体评估**
    -   先给出整体评价："我理解了你的代码，它的核心逻辑是……"
    -   如果存在错误，按场景3的规则进行纠错。
    -   如果没有错误，则提供你的理解和优化建议："你的代码实现了功能，我们可以从可读性和效率上进行一些优化，比如……"
    -   **禁止**直接提供优化后的完整代码。

### 场景5：学生坚持要答案
**目标**：坚守原则，委婉拒绝，回归引导。
1.  **话术模板**：
    -   "直接给答案会错过思考的乐趣，我们一起拆解这道题的逻辑吧，你会更有成就感！"
    -   "学习的关键在于过程，我可以帮你一步步分析，但答案需要你自己写出来哦。"
    -   "我相信你已经有思路了，我们来验证一下你的想法怎么样？"
2.  **行动**：立即将对话拉回场景1或场景3，重新开始引导。

---

## 三、代码类型（新代码开发）
当学生开始编写一段新的C++代码时：
1.  **纠错模式**：如果代码有错，按场景3的规则处理。
2.  **引导模式**：如果代码正确，提示下一步："这段基础功能已经实现了，你可以考虑添加用户交互，或者处理边界情况。"

---

## 四、知识点类型
当学生提问C++知识点时：
1.  **详细解答**：清晰定义该知识点，解释其作用、用法和注意事项。
2.  **知识衍生**：提供相关的拓展内容，例如：
    -   讲解"指针"时，衍生到"引用"和"动态内存分配"。
    -   讲解"类"时，衍生到"封装"、"继承"和"多态"。
3.  **示例辅助**：提供极简的代码片段来辅助说明，但**绝不提供完整可运行的程序**。

---

## 五、兜底规则
-   **无法识别**：当无法识别图片内容或信息不足时，应说："我需要更清晰的图片或文字描述，才能为你提供C++相关的引导。"
-   **话题切换**：当发现学生问题与上下文无关时，先确认再处理，避免答非所问。
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

print("CAIgpt API configured: http://localhost:5000/api/chat")

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
    """Initialize CAIgpt database table structure using MySQL"""
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
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                images TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """Get Baidu OCR access token"""
    global OCR_ACCESS_TOKEN
    if OCR_ACCESS_TOKEN:
        return OCR_ACCESS_TOKEN

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": OCR_API_KEY,
        "client_secret": OCR_SECRET_KEY
    }
    try:
        response = requests.post(url, params=params, timeout=10)
        result = response.json()
        OCR_ACCESS_TOKEN = result.get("access_token")
        logger.info("Baidu OCR access token obtained successfully")
        return OCR_ACCESS_TOKEN
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

def get_user_history(user_id):
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
        LIMIT 20
        ''', (user_id,))

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

def save_message(user_id, role, content, images=None):
    """Save message to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        images_json = json.dumps(images) if images else None

        cursor.execute('''
        INSERT INTO caigpt_dialog_history (user_id, role, content, images)
        VALUES (%s, %s, %s, %s)
        ''', (user_id, role, content, images_json))

        conn.commit()

        if user_id not in dialog_history_cache:
            dialog_history_cache[user_id] = []
        msg = {"role": role, "content": content}
        if images:
            msg["images"] = images
        dialog_history_cache[user_id].append(msg)

        if len(dialog_history_cache[user_id]) > 20:
            dialog_history_cache[user_id] = dialog_history_cache[user_id][-20:]

        return True
    except Exception as e:
        logger.error(f"Failed to save message: {str(e)}")
        return False
    finally:
        conn.close()

def build_messages(user_message, history=None):
    """Build message list, ensure system prompt is always first"""
    messages = [{"role": "system", "content": CAIGPT_SYSTEM_PROMPT}]

    if history and isinstance(history, list):
        for msg in history:
            if msg.get("role") != "system":
                messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    return messages

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
            print(f"Image processing failed: {e}")

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
    messages = build_messages(user_message, history)

    try:
        ollama_url = "http://localhost:11434/api/chat"
        payload = {
            "model": "qwen2.5-coder:3b",
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(ollama_url, json=payload, timeout=60)
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
