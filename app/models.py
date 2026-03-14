from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json
import subprocess
import tempfile
import os
from datetime import datetime

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='student', created_at=None, updated_at=None, nickname=None, avatar=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
        self.nickname = nickname if nickname else username
        self.avatar = avatar
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    def save(self):
        from flask import current_app
        from datetime import datetime
        db = current_app.db
        data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if self.nickname:
            data['nickname'] = self.nickname
        if self.avatar:
            data['avatar'] = self.avatar
        
        if self.id:
            db.update('users', self.id, data)
        else:
            # 新用户，添加创建时间
            data['created_at'] = data['updated_at']
            if not self.nickname:
                data['nickname'] = self.username
            self.id = db.insert('users', data)
        
        return self
    
    @staticmethod
    def get_by_id(user_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('users', user_id)
        if data:
            # 处理datetime对象
            created_at = data.get('created_at')
            if created_at:
                try:
                    if hasattr(created_at, 'strftime'):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            updated_at = data.get('updated_at')
            if updated_at:
                try:
                    if hasattr(updated_at, 'strftime'):
                        updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            return User(
                id=data.get('id'),
                username=data.get('username'),
                email=data.get('email'),
                password_hash=data.get('password_hash'),
                role=data.get('role'),
                created_at=created_at,
                updated_at=updated_at,
                nickname=data.get('nickname'),
                avatar=data.get('avatar')
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('users', 'email', email)
        if data:
            user_data = data[0]
            # 处理datetime对象
            created_at = user_data.get('created_at')
            if created_at:
                try:
                    if hasattr(created_at, 'strftime'):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            updated_at = user_data.get('updated_at')
            if updated_at:
                try:
                    if hasattr(updated_at, 'strftime'):
                        updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            return User(
                id=user_data.get('id'),
                username=user_data.get('username'),
                email=user_data.get('email'),
                password_hash=user_data.get('password_hash'),
                role=user_data.get('role'),
                created_at=created_at,
                updated_at=updated_at,
                nickname=user_data.get('nickname'),
                avatar=user_data.get('avatar')
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('users', 'username', username)
        if data:
            user_data = data[0]
            # 处理datetime对象
            created_at = user_data.get('created_at')
            if created_at:
                try:
                    if hasattr(created_at, 'strftime'):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            updated_at = user_data.get('updated_at')
            if updated_at:
                try:
                    if hasattr(updated_at, 'strftime'):
                        updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            return User(
                id=user_data.get('id'),
                username=user_data.get('username'),
                email=user_data.get('email'),
                password_hash=user_data.get('password_hash'),
                role=user_data.get('role'),
                created_at=created_at,
                updated_at=updated_at,
                nickname=user_data.get('nickname'),
                avatar=user_data.get('avatar')
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('users')
        print(f'从数据库读取到 {len(data)} 个用户')
        for i, user_data in enumerate(data):
            print(f'用户 {i+1}: ID={user_data.get("id")}, 用户名={user_data.get("username")}, 邮箱={user_data.get("email")}, 角色={user_data.get("role")}')
        users = []
        for user_data in data:
            # 处理datetime对象
            created_at = user_data.get('created_at')
            if created_at:
                try:
                    if hasattr(created_at, 'strftime'):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            updated_at = user_data.get('updated_at')
            if updated_at:
                try:
                    if hasattr(updated_at, 'strftime'):
                        updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            users.append(User(
                id=user_data.get('id'),
                username=user_data.get('username'),
                email=user_data.get('email'),
                password_hash=user_data.get('password_hash'),
                role=user_data.get('role'),
                created_at=created_at,
                updated_at=updated_at
            ))
        print(f'转换为User对象后: {len(users)} 个用户')
        return users
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class ProblemCategory:
    def __init__(self, id=None, name=None, parent_id=None, description=None):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.description = description
    
    def save(self):
        from flask import current_app
        db = current_app.db
        data = {
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description
        }
        
        if self.id:
            db.update('problem_categories', self.id, data)
        else:
            self.id = db.insert('problem_categories', data)
        
        return self
    
    @staticmethod
    def get_by_id(category_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('problem_categories', category_id)
        if data:
            return ProblemCategory(
                id=data['id'],
                name=data['name'],
                parent_id=data['parent_id'],
                description=data['description']
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('problem_categories')
        categories = []
        for category_data in data:
            categories.append(ProblemCategory(
                id=category_data['id'],
                name=category_data['name'],
                parent_id=category_data['parent_id'],
                description=category_data['description']
            ))
        return categories
    
    @staticmethod
    def get_by_parent_id(parent_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problem_categories', 'parent_id', parent_id)
        categories = []
        for category_data in data:
            categories.append(ProblemCategory(
                id=category_data['id'],
                name=category_data['name'],
                parent_id=category_data['parent_id'],
                description=category_data['description']
            ))
        return categories

class Problem:
    def __init__(self, id=None, title=None, description=None, input_format=None, 
                 output_format=None, sample_input=None, sample_output=None, 
                 difficulty=None, category_id=None, time_limit=1, memory_limit=256,
                 test_cases=None, source=None, source_id=None, source_url=None,
                 is_public=0, tags=None, hint=None):
        self.id = id
        self.title = title
        self.description = description
        self.input_format = input_format
        self.output_format = output_format
        self.sample_input = sample_input
        self.sample_output = sample_output
        self.difficulty = difficulty
        self.category_id = category_id
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.test_cases = test_cases if test_cases else []
        self.source = source
        self.source_id = source_id
        self.source_url = source_url
        self.is_public = is_public
        self.tags = tags
        self.hint = hint
    
    def save(self):
        from flask import current_app
        db = current_app.db
        data = {
            'title': self.title,
            'description': self.description,
            'input_format': self.input_format,
            'output_format': self.output_format,
            'sample_input': self.sample_input,
            'sample_output': self.sample_output,
            'difficulty': self.difficulty,
            'category_id': self.category_id,
            'time_limit': self.time_limit,
            'memory_limit': self.memory_limit,
            'test_cases': json.dumps(self.test_cases),
            'source': self.source,
            'source_id': self.source_id,
            'source_url': self.source_url,
            'is_public': self.is_public,
            'tags': self.tags,
            'hint': self.hint
        }
        
        if self.id:
            db.update('problems', self.id, data)
        else:
            self.id = db.insert('problems', data)
        
        return self
    
    @staticmethod
    def get_by_id(problem_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('problems', problem_id)
        if data:
            return Problem(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                input_format=data['input_format'],
                output_format=data['output_format'],
                sample_input=data['sample_input'],
                sample_output=data['sample_output'],
                difficulty=data['difficulty'],
                category_id=data['category_id'],
                time_limit=data['time_limit'],
                memory_limit=data['memory_limit'],
                test_cases=json.loads(data['test_cases']) if data.get('test_cases') else [],
                source=data.get('source'),
                source_id=data.get('source_id'),
                source_url=data.get('source_url'),
                is_public=data.get('is_public', 0),
                tags=data.get('tags'),
                hint=data.get('hint')
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('problems')
        problems = []
        
        # 预加载所有分类，用于映射 category_id 到 category 名称
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem_data in data:
            problem = Problem(
                id=problem_data['id'],
                title=problem_data['title'],
                description=problem_data['description'],
                input_format=problem_data['input_format'],
                output_format=problem_data['output_format'],
                sample_input=problem_data['sample_input'],
                sample_output=problem_data['sample_output'],
                difficulty=problem_data['difficulty'],
                category_id=problem_data['category_id'],
                time_limit=problem_data['time_limit'],
                memory_limit=problem_data['memory_limit'],
                test_cases=json.loads(problem_data['test_cases']) if problem_data.get('test_cases') else [],
                source=problem_data.get('source'),
                source_id=problem_data.get('source_id'),
                source_url=problem_data.get('source_url'),
                is_public=problem_data.get('is_public', 0),
                tags=problem_data.get('tags'),
                hint=problem_data.get('hint')
            )
            # 添加 category 属性
            problem.category = category_map.get(problem_data['category_id'], '')
            problems.append(problem)
        return problems
    
    @staticmethod
    def get_by_category(category_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problems', 'category_id', category_id)
        problems = []
        
        # 预加载所有分类，用于映射 category_id 到 category 名称
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem_data in data:
            problem = Problem(
                id=problem_data['id'],
                title=problem_data['title'],
                description=problem_data['description'],
                input_format=problem_data['input_format'],
                output_format=problem_data['output_format'],
                sample_input=problem_data['sample_input'],
                sample_output=problem_data['sample_output'],
                difficulty=problem_data['difficulty'],
                category_id=problem_data['category_id'],
                time_limit=problem_data['time_limit'],
                memory_limit=problem_data['memory_limit'],
                test_cases=json.loads(problem_data['test_cases']) if problem_data.get('test_cases') else [],
                source=problem_data.get('source'),
                source_id=problem_data.get('source_id'),
                source_url=problem_data.get('source_url'),
                is_public=problem_data.get('is_public', 0),
                tags=problem_data.get('tags'),
                hint=problem_data.get('hint')
            )
            # 添加 category 属性
            problem.category = category_map.get(problem_data['category_id'], '')
            problems.append(problem)
        return problems
    
    @staticmethod
    def get_by_difficulty(difficulty):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problems', 'difficulty', difficulty)
        problems = []
        
        # 预加载所有分类，用于映射 category_id 到 category 名称
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem_data in data:
            problem = Problem(
                id=problem_data['id'],
                title=problem_data['title'],
                description=problem_data['description'],
                input_format=problem_data['input_format'],
                output_format=problem_data['output_format'],
                sample_input=problem_data['sample_input'],
                sample_output=problem_data['sample_output'],
                difficulty=problem_data['difficulty'],
                category_id=problem_data['category_id'],
                time_limit=problem_data['time_limit'],
                memory_limit=problem_data['memory_limit'],
                test_cases=json.loads(problem_data['test_cases']) if problem_data.get('test_cases') else [],
                source=problem_data.get('source'),
                source_id=problem_data.get('source_id'),
                source_url=problem_data.get('source_url'),
                is_public=problem_data.get('is_public', 0),
                tags=problem_data.get('tags'),
                hint=problem_data.get('hint')
            )
            # 添加 category 属性
            problem.category = category_map.get(problem_data['category_id'], '')
            problems.append(problem)
        return problems
    
    @staticmethod
    def get_by_source(source):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problems', 'source', source)
        problems = []
        
        # 预加载所有分类，用于映射 category_id 到 category 名称
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem_data in data:
            problem = Problem(
                id=problem_data['id'],
                title=problem_data['title'],
                description=problem_data['description'],
                input_format=problem_data['input_format'],
                output_format=problem_data['output_format'],
                sample_input=problem_data['sample_input'],
                sample_output=problem_data['sample_output'],
                difficulty=problem_data['difficulty'],
                category_id=problem_data['category_id'],
                time_limit=problem_data['time_limit'],
                memory_limit=problem_data['memory_limit'],
                test_cases=json.loads(problem_data['test_cases']) if problem_data.get('test_cases') else [],
                source=problem_data.get('source'),
                source_id=problem_data.get('source_id'),
                source_url=problem_data.get('source_url'),
                is_public=problem_data.get('is_public', 0),
                tags=problem_data.get('tags'),
                hint=problem_data.get('hint')
            )
            # 添加 category 属性
            problem.category = category_map.get(problem_data['category_id'], '')
            problems.append(problem)
        return problems
    
    @staticmethod
    def exists(title, source=None, source_id=None):
        """
        检查题目是否已存在
        基于标题、来源和来源ID进行判断
        """
        from flask import current_app
        db = current_app.db
        
        # 首先检查相同标题的题目
        all_problems = db.read_table('problems')
        for problem in all_problems:
            # 如果标题相同
            if problem['title'] == title:
                # 如果有来源和来源ID，检查是否匹配
                if source and source_id:
                    if problem.get('source') == source and problem.get('source_id') == source_id:
                        return True
                else:
                    # 如果没有来源信息，只根据标题判断
                    return True
        return False

class Submission:
    def __init__(self, id=None, user_id=None, problem_id=None, code=None, 
                 status=None, error_message=None, submit_time=None):
        self.id = id
        self.user_id = user_id
        self.problem_id = problem_id
        self.code = code
        self.status = status
        self.error_message = error_message
        self.submit_time = submit_time
    
    def save(self):
        from flask import current_app
        db = current_app.db
        data = {
            'user_id': self.user_id,
            'problem_id': self.problem_id,
            'code': self.code,
            'status': self.status,
            'error_message': self.error_message,
            'submit_time': self.submit_time
        }
        
        if self.id:
            db.update('submissions', self.id, data)
        else:
            self.id = db.insert('submissions', data)
        
        return self
    
    @staticmethod
    def get_by_id(submission_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('submissions', submission_id)
        if data:
            return Submission(
                id=data['id'],
                user_id=data['user_id'],
                problem_id=data['problem_id'],
                code=data['code'],
                status=data['status'],
                error_message=data['error_message'],
                submit_time=data['submit_time']
            )
        return None
    
    @staticmethod
    def get_by_user(user_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('submissions', 'user_id', user_id)
        submissions = []
        for submission_data in data:
            submissions.append(Submission(
                id=submission_data['id'],
                user_id=submission_data['user_id'],
                problem_id=submission_data['problem_id'],
                code=submission_data['code'],
                status=submission_data['status'],
                error_message=submission_data['error_message'],
                submit_time=submission_data['submit_time']
            ))
        return submissions
    
    @staticmethod
    def get_by_problem(problem_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('submissions', 'problem_id', problem_id)
        submissions = []
        for submission_data in data:
            submissions.append(Submission(
                id=submission_data['id'],
                user_id=submission_data['user_id'],
                problem_id=submission_data['problem_id'],
                code=submission_data['code'],
                status=submission_data['status'],
                error_message=submission_data['error_message'],
                submit_time=submission_data['submit_time']
            ))
        return submissions

def evaluate_code(code, test_cases, time_limit=1, memory_limit=256):
    """
    评测C++代码
    :param code: C++代码
    :param test_cases: 测试用例列表 [{'input': '输入', 'output': '输出'}, ...]
    :param time_limit: 时间限制（秒）
    :param memory_limit: 内存限制（MB）
    :return: 评测结果 {'status': 'AC/WA/TLE/MLE/CE', 'message': '详细信息'}
    """
    results = []
    
    for i, test_case in enumerate(test_cases):
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as source_file:
                source_file.write(code)
                source_file_path = source_file.name
            
            executable_path = source_file_path.replace('.cpp', '.exe')
            
            compile_result = subprocess.run(
                ['g++', source_file_path, '-o', executable_path, '-O2'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode != 0:
                os.unlink(source_file_path)
                if os.path.exists(executable_path):
                    os.unlink(executable_path)
                return {
                    'status': 'CE',
                    'message': f'编译错误：{compile_result.stderr}'
                }
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as input_file:
                input_file.write(test_case['input'])
                input_file_path = input_file.name
            
            with open(input_file_path, 'r') as f:
                run_result = subprocess.run(
                    [executable_path],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=time_limit
                )
            
            os.unlink(source_file_path)
            os.unlink(executable_path)
            os.unlink(input_file_path)
            
            expected_output = test_case['output'].strip()
            actual_output = run_result.stdout.strip()
            
            if actual_output == expected_output:
                results.append({'test_case': i + 1, 'status': 'AC'})
            else:
                return {
                    'status': 'WA',
                    'message': f'测试用例 {i + 1} 答案错误\n期望输出：{expected_output}\n实际输出：{actual_output}'
                }
            
        except subprocess.TimeoutExpired:
            os.unlink(source_file_path)
            if os.path.exists(executable_path):
                os.unlink(executable_path)
            return {
                'status': 'TLE',
                'message': f'测试用例 {i + 1} 超时'
            }
        except Exception as e:
            if os.path.exists(source_file_path):
                os.unlink(source_file_path)
            if os.path.exists(executable_path):
                os.unlink(executable_path)
            return {
                'status': 'RE',
                'message': f'运行时错误：{str(e)}'
            }
    
    return {
        'status': 'AC',
        'message': '所有测试用例通过'
    }

class AIConversation:
    def __init__(self, id=None, user_id=None, problem_id=None, question=None, 
                 answer=None, model_name=None, conversation_type=None, 
                 has_code=False, has_image=False, created_at=None):
        self.id = id
        self.user_id = user_id
        self.problem_id = problem_id
        self.question = question
        self.answer = answer
        self.model_name = model_name
        self.conversation_type = conversation_type
        self.has_code = has_code
        self.has_image = has_image
        self.created_at = created_at
    
    def save(self):
        from flask import current_app
        db = current_app.db
        
        data = {
            'user_id': self.user_id,
            'problem_id': self.problem_id,
            'question': self.question,
            'answer': self.answer,
            'model_name': self.model_name,
            'conversation_type': self.conversation_type,
            'has_code': self.has_code,
            'has_image': self.has_image
        }
        
        if self.id:
            data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('ai_conversations', self.id, data)
        else:
            data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['updated_at'] = data['created_at']
            self.id = db.insert('ai_conversations', data)
        
        return self
    
    @staticmethod
    def get_by_id(conversation_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('ai_conversations', conversation_id)
        if data:
            return AIConversation(
                id=data['id'],
                user_id=data['user_id'],
                problem_id=data['problem_id'],
                question=data['question'],
                answer=data['answer'],
                model_name=data['model_name'],
                conversation_type=data['conversation_type'],
                has_code=data['has_code'],
                has_image=data['has_image'],
                created_at=data['created_at']
            )
        return None
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('ai_conversations', 'user_id', user_id)
        conversations = []
        for conv_data in data[:limit]:
            conversations.append(AIConversation(
                id=conv_data['id'],
                user_id=conv_data['user_id'],
                problem_id=conv_data['problem_id'],
                question=conv_data['question'],
                answer=conv_data['answer'],
                model_name=conv_data['model_name'],
                conversation_type=conv_data['conversation_type'],
                has_code=conv_data['has_code'],
                has_image=conv_data['has_image'],
                created_at=conv_data['created_at']
            ))
        return conversations
    
    @staticmethod
    def get_by_problem(user_id, problem_id):
        from flask import current_app
        db = current_app.db
        conversations = db.read_table('ai_conversations')
        result = []
        for conv_data in conversations:
            if conv_data['user_id'] == user_id and conv_data['problem_id'] == problem_id:
                result.append(AIConversation(
                    id=conv_data['id'],
                    user_id=conv_data['user_id'],
                    problem_id=conv_data['problem_id'],
                    question=conv_data['question'],
                    answer=conv_data['answer'],
                    model_name=conv_data['model_name'],
                    conversation_type=conv_data['conversation_type'],
                    has_code=conv_data['has_code'],
                    has_image=conv_data['has_image'],
                    created_at=conv_data['created_at']
                ))
        return result
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('ai_conversations')
        conversations = []
        for conv_data in data:
            conversations.append(AIConversation(
                id=conv_data['id'],
                user_id=conv_data['user_id'],
                problem_id=conv_data['problem_id'],
                question=conv_data['question'],
                answer=conv_data['answer'],
                model_name=conv_data['model_name'],
                conversation_type=conv_data['conversation_type'],
                has_code=conv_data['has_code'],
                has_image=conv_data['has_image'],
                created_at=conv_data['created_at']
            ))
        return conversations
    
    def delete(self):
        from flask import current_app
        db = current_app.db
        if self.id:
            db.delete('ai_conversations', self.id)

class TeacherAssignment:
    def __init__(self, id=None, teacher_id=None, problem_id=None, title=None, 
                 description=None, start_time=None, end_time=None, created_at=None, updated_at=None):
        self.id = id
        self.teacher_id = teacher_id
        self.problem_id = problem_id
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.created_at = created_at
        self.updated_at = updated_at
    
    def save(self):
        from flask import current_app
        db = current_app.db
        
        data = {
            'teacher_id': self.teacher_id,
            'problem_id': self.problem_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time
        }
        
        if self.id:
            data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('teacher_assignments', self.id, data)
        else:
            data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['updated_at'] = data['created_at']
            self.id = db.insert('teacher_assignments', data)
        
        return self
    
    @staticmethod
    def get_by_id(assignment_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('teacher_assignments', assignment_id)
        if data:
            return TeacherAssignment(
                id=data['id'],
                teacher_id=data['teacher_id'],
                problem_id=data['problem_id'],
                title=data['title'],
                description=data['description'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                created_at=data['created_at'],
                updated_at=data['updated_at']
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('teacher_assignments')
        assignments = []
        for assignment_data in data:
            assignments.append(TeacherAssignment(
                id=assignment_data['id'],
                teacher_id=assignment_data['teacher_id'],
                problem_id=assignment_data['problem_id'],
                title=assignment_data['title'],
                description=assignment_data['description'],
                start_time=assignment_data['start_time'],
                end_time=assignment_data['end_time'],
                created_at=assignment_data['created_at'],
                updated_at=assignment_data['updated_at']
            ))
        return assignments
    
    @staticmethod
    def get_by_teacher(teacher_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('teacher_assignments', 'teacher_id', teacher_id)
        assignments = []
        for assignment_data in data:
            assignments.append(TeacherAssignment(
                id=assignment_data['id'],
                teacher_id=assignment_data['teacher_id'],
                problem_id=assignment_data['problem_id'],
                title=assignment_data['title'],
                description=assignment_data['description'],
                start_time=assignment_data['start_time'],
                end_time=assignment_data['end_time'],
                created_at=assignment_data['created_at'],
                updated_at=assignment_data['updated_at']
            ))
        return assignments
    
    def delete(self):
        from flask import current_app
        db = current_app.db
        if self.id:
            db.delete('teacher_assignments', self.id)

class TeacherSelectedProblem:
    def __init__(self, id=None, teacher_id=None, problem_id=None, course_id=None,
                 selected_at=None, visible_start=None, visible_end=None, notes=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.teacher_id = teacher_id
        self.problem_id = problem_id
        self.course_id = course_id
        self.selected_at = selected_at
        self.visible_start = visible_start
        self.visible_end = visible_end
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
    
    def save(self):
        from flask import current_app
        db = current_app.db
        
        data = {
            'teacher_id': self.teacher_id,
            'problem_id': self.problem_id,
            'course_id': self.course_id,
            'visible_start': self.visible_start,
            'visible_end': self.visible_end,
            'notes': self.notes
        }
        
        if self.id:
            data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('teacher_selected_problems', self.id, data)
        else:
            data['selected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['created_at'] = data['selected_at']
            data['updated_at'] = data['selected_at']
            self.id = db.insert('teacher_selected_problems', data)
        
        return self
    
    @staticmethod
    def get_by_id(selected_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('teacher_selected_problems', selected_id)
        if data:
            return TeacherSelectedProblem(
                id=data['id'],
                teacher_id=data['teacher_id'],
                problem_id=data['problem_id'],
                course_id=data.get('course_id'),
                selected_at=data.get('selected_at'),
                visible_start=data.get('visible_start'),
                visible_end=data.get('visible_end'),
                notes=data.get('notes'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('teacher_selected_problems')
        selected = []
        for item in data:
            selected.append(TeacherSelectedProblem(
                id=item['id'],
                teacher_id=item['teacher_id'],
                problem_id=item['problem_id'],
                course_id=item.get('course_id'),
                selected_at=item.get('selected_at'),
                visible_start=item.get('visible_start'),
                visible_end=item.get('visible_end'),
                notes=item.get('notes'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            ))
        return selected
    
    @staticmethod
    def get_by_teacher(teacher_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('teacher_selected_problems', 'teacher_id', teacher_id)
        selected = []
        for item in data:
            selected.append(TeacherSelectedProblem(
                id=item['id'],
                teacher_id=item['teacher_id'],
                problem_id=item['problem_id'],
                course_id=item.get('course_id'),
                selected_at=item.get('selected_at'),
                visible_start=item.get('visible_start'),
                visible_end=item.get('visible_end'),
                notes=item.get('notes'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            ))
        return selected
    
    @staticmethod
    def get_by_teacher_and_problem(teacher_id, problem_id):
        from flask import current_app
        db = current_app.db
        all_data = db.read_table('teacher_selected_problems')
        for item in all_data:
            if item['teacher_id'] == teacher_id and item['problem_id'] == problem_id:
                return TeacherSelectedProblem(
                    id=item['id'],
                    teacher_id=item['teacher_id'],
                    problem_id=item['problem_id'],
                    course_id=item.get('course_id'),
                    selected_at=item.get('selected_at'),
                    visible_start=item.get('visible_start'),
                    visible_end=item.get('visible_end'),
                    notes=item.get('notes'),
                    created_at=item.get('created_at'),
                    updated_at=item.get('updated_at')
                )
        return None
    
    @staticmethod
    def get_visible_problems_for_student(student_id):
        from flask import current_app
        db = current_app.db
        all_data = db.read_table('teacher_selected_problems')
        visible_problems = []
        now = datetime.now()
        
        for item in all_data:
            visible_start = item.get('visible_start')
            visible_end = item.get('visible_end')
            
            is_visible = True
            if visible_start:
                try:
                    start_time = datetime.strptime(visible_start, '%Y-%m-%d %H:%M:%S')
                    if now < start_time:
                        is_visible = False
                except:
                    pass
            
            if visible_end:
                try:
                    end_time = datetime.strptime(visible_end, '%Y-%m-%d %H:%M:%S')
                    if now > end_time:
                        is_visible = False
                except:
                    pass
            
            if is_visible:
                visible_problems.append(item['problem_id'])
        
        return list(set(visible_problems))
    
    def delete(self):
        from flask import current_app
        db = current_app.db
        if self.id:
            db.delete('teacher_selected_problems', self.id)

class ProblemImportLog:
    def __init__(self, id=None, admin_id=None, source=None, count=None,
                 status=None, error_message=None, created_at=None):
        self.id = id
        self.admin_id = admin_id
        self.source = source
        self.count = count
        self.status = status
        self.error_message = error_message
        self.created_at = created_at
    
    def save(self):
        from flask import current_app
        db = current_app.db
        
        data = {
            'admin_id': self.admin_id,
            'source': self.source,
            'count': self.count,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.id = db.insert('problem_import_logs', data)
        return self
    
    @staticmethod
    def get_by_id(log_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('problem_import_logs', log_id)
        if data:
            return ProblemImportLog(
                id=data['id'],
                admin_id=data['admin_id'],
                source=data.get('source'),
                count=data.get('count'),
                status=data.get('status'),
                error_message=data.get('error_message'),
                created_at=data.get('created_at')
            )
        return None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('problem_import_logs')
        logs = []
        for log_data in data:
            logs.append(ProblemImportLog(
                id=log_data['id'],
                admin_id=log_data['admin_id'],
                source=log_data.get('source'),
                count=log_data.get('count'),
                status=log_data.get('status'),
                error_message=log_data.get('error_message'),
                created_at=log_data.get('created_at')
            ))
        return logs
    
    @staticmethod
    def get_by_admin(admin_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problem_import_logs', 'admin_id', admin_id)
        logs = []
        for log_data in data:
            logs.append(ProblemImportLog(
                id=log_data['id'],
                admin_id=log_data['admin_id'],
                source=log_data.get('source'),
                count=log_data.get('count'),
                status=log_data.get('status'),
                error_message=log_data.get('error_message'),
                created_at=log_data.get('created_at')
            ))
        return logs