from datetime import datetime
from flask import flash, redirect, url_for
from flask_login import current_user

DIFFICULTY_EASY = 'easy'
DIFFICULTY_MEDIUM = 'medium'
DIFFICULTY_HARD = 'hard'

DIFFICULTY_LABELS = {
    DIFFICULTY_EASY: '简单',
    DIFFICULTY_MEDIUM: '中等',
    DIFFICULTY_HARD: '困难',
}

DIFFICULTY_COLORS = {
    DIFFICULTY_EASY: '#28a745',
    DIFFICULTY_MEDIUM: '#ffc107',
    DIFFICULTY_HARD: '#dc3545',
}

DIFFICULTY_ICONS = {
    DIFFICULTY_EASY: '🟢',
    DIFFICULTY_MEDIUM: '🟡',
    DIFFICULTY_HARD: '🔴',
}

DIFFICULTY_MAPPING = {
    '洛谷': {
        '入门': DIFFICULTY_EASY,
        '普及-': DIFFICULTY_EASY, 
        '普及/提高-': DIFFICULTY_EASY,
        '普及': DIFFICULTY_MEDIUM,
        '提高-': DIFFICULTY_MEDIUM,
        '普及+/提高': DIFFICULTY_MEDIUM,
        '提高': DIFFICULTY_HARD,
        '提高+/省选-': DIFFICULTY_HARD,
        '省选/NOI-': DIFFICULTY_HARD,
        '省选': DIFFICULTY_HARD,
        'NOI/NOI+/CTSC': DIFFICULTY_HARD,
    },
    'OpenJudge': {
        '1': DIFFICULTY_EASY, '2': DIFFICULTY_EASY, '3': DIFFICULTY_EASY, '4': DIFFICULTY_EASY,
        '5': DIFFICULTY_MEDIUM, '6': DIFFICULTY_MEDIUM,
        '7': DIFFICULTY_HARD, '8': DIFFICULTY_HARD, '9': DIFFICULTY_HARD, '10': DIFFICULTY_HARD,
    },
    '码学堂': {
        '简单': DIFFICULTY_EASY,
        '中等': DIFFICULTY_MEDIUM,
        '困难': DIFFICULTY_HARD,
    },
}

def convert_difficulty(source, original_difficulty):
    """
    将来源平台的原始难度转换为系统标准难度
    """
    if not source or not original_difficulty:
        return original_difficulty
    
    if original_difficulty in [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]:
        return original_difficulty
    
    source_mapping = DIFFICULTY_MAPPING.get(source, {})
    return source_mapping.get(original_difficulty, original_difficulty)

def get_difficulty_label(difficulty):
    """
    获取难度的中文标签
    """
    return DIFFICULTY_LABELS.get(difficulty, difficulty or '未设置')

def get_difficulty_color(difficulty):
    """
    获取难度的颜色代码
    """
    return DIFFICULTY_COLORS.get(difficulty, '#6c757d')

def get_difficulty_icon(difficulty):
    """
    获取难度的图标
    """
    return DIFFICULTY_ICONS.get(difficulty, '⚪')

def get_difficulty_badge(difficulty):
    """
    获取难度的徽章HTML
    """
    label = get_difficulty_label(difficulty)
    color = get_difficulty_color(difficulty)
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{label}</span>'

def get_difficulty_stats(problems):
    """
    获取题目难度分布统计
    """
    stats = {
        DIFFICULTY_EASY: 0,
        DIFFICULTY_MEDIUM: 0,
        DIFFICULTY_HARD: 0,
        'unknown': 0
    }
    
    for problem in problems:
        difficulty = getattr(problem, 'difficulty', None) or problem.get('difficulty') if isinstance(problem, dict) else None
        if difficulty in stats:
            stats[difficulty] += 1
        else:
            stats['unknown'] += 1
    
    return stats

def get_greeting():
    """
    根据当前时间生成问候语
    """
    hour = datetime.now().hour
    if hour < 12:
        return "早上好"
    elif hour < 18:
        return "下午好"
    else:
        return "晚上好"

def get_week_day_chinese():
    """
    获取当前星期几的中文表示
    """
    week_day = datetime.now().strftime('%A')
    week_day_map = {
        'Monday': '周一',
        'Tuesday': '周二',
        'Wednesday': '周三',
        'Thursday': '周四',
        'Friday': '周五',
        'Saturday': '周六',
        'Sunday': '周日'
    }
    return week_day_map.get(week_day, week_day)

