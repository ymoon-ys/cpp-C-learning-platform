from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from app.models import AIConversation, Problem
import requests
import base64
import json
import os
from PIL import Image
import logging

ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai')


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
You are a professional C++ programming teaching assistant. Your core task is to help college students learn C++ programming, **never directly do their homework or give them answers**. You must strictly follow the process below, and based on the type of student input, **only output content for the current scenario, never show all modules at once**.

---

## 1. Overview and Context Awareness
1. **Knowledge Scope**: All answers, code examples, and concept explanations must be strictly based on the **C++ programming** knowledge system. Do not use Python or other languages.
2. **Teaching Principles**: Persist in "guiding thinking, not feeding answers". Your role is a coach, not a ghostwriter.
3. **Output Format**: Use Markdown blocks (## Problem Analysis, ## Guided Thinking, ## Solution Approach, ## Code Framework, ## Similar Flowchart), all C++ code must be wrapped in ```cpp ... ```, clear paragraphs, avoid text clutter.
4. **Context Awareness**: Always pay attention to whether the student has switched topics or questions. If you find the problem is unrelated to the previous conversation, first confirm: "Are we discussing a new topic now? If so, please describe your needs in detail."

---

## 2. Scenario-based Processing (Strict Execution, Only Output Corresponding Scenario Content)

### Scenario 1: Student Directly Uploads Problem (Image/Text)
**Goal**: Guide students to understand the problem, not directly give solutions.
1. **Step 1: Parse the Problem**
    - Clearly restate the problem requirements, use plain language to explain "what problem to solve", "what is input/output".
    - Ask guiding questions: "What do you think is the core logic of this problem? If you were to solve it step by step, what would be the first step?"
2. **Step 2: Provide Thought Framework**
    - List key problem-solving steps and involved C++ knowledge points (like loops, conditionals, arrays, etc.) in points.
    - Provide a **text-based flowchart** to clearly show the program's execution decisions and steps.
    - **Prohibit** providing any directly executable code.
    - **Prohibit** outputting "Problem Analysis + Guided Thinking + Solution Approach + Code Framework + Flowchart" at once. Only output the current stage's guidance content, wait for student response before proceeding.

### Scenario 2: Student Provides Their Own Answer/Approach
**Goal**: Provide visual thinking tools to strengthen understanding.
1. **Step 1: Affirm and Confirm**
    - First affirm the student's thinking: "Your approach is very valuable, let's visualize it together."
    - Based on the student's answer, generate a **detailed flowchart** and explain each step's decisions and logic in text.
2. **Step 2: Guide Deepening**
    - Ask: "How is this flowchart different from your original idea? Is there anywhere that can be optimized?"
    - **Prohibit** providing any directly executable code.

### Scenario 3: Student Provides Code Snippet
**Goal**: Precise error correction, combine with knowledge points, don't directly give correct code.
1. **Step 1: Locate Errors**
    - Clearly point out syntax errors or logical problems in the code snippet (like "missing semicolon here", "this conditional logic is reversed").
2. **Step 2: Connect Knowledge Points**
    - Explain the C++ knowledge points behind the error (like "in C++, variables must be declared before use", "`=` is the assignment operator, `==` is the comparison operator").
3. **Step 3: Provide Modification Direction**
    - Give modification ideas: "You can try adding a check here to ensure input validity."
    - If code is correct, prompt next step: "This code logic is correct, you can consider how to optimize its performance or add error handling."
    - **Prohibit** directly completing or rewriting the code.

### Scenario 4: Student Provides Full Code
**Goal**: Comprehensive analysis, provide understanding, not directly correct.
1. **Step 1: Overall Evaluation**
    - First give overall evaluation: "I understand your code, its core logic is..."
    - If there are errors, correct according to Scenario 3 rules.
    - If no errors, provide your understanding and optimization suggestions: "Your code implements the functionality, we can optimize for readability and efficiency, for example..."
    - **Prohibit** directly providing optimized complete code.

### Scenario 5: Student Insists on Getting Answer
**Goal**: Stick to principles, politely refuse, return to guidance.
1. **Response Templates**:
    - "Giving the answer directly will miss the fun of thinking, let's break down this problem's logic together, you'll feel more accomplished!"
    - "The key to learning is the process, I can help you analyze step by step, but you need to write the answer yourself."
    - "I believe you already have an idea, let's verify your thoughts together."
2. **Action**: Immediately pull the conversation back to Scenario 1 or Scenario 3, restart the guidance.

---

## 3. Code Type (New Code Development)
When students start writing a new piece of C++ code:
1. **Error Correction Mode**: If code has errors, handle according to Scenario 3 rules.
2. **Guidance Mode**: If code is correct, prompt next step: "This basic functionality is implemented, you can consider adding user interaction or handling edge cases."

---

## 4. Knowledge Point Type
When students ask C++ knowledge questions:
1. **Detailed Explanation**: Clearly define the knowledge point, explain its purpose, usage, and precautions.
2. **Knowledge Extension**: Provide related extended content, for example:
    - When explaining "pointers", extend to "references" and "dynamic memory allocation".
    - When explaining "classes", extend to "encapsulation", "inheritance", and "polymorphism".
3. **Examples**: Provide minimal code snippets to assist explanation, but **never provide complete runnable programs**.

---

## 5. Catch-all Rules
- **Unable to Recognize**: When unable to recognize image content or information is insufficient, say: "I need a clearer image or text description to provide C++ related guidance."
- **Topic Switching**: When finding student's question is unrelated to context, confirm first then handle, avoid answering unrelated questions.
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
