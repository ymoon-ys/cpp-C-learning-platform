from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, TypeVar, Type
from flask import current_app

T = TypeVar('T', bound='BaseModel')


class BaseModel:
    """基础模型类，封装通用的数据库操作"""

    table_name: str = ""

    def __init__(self, id: Optional[int] = None):
        self.id = id

    def save(self: T) -> T:
        """保存或更新记录"""
        db = current_app.db
        data = self._to_dict()

        if self.id:
            db.update(self.table_name, self.id, data)
        else:
            self.id = db.insert(self.table_name, data)
        return self

    def delete(self) -> bool:
        """删除记录"""
        if not self.id:
            return False
        db = current_app.db
        return db.delete(self.table_name, self.id)

    @classmethod
    def get_by_id(cls: Type[T], record_id: int) -> Optional[T]:
        """根据ID获取记录"""
        db = current_app.db
        data = db.find_by_id(cls.table_name, record_id)
        if data:
            return cls._from_dict(data)
        return None

    @classmethod
    def get_all(cls: Type[T]) -> List[T]:
        """获取所有记录"""
        db = current_app.db
        data = db.read_table(cls.table_name)
        return [cls._from_dict(item) for item in data]

    @classmethod
    def get_by_field(cls: Type[T], field_name: str, field_value: Any) -> List[T]:
        """根据字段获取记录"""
        db = current_app.db
        data = db.find_by_field(cls.table_name, field_name, field_value)
        return [cls._from_dict(item) for item in data]

    def _to_dict(self) -> Dict[str, Any]:
        """转换为字典，子类需要重写"""
        return {'id': self.id} if self.id else {}

    @classmethod
    def _from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """从字典创建实例，子类需要重写"""
        return cls(id=data.get('id'))

    @staticmethod
    def _convert_datetime(value: Any) -> Optional[str]:
        """转换datetime对象为字符串"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


class User(UserMixin, BaseModel):
    table_name = 'users'
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='student', created_at=None, updated_at=None, nickname=None, avatar=None):
        super().__init__(id)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
        self.nickname = nickname if nickname else username
        self.avatar = avatar
    
    def _to_dict(self):
        data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
        }
        if self.id:
            data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.nickname:
            data['nickname'] = self.nickname
        if self.avatar:
            data['avatar'] = self.avatar
        return data
    
    @classmethod
    def _from_dict(cls, data):
        created_at = cls._convert_datetime(data.get('created_at'))
        updated_at = cls._convert_datetime(data.get('updated_at'))
        return cls(
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
    
    def save(self):
        from flask import current_app
        db = current_app.db
        data = self._to_dict()
        
        if self.id:
            db.update('users', self.id, data)
        else:
            data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['updated_at'] = data['created_at']
            if not self.nickname:
                data['nickname'] = self.username
            self.id = db.insert('users', data)
        
        return self
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_by_id(user_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_id('users', user_id)
        if data:
            return User._from_dict(data)
        return None
    
    @staticmethod
    def get_by_email(email):
        from flask import current_app
        db = current_app.db
        users = db.find_by_field('users', 'email', email)
        return User._from_dict(users[0]) if users else None
    
    @staticmethod
    def get_by_username(username):
        from flask import current_app
        db = current_app.db
        users = db.find_by_field('users', 'username', username)
        return User._from_dict(users[0]) if users else None
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('users')
        return [User._from_dict(item) for item in data]
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class ProblemCategory(BaseModel):
    table_name = 'problem_categories'
    
    def __init__(self, id=None, name=None, parent_id=None, description=None):
        super().__init__(id)
        self.name = name
        self.parent_id = parent_id
        self.description = description
    
    def _to_dict(self):
        return {
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description
        }
    
    @classmethod
    def _from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            parent_id=data.get('parent_id'),
            description=data.get('description')
        )
    
    @staticmethod
    def get_by_parent_id(parent_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problem_categories', 'parent_id', parent_id)
        return [ProblemCategory._from_dict(item) for item in data]

class Problem(BaseModel):
    table_name = 'problems'
    
    def __init__(self, id=None, title=None, description=None, input_format=None, 
                 output_format=None, sample_input=None, sample_output=None, 
                 difficulty=None, category_id=None, time_limit=1, memory_limit=256,
                 test_cases=None, source=None, source_id=None, source_url=None,
                 is_public=0, tags=None, hint=None):
        super().__init__(id)
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
        self.category = None
    
    def _to_dict(self):
        return {
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
    
    @classmethod
    def _from_dict(cls, data):
        test_cases = []
        if data.get('test_cases'):
            try:
                test_cases = json.loads(data['test_cases'])
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                import logging
                logging.warning(f"Failed to parse test_cases: {e}")
                test_cases = []
        
        problem = cls(
            id=data.get('id'),
            title=data.get('title'),
            description=data.get('description'),
            input_format=data.get('input_format'),
            output_format=data.get('output_format'),
            sample_input=data.get('sample_input'),
            sample_output=data.get('sample_output'),
            difficulty=data.get('difficulty'),
            category_id=data.get('category_id'),
            time_limit=data.get('time_limit', 1),
            memory_limit=data.get('memory_limit', 256),
            test_cases=test_cases,
            source=data.get('source'),
            source_id=data.get('source_id'),
            source_url=data.get('source_url'),
            is_public=data.get('is_public', 0),
            tags=data.get('tags'),
            hint=data.get('hint')
        )
        
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        problem.category = category_map.get(data.get('category_id'), '')
        return problem
    
    @staticmethod
    def _get_with_category(field_name, field_value):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('problems', field_name, field_value)
        problems = [Problem._from_dict(item) for item in data]
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem in problems:
            problem.category = category_map.get(problem.category_id, '')
        return problems
    
    @staticmethod
    def get_all():
        from flask import current_app
        db = current_app.db
        data = db.read_table('problems')
        problems = [Problem._from_dict(item) for item in data]
        categories = ProblemCategory.get_all()
        category_map = {cat.id: cat.name for cat in categories}
        
        for problem in problems:
            problem.category = category_map.get(problem.category_id, '')
        return problems
    
    @staticmethod
    def get_by_category(category_id):
        return Problem._get_with_category('category_id', category_id)
    
    @staticmethod
    def get_by_difficulty(difficulty):
        return Problem._get_with_category('difficulty', difficulty)
    
    @staticmethod
    def get_by_source(source):
        return Problem._get_with_category('source', source)
    
    @staticmethod
    def exists(title, source=None, source_id=None):
        from flask import current_app
        db = current_app.db
        all_problems = db.read_table('problems')
        for problem in all_problems:
            if problem['title'] == title:
                if source and source_id:
                    if problem.get('source') == source and problem.get('source_id') == source_id:
                        return True
                else:
                    return True
        return False

class Submission:
    def __init__(self, id=None, user_id=None, problem_id=None, code=None, 
                 status=None, error_message=None, submit_time=None, ai_analysis=None):
        self.id = id
        self.user_id = user_id
        self.problem_id = problem_id
        self.code = code
        self.status = status
        self.error_message = error_message
        self.submit_time = submit_time
        self.ai_analysis = ai_analysis
    
    def save(self):
        from flask import current_app
        db = current_app.db
        data = {
            'user_id': self.user_id,
            'problem_id': self.problem_id,
            'code': self.code,
            'status': self.status,
            'error_message': self.error_message,
            'ai_analysis': self.ai_analysis,
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
                submit_time=data['submit_time'],
                ai_analysis=data.get('ai_analysis')
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
                submit_time=submission_data['submit_time'],
                ai_analysis=submission_data.get('ai_analysis')
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
                submit_time=submission_data['submit_time'],
                ai_analysis=submission_data.get('ai_analysis')
            ))
        return submissions


def _cleanup_temp_files(*files):
    """清理临时文件"""
    for file_path in files:
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass


def _compile_code(source_file_path: str) -> tuple:
    executable_path = os.path.splitext(source_file_path)[0]
    if os.name == 'nt':
        executable_path += '.exe'

    compile_cmd = ['g++', source_file_path, '-o', executable_path, '-O2', '-std=c++17']
    if os.name == 'nt':
        compile_cmd.append('-mconsole')

    compile_result = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True,
        timeout=10
    )

    if compile_result.returncode != 0:
        _cleanup_temp_files(source_file_path)
        return (False, None, compile_result.stderr)

    return (True, executable_path, None)


def _run_test_case(executable_path: str, input_data: str, time_limit: int) -> tuple:
    """
    运行单个测试用例
    :return: (成功标志, 输出内容, 超时标志, 错误信息)
    """
    input_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as input_file:
            input_file.write(input_data)
            input_file_path = input_file.name
        
        with open(input_file_path, 'r') as f:
            run_result = subprocess.run(
                [executable_path],
                stdin=f,
                capture_output=True,
                text=True,
                timeout=time_limit
            )
        
        return (True, run_result.stdout.strip(), False, None)
        
    except subprocess.TimeoutExpired:
        return (False, '', True, 'TLE')
    except Exception as e:
        return (False, '', False, str(e))
    finally:
        if input_file_path:
            _cleanup_temp_files(input_file_path)


def evaluate_code(code: str, test_cases: list, time_limit: int = 1, memory_limit: int = 256) -> dict:
    source_file_path = None
    executable_path = None

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as source_file:
            source_file.write(code)
            source_file_path = source_file.name

        success, executable_path, error = _compile_code(source_file_path)

        if not success:
            return {
                'status': 'CE',
                'message': f'编译错误：{error}'
            }

        if not test_cases:
            return {
                'status': 'CE',
                'message': '该题目没有测试用例，无法评测'
            }

        for i, test_case in enumerate(test_cases):
            success, output, is_timeout, error = _run_test_case(
                executable_path,
                test_case['input'],
                time_limit
            )

            if is_timeout:
                return {
                    'status': 'TLE',
                    'message': f'测试用例 {i + 1} 超时'
                }

            if not success:
                return {
                    'status': 'RE',
                    'message': f'运行时错误：{error}'
                }

            expected_output = test_case['output'].strip()

            if output != expected_output:
                return {
                    'status': 'WA',
                    'message': f'测试用例 {i + 1} 答案错误\n期望输出：{expected_output}\n实际输出：{output}'
                }

        return {
            'status': 'AC',
            'message': '所有测试用例通过'
        }

    except Exception as e:
        return {
            'status': 'RE',
            'message': f'运行时错误：{str(e)}'
        }
    finally:
        _cleanup_temp_files(source_file_path, executable_path)


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
                except (ValueError, TypeError) as e:
                    import logging
                    logging.warning(f"Failed to parse visible_start: {e}")
            
            if visible_end:
                try:
                    end_time = datetime.strptime(visible_end, '%Y-%m-%d %H:%M:%S')
                    if now > end_time:
                        is_visible = False
                except (ValueError, TypeError) as e:
                    import logging
                    logging.warning(f"Failed to parse visible_end: {e}")
            
            if is_visible:
                visible_problems.append(item['problem_id'])
        
        return list(set(visible_problems))
    
    def delete(self):
        from flask import current_app
        db = current_app.db
        if self.id:
            db.delete('teacher_selected_problems', self.id)


class LearningProgress(BaseModel):
    table_name = 'learning_progress'
    
    def __init__(self, id=None, user_id=None, course_id=None, chapter_id=None,
                 lesson_id=None, progress=0, completed=False, updated_at=None):
        super().__init__(id)
        self.user_id = user_id
        self.course_id = course_id
        self.chapter_id = chapter_id
        self.lesson_id = lesson_id
        self.progress = progress
        self.completed = completed
        self.updated_at = updated_at
    
    def _to_dict(self):
        return {
            'user_id': self.user_id,
            'course_id': self.course_id,
            'chapter_id': self.chapter_id,
            'lesson_id': self.lesson_id,
            'progress': self.progress,
            'completed': 1 if self.completed else 0,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if self.id else None
        }
    
    @classmethod
    def _from_dict(cls, data):
        updated_at = cls._convert_datetime(data.get('updated_at'))
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            course_id=data.get('course_id'),
            chapter_id=data.get('chapter_id'),
            lesson_id=data.get('lesson_id'),
            progress=data.get('progress', 0),
            completed=bool(data.get('completed', 0)),
            updated_at=updated_at
        )
    
    @staticmethod
    def get_by_user(user_id):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('learning_progress', 'user_id', user_id)
        return [LearningProgress._from_dict(item) for item in data]
    
    @staticmethod
    def get_by_user_and_course(user_id, course_id):
        from flask import current_app
        db = current_app.db
        data = db.find_all('learning_progress', {
            'user_id': user_id,
            'course_id': course_id
        })
        return [LearningProgress._from_dict(item) for item in data]
    
    @staticmethod
    def get_by_user_and_lesson(user_id, lesson_id):
        from flask import current_app
        db = current_app.db
        data = db.find_all('learning_progress', {
            'user_id': user_id,
            'lesson_id': lesson_id
        })
        if data:
            return LearningProgress._from_dict(data[0])
        return None
    
    @staticmethod
    def update_progress(user_id, course_id, chapter_id, lesson_id, progress, completed=False):
        existing = LearningProgress.get_by_user_and_lesson(user_id, lesson_id)
        if existing:
            existing.progress = progress
            existing.completed = completed
            return existing.save()
        else:
            new_progress = LearningProgress(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                lesson_id=lesson_id,
                progress=progress,
                completed=completed
            )
            return new_progress.save()


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