def get_learning_days(user):
    """
    计算用户学习天数（从注册到现在的总天数）
    """
    if hasattr(user, 'created_at') and user.created_at:
        try:
            created_date = datetime.strptime(user.created_at, '%Y-%m-%d %H:%M:%S')
            return (datetime.now() - created_date).days
        except (ValueError, TypeError):
            return 15
    else:
        return 15

def get_consecutive_learning_days(user):
    """
    计算用户连续学习天数（基于实际学习记录）
    逻辑：从今天开始往前查找，计算连续有学习记录的天数
    """
    from flask import current_app
    
    try:
        db = current_app.db
        
        learning_dates = set()
        
        progress_records = db.find_field('learning_progress', 'user_id', user.id)
        if progress_records:
            for record in progress_records:
                updated_at = record.get('updated_at')
                if updated_at:
                    try:
                        date_str = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                        learning_dates.add(date_str)
                    except (ValueError, TypeError):
                        pass
        
        submissions = db.find_field('submissions', 'user_id', user.id)
        if submissions:
            for submission in submissions:
                submit_time = submission.get('submit_time')
                if submit_time:
                    try:
                        date_str = datetime.strptime(submit_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                        learning_dates.add(date_str)
                    except (ValueError, TypeError):
                        pass
        
        if not learning_dates:
            return 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        consecutive_days = 0
        check_date = datetime.now()
        
        max_check_days = 365
        for _ in range(max_check_days):
            date_str = check_date.strftime('%Y-%m-%d')
            
            if date_str in learning_dates:
                consecutive_days += 1
                check_date = check_date.replace(day=check_date.day - 1)
            elif date_str == today:
                check_date = check_date.replace(day=check_date.day - 1)
            else:
                break
        
        return consecutive_days
        
    except Exception as e:
        print(f"计算连续学习天数时出错: {e}")
        return 0

def check_role_and_redirect(required_role):
    """
    检查用户角色并重定向
    """
    if current_user.role != required_role:
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    return None

def check_permission_and_redirect(resource_owner_id):
    """
    检查用户权限并重定向
    """
    if int(resource_owner_id) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    return None

def get_user_context(user):
    """
    获取用户上下文信息
    """
    return {
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'learning_days': get_learning_days(user),
        'consecutive_days': get_consecutive_learning_days(user),
        'now': datetime.now(),
        'today_date': datetime.now().strftime('%Y-%m-%d')
    }

def validate_file_upload(file, allowed_extensions=None):
    """
    验证文件上传
    """
    from werkzeug.utils import secure_filename
    
    if not file or not file.filename:
        return False, '请选择文件'
    
    filename = secure_filename(file.filename)
    if not filename:
        return False, '文件名包含非法字符'
    
    if allowed_extensions:
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_ext not in allowed_extensions:
            return False, f'不支持的文件类型，支持的类型：{", ".join(allowed_extensions)}'
    
    return True, None

def save_uploaded_file(file, upload_folder, prefix='', allowed_extensions=None):
    """
    保存上传的文件
    """
    from flask import current_app
    from werkzeug.utils import secure_filename
    import os
    
    is_valid, error = validate_file_upload(file, allowed_extensions)
    if not is_valid:
        raise ValueError(error)
    
    filename = secure_filename(file.filename)
    filename = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    return filename

def get_pagination_info(page, per_page, total_items):
    """
    获取分页信息
    """
    total_pages = (total_items + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    return {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'start_index': start_index,
        'end_index': end_index,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

import json
import csv
import io

def parse_json_import(file_content):
    """
    解析JSON格式的题目导入文件
    """
    try:
        data = json.loads(file_content)
        problems = data.get('problems', [])
        return True, problems, None
    except json.JSONDecodeError as e:
        return False, [], f'JSON解析错误：{str(e)}'
    except Exception as e:
        return False, [], f'解析错误：{str(e)}'

def parse_csv_import(file_content):
    """
    解析CSV格式的题目导入文件
    """
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        problems = []
        for row in reader:
            problem = {
                'title': row.get('title', ''),
                'description': row.get('description', ''),
                'input_format': row.get('input_format', ''),
                'output_format': row.get('output_format', ''),
                'sample_input': row.get('sample_input', ''),
                'sample_output': row.get('sample_output', ''),
                'difficulty': row.get('difficulty', 'medium'),
                'category': row.get('category', ''),
                'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                'time_limit': int(row.get('time_limit', 1)),
                'memory_limit': int(row.get('memory_limit', 256)),
                'source': row.get('source', ''),
                'source_id': row.get('source_id', ''),
                'source_url': row.get('source_url', ''),
                'hint': row.get('hint', '')
            }
            problems.append(problem)
        return True, problems, None
    except Exception as e:
        return False, [], f'CSV解析错误：{str(e)}'

def import_problems(problems_data, admin_id, source=None):
    """
    导入题目到数据库
    """
    from app.models import Problem, ProblemCategory, ProblemImportLog
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for problem_data in problems_data:
        try:
            title = problem_data.get('title', '')
            problem_source = problem_data.get('source', source)
            source_id = problem_data.get('source_id')
            
            # 检查题目是否已存在
            if Problem.exists(title, problem_source, source_id):
                failed_count += 1
                errors.append(f"题目 '{title}' 已存在，跳过导入")
                continue
            
            difficulty = problem_data.get('difficulty', 'medium')
            
            if problem_source and difficulty not in [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]:
                difficulty = convert_difficulty(problem_source, difficulty)
            
            category_name = problem_data.get('category', '')
            category_id = None
            if category_name:
                categories = ProblemCategory.get_all()
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id
                        break
            
            tags = problem_data.get('tags', [])
            tags_str = json.dumps(tags, ensure_ascii=False) if tags else None
            
            test_cases = problem_data.get('test_cases', [])
            
            problem = Problem(
                title=title,
                description=problem_data.get('description', ''),
                input_format=problem_data.get('input_format', ''),
                output_format=problem_data.get('output_format', ''),
                sample_input=problem_data.get('sample_input', ''),
                sample_output=problem_data.get('sample_output', ''),
                difficulty=difficulty,
                category_id=category_id,
                time_limit=problem_data.get('time_limit', 1),
                memory_limit=problem_data.get('memory_limit', 256),
                test_cases=test_cases,
                source=problem_source,
                source_id=source_id,
                source_url=problem_data.get('source_url'),
                is_public=0,
                tags=tags_str,
                hint=problem_data.get('hint')
            )
            problem.save()
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"题目 '{problem_data.get('title', '未知')}' 导入失败：{str(e)}")
    
    status = 'success' if failed_count == 0 else ('partial' if success_count > 0 else 'failed')
    error_message = '\n'.join(errors) if errors else None
    
    log = ProblemImportLog(
        admin_id=admin_id,
        source=source,
        count=success_count,
        status=status,
        error_message=error_message
    )
    log.save()
    
    return {
        'success': success_count,
        'failed': failed_count,
        'total': len(problems_data),
        'status': status,
        'errors': errors
    }

def get_import_template_json():
    """
    获取JSON导入模板
    """
    template = {
        "problems": [
            {
                "title": "两数之和",
                "description": "给定两个整数a和b，计算它们的和。",
                "input_format": "输入两个整数a和b",
                "output_format": "输出a+b的值",
                "sample_input": "1 2",
                "sample_output": "3",
                "difficulty": "easy",
                "category": "基础算法",
                "tags": ["模拟", "入门"],
                "time_limit": 1,
                "memory_limit": 256,
                "test_cases": [
                    {"input": "1 2", "output": "3"},
                    {"input": "100 200", "output": "300"}
                ],
                "source": "洛谷",
                "source_id": "B2001",
                "source_url": "https://www.luogu.com.cn/problem/B2001",
                "hint": "使用加法运算符即可"
            }
        ]
    }
    return json.dumps(template, ensure_ascii=False, indent=2)

def get_import_template_csv():
    """
    获取CSV导入模板
    """
    return 'title,description,input_format,output_format,sample_input,sample_output,difficulty,category,tags,time_limit,memory_limit,source,source_id,source_url,hint\n"两数之和","给定两个整数a和b，计算它们的和。","输入两个整数a和b","输出a+b的值","1 2","3","easy","基础算法","模拟,入门",1,256,"洛谷","B2001","https://www.luogu.com.cn/problem/B2001","使用加法运算符即可"'

def ensure_url_path(path):
    """
    确保路径有正确的前导斜杠用于URL
    """
    if not path:
        return ''
    path = str(path).strip()
    if not path:
        return ''
    if path.startswith('/'):
        return path
    if path.startswith('uploads/'):
        return '/' + path
    return '/' + path

import json

def from_json(value):
    """
    将JSON字符串转换为Python对象（Jinja2模板过滤器）
    """
    if value is None:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []