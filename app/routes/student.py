from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.utils import get_greeting, get_week_day_chinese, get_learning_days

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    from flask import current_app
    db = current_app.db
    courses = db.read_table('courses')
    published_courses = courses  # 由于courses表没有status字段，显示所有课程
    
    my_progress = db.find_all('learning_progress', {'user_id': current_user.id})
    completed_lessons = len([p for p in my_progress if p.get('status') == 'completed'])
    
    context = {
        'courses': published_courses,
        'completed_lessons': completed_lessons,
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'learning_days': get_learning_days(current_user),
        'consecutive_days': 8,
        'registration_time': current_user.created_at if hasattr(current_user, 'created_at') else '2024-03-01',
        'last_login': current_user.updated_at if hasattr(current_user, 'updated_at') else '2024-03-15 14:30'
    }
    
    return render_template('student/dashboard.html', **context)

@student_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course:
        flash('课程不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    chapters = db.find_all('chapters', {'course_id': course_id})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))
    
    for chapter in chapters:
        chapter['lessons'] = db.find_all('lessons', {'chapter_id': chapter['id']})
        chapter['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))
        
        for lesson in chapter['lessons']:
            progress = db.find_by_field('learning_progress', 'user_id', current_user.id)
            progress = [p for p in progress if int(p.get('lesson_id', 0)) == lesson['id']]
            lesson['completed'] = len(progress) > 0 and progress[0].get('status') == 'completed'
    
    # 获取课程资料
    materials = db.find_all('materials', {'course_id': course_id})
    
    # 获取讨论
    discussions = db.find_all('discussions', {'course_id': course_id})
    
    # 获取评价
    reviews = db.find_all('reviews', {'course_id': course_id})
    
    return render_template('student/course_detail.html', course=course, chapters=chapters, materials=materials, discussions=discussions, reviews=reviews)

@student_bp.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        flash('课程内容不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    course = db.find_by_id('courses', chapter['course_id'])
    
    # 获取所有章节和小节
    chapters = db.find_all('chapters', {'course_id': course['id']})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))
    
    for c in chapters:
        c['lessons'] = db.find_all('lessons', {'chapter_id': c['id']})
        c['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))
        
        for l in c['lessons']:
            progress = db.find_by_field('learning_progress', 'user_id', current_user.id)
            progress = [p for p in progress if int(p.get('lesson_id', 0)) == l['id']]
            l['completed'] = len(progress) > 0 and progress[0].get('status') == 'completed'
    
    # 获取讨论
    discussions = db.find_all('discussions', {'lesson_id': lesson_id})
    
    # 计算学习进度
    total_lessons = sum(len(c['lessons']) for c in chapters)
    completed_lessons = sum(len([l for l in c['lessons'] if l.get('completed')]) for c in chapters)
    
    # 查找上一节和下一节
    prev_lesson = None
    next_lesson = None
    
    # 将所有小节放入一个列表
    all_lessons = []
    for c in chapters:
        all_lessons.extend(c['lessons'])
    
    # 按order_index排序
    all_lessons.sort(key=lambda x: int(x.get('order_index', 0)))
    
    # 查找当前小节的索引
    current_index = -1
    for i, l in enumerate(all_lessons):
        if l['id'] == lesson['id']:
            current_index = i
            break
    
    # 查找上一节和下一节
    if current_index > 0:
        prev_lesson = all_lessons[current_index - 1]
    if current_index < len(all_lessons) - 1:
        next_lesson = all_lessons[current_index + 1]
    
    return render_template('student/lesson_detail.html', 
                         lesson=lesson, 
                         course=course, 
                         chapter=chapter, 
                         chapters=chapters, 
                         discussions=discussions, 
                         total_lessons=total_lessons, 
                         completed_lessons=completed_lessons, 
                         prev_lesson=prev_lesson, 
                         next_lesson=next_lesson)

@student_bp.route('/lessons/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        flash('课程内容不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    progress = db.find_by_field('learning_progress', 'user_id', current_user.id)
    progress = [p for p in progress if int(p.get('lesson_id', 0)) == lesson_id]
    
    if progress:
        progress_data = {
            'status': 'completed',
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        db.update('learning_progress', progress[0]['id'], progress_data)
    else:
        progress_data = {
            'user_id': current_user.id,
            'lesson_id': lesson_id,
            'status': 'completed',
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        db.insert('learning_progress', progress_data)
    
    flash('课程学习完成', 'success')
    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    return redirect(url_for('student.lesson_detail', lesson_id=lesson_id))

@student_bp.route('/lessons/<int:lesson_id>/discussions/create', methods=['POST'])
@login_required
def create_lesson_discussion(lesson_id):
    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        flash('课程内容不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    discussion_data = {
        'lesson_id': lesson_id,
        'user_id': current_user.id,
        'title': title,
        'content': content
    }
    
    db.insert('discussions', discussion_data)
    flash('讨论发布成功', 'success')
    return redirect(url_for('student.lesson_detail', lesson_id=lesson_id))

@student_bp.route('/courses/<int:course_id>/discussions/create', methods=['POST'])
@login_required
def create_discussion(course_id):
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course:
        flash('课程不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    discussion_data = {
        'course_id': course_id,
        'user_id': current_user.id,
        'title': title,
        'content': content
    }
    
    db.insert('discussions', discussion_data)
    flash('讨论发布成功', 'success')
    return redirect(url_for('student.course_detail', course_id=course_id))

@student_bp.route('/courses/<int:course_id>/reviews/create', methods=['POST'])
@login_required
def create_review(course_id):
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course:
        flash('课程不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    rating = request.form.get('rating')
    content = request.form.get('content')
    
    existing_review = db.find_all('reviews', {'course_id': course_id, 'user_id': current_user.id})
    
    if existing_review:
        review_data = {
            'rating': rating,
            'content': content
        }
        db.update('reviews', existing_review[0]['id'], review_data)
    else:
        review_data = {
            'course_id': course_id,
            'user_id': current_user.id,
            'rating': rating,
            'content': content
        }
        db.insert('reviews', review_data)
    
    flash('评价提交成功', 'success')
    return redirect(url_for('student.course_detail', course_id=course_id))

@student_bp.route('/test-user-info')
@login_required
def test_user_info():
    context = {
        'greeting': get_greeting()
    }
    
    return render_template('student/test_user_info.html', **context)

@student_bp.route('/settings')
@login_required
def settings():
    context = {
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'consecutive_days': 8,
        'registration_time': current_user.created_at if hasattr(current_user, 'created_at') else '2024-03-01',
        'last_login': current_user.updated_at if hasattr(current_user, 'updated_at') else '2024-03-15 14:30',
        'learning_days': get_learning_days(current_user),
        'today_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    return render_template('student/settings.html', **context)

@student_bp.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    from app.models import User
    from flask import current_app
    from datetime import datetime
    import os
    
    nickname = request.form.get('nickname')
    avatar = request.files.get('avatar')
    
    db = current_app.db
    
    update_data = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if nickname:
        update_data['nickname'] = nickname
    
    if avatar and avatar.filename:
        filename = f"avatar_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{avatar.filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(upload_path, exist_ok=True)
        avatar.save(os.path.join(upload_path, filename))
        update_data['avatar'] = f"/uploads/avatars/{filename}"
    
    # 确保 current_user.id 是整数类型
    user_id = current_user.id
    try:
        user_id = int(user_id)
    except ValueError:
        flash('用户ID无效', 'error')
        return redirect(url_for('student.settings'))
    
    # 更新用户数据
    success = db.update('users', user_id, update_data)
    
    if success:
        # 重新加载用户信息
        from flask_login import login_user
        updated_user = User.get_by_id(user_id)
        if updated_user:
            login_user(updated_user, remember=True)
        flash('个人资料更新成功', 'success')
    else:
        flash('个人资料更新失败', 'error')
    
    return redirect(url_for('student.settings'))

@student_bp.route('/settings/password', methods=['POST'])
@login_required
def update_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    from flask import current_app
    
    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_password = request.form.get('confirmPassword')
    
    if not current_password or not new_password or not confirm_password:
        flash('请填写所有密码字段', 'error')
        return redirect(url_for('student.settings'))
    
    if new_password != confirm_password:
        flash('两次输入的密码不一致', 'error')
        return redirect(url_for('student.settings'))
    
    if len(new_password) < 6:
        flash('密码长度至少为6位', 'error')
        return redirect(url_for('student.settings'))
    
    db = current_app.db
    user_data = db.find_by_id('users', current_user.id)
    
    if not user_data or not check_password_hash(user_data['password_hash'], current_password):
        flash('当前密码错误', 'error')
        return redirect(url_for('student.settings'))
    
    update_data = {
        'password_hash': generate_password_hash(new_password),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    db.update('users', current_user.id, update_data)
    
    flash('密码修改成功，请重新登录', 'success')
    return redirect(url_for('auth.logout'))

@student_bp.route('/settings/delete', methods=['POST'])
@login_required
def delete_account():
    from flask import current_app
    
    db = current_app.db
    
    db.delete('users', current_user.id)
    
    flash('账户已注销', 'success')
    return redirect(url_for('auth.login'))

@student_bp.route('/practice')
@login_required
def practice():
    from flask import current_app
    from app.models import ProblemCategory, Problem, TeacherAssignment, TeacherSelectedProblem
    from app.utils import get_difficulty_label, get_difficulty_icon
    db = current_app.db
    
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty')
    search = request.args.get('search', '')
    
    categories = ProblemCategory.get_all()
    main_categories = [c for c in categories if c.parent_id is None]
    
    for main_cat in main_categories:
        main_cat.subcategories = [c for c in categories if c.parent_id == main_cat.id]
    
    visible_problem_ids = TeacherSelectedProblem.get_visible_problems_for_student(current_user.id)
    
    all_problems = Problem.get_all()
    problems = [p for p in all_problems if p.id in visible_problem_ids]
    
    if category_id:
        category_problems = Problem.get_by_category(category_id)
        category_problem_ids = [p.id for p in category_problems]
        problems = [p for p in problems if p.id in category_problem_ids]
    
    if difficulty:
        problems = [p for p in problems if p.difficulty == difficulty]
    
    if search:
        problems = [p for p in problems if search.lower() in p.title.lower()]
    
    assignments = TeacherAssignment.get_all()
    
    context = {
        'categories': main_categories,
        'problems': problems,
        'current_category_id': category_id,
        'current_difficulty': difficulty,
        'search': search,
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'consecutive_days': 8,
        'assignments': assignments,
        'get_difficulty_label': get_difficulty_label,
        'get_difficulty_icon': get_difficulty_icon
    }
    
    return render_template('student/practice.html', **context)

@student_bp.route('/practice/<int:problem_id>')
@login_required
def problem_detail(problem_id):
    from flask import current_app
    from app.models import Problem, Submission
    db = current_app.db
    
    problem = Problem.get_by_id(problem_id)
    
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('student.practice'))
    
    submissions = Submission.get_by_user(current_user.id)
    problem_submissions = [s for s in submissions if s.problem_id == problem_id]
    
    context = {
        'problem': problem,
        'submissions': problem_submissions,
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'consecutive_days': 8,
        'questions': []
    }
    
    return render_template('student/problem_detail.html', **context)

@student_bp.route('/practice/<int:problem_id>/submit', methods=['POST'])
@login_required
def submit_code(problem_id):
    from flask import current_app
    from app.models import Problem, Submission, evaluate_code
    import json
    db = current_app.db
    
    problem = Problem.get_by_id(problem_id)
    
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('student.practice'))
    
    code = request.form.get('code')
    
    if not code:
        flash('请输入代码', 'error')
        return redirect(url_for('student.problem_detail', problem_id=problem_id))
    
    result = evaluate_code(code, problem.test_cases, problem.time_limit, problem.memory_limit)
    
    submission_data = {
        'user_id': current_user.id,
        'problem_id': problem_id,
        'code': code,
        'status': result['status'],
        'error_message': result['message'],
        'submit_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    submission = Submission(**submission_data)
    submission.save()
    
    if result['status'] == 'AC':
        flash('恭喜！所有测试用例通过！', 'success')
    else:
        flash(f'提交结果：{result["status"]}', 'error')
    
    return redirect(url_for('student.problem_detail', problem_id=problem_id))

@student_bp.route('/practice/submissions')
@login_required
def submissions():
    from flask import current_app
    from app.models import Submission, Problem
    db = current_app.db
    
    submissions = Submission.get_by_user(current_user.id)
    submissions.sort(key=lambda x: x.submit_time, reverse=True)
    
    for submission in submissions:
        submission.problem = Problem.get_by_id(submission.problem_id)
    
    context = {
        'submissions': submissions,
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'consecutive_days': 8
    }
    
    return render_template('student/submissions.html', **context)
