from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.utils import get_greeting, get_week_day_chinese, get_learning_days, get_consecutive_learning_days

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
        'consecutive_days': get_consecutive_learning_days(current_user),
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
    
    # 计算学习进度
    total_lessons = sum(len(chapter['lessons']) for chapter in chapters)
    completed_lessons = sum(len([l for l in chapter['lessons'] if l.get('completed')]) for chapter in chapters)
    
    return render_template('student/course_detail.html', course=course, chapters=chapters, materials=materials, discussions=discussions, reviews=reviews, total_lessons=total_lessons, completed_lessons=completed_lessons)

@student_bp.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    import json
    import traceback
    
    print(f'[DEBUG] ===== 开始加载课程详情 lesson_id={lesson_id} =====')
    
    db = None
    lesson = None
    chapter = {}
    course = {}
    chapters = []
    discussions = []
    
    try:
        from flask import current_app
        db = current_app.db
        print(f'[DEBUG] 数据库连接成功')
    except Exception as e:
        print(f'[ERROR] 获取数据库连接失败: {e}')
    
    if db:
        try:
            lesson = db.find_by_id('lessons', lesson_id)
            print(f'[DEBUG] 查询课程结果: {lesson is not None}')
            if not lesson:
                flash('课程内容不存在', 'error')
                return redirect(url_for('student.dashboard'))
        except Exception as e:
            print(f'[ERROR] 查询课程失败: {e}')
            traceback.print_exc()
            flash('课程内容加载失败', 'error')
            return redirect(url_for('student.dashboard'))
        
        if lesson:
            try:
                chapter_id = lesson.get('chapter_id')
                print(f'[DEBUG] chapter_id: {chapter_id}, type: {type(chapter_id)}')
                if chapter_id:
                    chapter = db.find_by_id('chapters', int(chapter_id) if isinstance(chapter_id, str) else chapter_id)
                    print(f'[DEBUG] 查询章节结果: {chapter is not None}')
            except Exception as e:
                print(f'[ERROR] 查询章节失败: {e}')
                chapter = {}
            
            try:
                course_id = None
                if chapter and isinstance(chapter, dict):
                    course_id = chapter.get('course_id')
                
                print(f'[DEBUG] course_id: {course_id}')
                
                if course_id:
                    course = db.find_by_id('courses', int(course_id) if isinstance(course_id, str) else course_id)
                    print(f'[DEBUG] 查询课程结果: {course is not None}')
                    
                    if course and course.get('id'):
                        try:
                            chapters = db.find_all('chapters', {'course_id': course['id']})
                            print(f'[DEBUG] 查询到 {len(chapters)} 个章节')
                            
                            for c in chapters:
                                try:
                                    c['lessons'] = db.find_all('lessons', {'chapter_id': c['id']})
                                    for l in c['lessons']:
                                        l['completed'] = False
                                except:
                                    c['lessons'] = []
                        except Exception as e:
                            print(f'[ERROR] 查询章节列表失败: {e}')
                            chapters = []
                else:
                    course = {}
            except Exception as e:
                print(f'[ERROR] 查询课程/章节失败: {e}')
                course = {}
                chapters = []
            
            try:
                discussions = db.find_all('discussions', {'lesson_id': lesson_id})
            except:
                discussions = []
    
    total_lessons = sum(len(c.get('lessons', [])) for c in chapters) if chapters else 0
    completed_lessons = 0
    
    media_files_list = []
    
    if lesson and isinstance(lesson, dict):
        media_files_raw = lesson.get('media_files')
        print(f'[DEBUG] media_files_raw: {media_files_raw}, type: {type(media_files_raw)}')
        
        if media_files_raw and isinstance(media_files_raw, str):
            try:
                cleaned = media_files_raw.strip()
                if cleaned and cleaned not in ['[]', 'null', 'None', '', 'none']:
                    media_files_list = json.loads(cleaned)
                    print(f'[DEBUG] 解析 JSON 成功, 文件数: {len(media_files_list)}')
            except json.JSONDecodeError as e:
                print(f'[ERROR] JSON 解析失败: {e}')
                media_files_list = []
            except Exception as e:
                print(f'[ERROR] 处理 media_files 失败: {e}')
                media_files_list = []
        elif isinstance(media_files_raw, list):
            media_files_list = media_files_raw
        
        lesson['media_files_list'] = media_files_list
    else:
        lesson = {'id': lesson_id, 'title': f'课程 #{lesson_id}', 'content': '', 'media_files_list': []}
    
    print(f'[DEBUG] ===== 准备渲染模板 =====')
    print(f'[DEBUG] lesson keys: {list(lesson.keys()) if lesson else "None"}')
    print(f'[DEBUG] media_files_list length: {len(media_files_list)}')
    
    try:
        return render_template('student/lesson_detail.html',
                             lesson=lesson,
                             course=course or {},
                             chapter=chapter or {},
                             chapters=chapters or [],
                             discussions=discussions or [],
                             total_lessons=total_lessons,
                             completed_lessons=completed_lessons,
                             prev_lesson=None,
                             next_lesson=None)
    except Exception as e:
        print(f'[ERROR] 渲染模板失败: {e}')
        traceback.print_exc()
        flash('页面渲染失败，请稍后重试', 'error')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/lessons/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    from flask import current_app
    from app.services.learning_progress_service import LearningProgressService
    
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        flash('课程内容不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    course = db.find_by_id('courses', chapter['course_id'])
    
    LearningProgressService.complete_lesson(
        user_id=current_user.id,
        lesson_id=lesson_id,
        course_id=course['id'],
        chapter_id=chapter['id']
    )
    
    flash('课程学习完成', 'success')
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

@student_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    from werkzeug.security import check_password_hash, generate_password_hash
    from app.models import User
    from werkzeug.utils import secure_filename
    import os

    if request.method == 'POST':
        db = current_app.db
        ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

        nickname = request.form.get('nickname', '').strip()
        email = request.form.get('email', '').strip()
        bio = request.form.get('bio', '').strip()
        avatar = request.files.get('avatar')

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        print(f'[DEBUG] Settings POST - nickname: {nickname}, email: {email}, bio: {bio[:20] if bio else None}')
        print(f'[DEBUG] Avatar file: {avatar.filename if avatar else None}')

        update_data = {
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if nickname:
            update_data['nickname'] = nickname
        if email:
            update_data['email'] = email
        if bio is not None:
            update_data['bio'] = bio

        if avatar and avatar.filename:
            print(f'[INFO] Processing avatar upload: {avatar.filename}')
            import uuid
            filename = secure_filename(avatar.filename)
            if not filename:
                flash('文件名包含非法字符', 'error')
                return redirect(url_for('student.settings'))

            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext not in ALLOWED_AVATAR_EXTENSIONS:
                flash(f'不支持的文件类型: .{file_ext}，仅支持 PNG、JPG、GIF、WEBP 格式', 'error')
                return redirect(url_for('student.settings'))

            safe_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:12]}.{file_ext}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')

            try:
                os.makedirs(upload_path, exist_ok=True)
                full_path = os.path.join(upload_path, safe_filename)
                avatar.save(full_path)

                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    print(f'[OK] Avatar saved: {safe_filename} ({file_size} bytes)')
                    update_data['avatar'] = f"/uploads/avatars/{safe_filename}"
                else:
                    print(f'[ERR] File not found after save: {full_path}')
                    flash('头像文件保存失败', 'error')
                    return redirect(url_for('student.settings'))
            except Exception as e:
                print(f'[ERR] Failed to save avatar: {e}')
                import traceback
                traceback.print_exc()
                flash(f'头像保存失败: {str(e)}', 'error')
                return redirect(url_for('student.settings'))
        elif avatar:
            print('[INFO] Avatar field exists but no file selected')

        user_id = current_user.id
        try:
            user_id = int(user_id)
        except ValueError:
            flash('用户ID无效', 'error')
            return redirect(url_for('student.settings'))

        print(f'[INFO] Updating user {user_id} with data: {list(update_data.keys())}')
        success = db.update('users', user_id, update_data)

        avatar_updated = 'avatar' in update_data

        if success:
            print(f'[OK] User {user_id} updated successfully')
            print(f'[DEBUG] Avatar updated: {avatar_updated}')

            try:
                print(f'[INFO] Forcing session reload...')

                updated_user_data = db.find_by_id('users', user_id)
                if updated_user_data:
                    print(f'[INFO] Reloaded user data from DB, avatar: {updated_user_data.get("avatar", "None")}')

                    for key, value in updated_user_data.items():
                        if hasattr(current_user, key):
                            try:
                                setattr(current_user, key, value)
                            except Exception as attr_err:
                                print(f'[WARN] Could not set attribute {key}: {attr_err}')

                    from flask_login import login_user
                    login_user(current_user._get_current_object(), remember=True)
                    print(f'[OK] User session force-refreshed')
                    print(f'[OK] Current user avatar is now: {current_user.avatar}')
                else:
                    print(f'[WARN] User {user_id} not found in database after update')
            except Exception as e:
                print(f'[WARN] Failed to refresh user session: {e}')
                import traceback
                traceback.print_exc()
        else:
            print(f'[ERR] Failed to update user {user_id}')

        if new_password:
            if not current_password:
                flash('修改密码需要输入当前密码', 'error')
            elif new_password != confirm_password:
                flash('两次输入的密码不一致', 'error')
            elif len(new_password) < 6:
                flash('密码长度至少为6位', 'error')
            else:
                user_data = db.find_by_id('users', current_user.id)
                if user_data and check_password_hash(user_data['password_hash'], current_password):
                    db.update('users', current_user.id, {
                        'password_hash': generate_password_hash(new_password),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    flash('设置保存成功，密码已更新，请重新登录', 'success')
                    return redirect(url_for('auth.logout'))
                else:
                    flash('当前密码错误，其他设置已保存', 'warning')

        if success:
            if avatar_updated:
                flash('✅ 设置保存成功！头像已更新（如未显示请刷新页面 Ctrl+F5）', 'success')
            else:
                flash('✅ 设置保存成功！', 'success')
        else:
            flash('❌ 设置保存失败，请稍后重试', 'error')

        response = redirect(url_for('student.settings'))

        if avatar_updated:
            from flask import make_response
            response = make_response(response)
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response

    context = {
        'greeting': get_greeting(),
        'week_day': get_week_day_chinese(),
        'consecutive_days': get_consecutive_learning_days(current_user),
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
    from werkzeug.utils import secure_filename
    import os
    
    ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    nickname = request.form.get('nickname')
    avatar = request.files.get('avatar')
    
    db = current_app.db
    
    update_data = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if nickname:
        update_data['nickname'] = nickname
    
    if avatar and avatar.filename:
        import uuid
        filename = secure_filename(avatar.filename)
        if not filename:
            flash('文件名包含非法字符', 'error')
            return redirect(url_for('student.settings'))

        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_ext not in ALLOWED_AVATAR_EXTENSIONS:
            flash('不支持的文件类型，仅支持 PNG、JPG、GIF、WEBP 格式', 'error')
            return redirect(url_for('student.settings'))

        safe_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:12]}.{file_ext}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(upload_path, exist_ok=True)
        avatar.save(os.path.join(upload_path, safe_filename))
        update_data['avatar'] = f"/uploads/avatars/{safe_filename}"
    
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
        'consecutive_days': get_consecutive_learning_days(current_user),
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
        'consecutive_days': get_consecutive_learning_days(current_user),
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
        'consecutive_days': get_consecutive_learning_days(current_user)
    }
    
    return render_template('student/submissions.html', **context)

@student_bp.route('/lessons/<int:lesson_id>/discussions/api')
@login_required
def get_lesson_discussions(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    discussions = db.find_all('discussions', {'lesson_id': lesson_id})
    discussions.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    result = []
    for disc in discussions:
        user = db.find_by_id('users', disc['user_id'])
        result.append({
            'id': disc['id'],
            'title': disc.get('title', ''),
            'content': disc.get('content', ''),
            'user_name': user.get('username', '未知用户') if user else '未知用户',
            'created_at': disc.get('created_at', ''),
            'user_id': disc.get('user_id')
        })

    return jsonify({'success': True, 'discussions': result})

@student_bp.route('/lessons/<int:lesson_id>/discussions/api/create', methods=['POST'])
@login_required
def create_lesson_discussion_api(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    title = request.form.get('title', '')
    content = request.form.get('content', '')

    if not title or not content:
        return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400

    discussion_data = {
        'lesson_id': lesson_id,
        'user_id': current_user.id,
        'title': title,
        'content': content
    }

    discussion_id = db.insert('discussions', discussion_data)

    return jsonify({
        'success': True,
        'discussion': {
            'id': discussion_id,
            'title': title,
            'content': content,
            'user_name': current_user.username,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': current_user.id
        }
    })

@student_bp.route('/lessons/<int:lesson_id>/notes/api')
@login_required
def get_lesson_notes(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    notes = db.find_all('lesson_notes', {'lesson_id': lesson_id, 'user_id': current_user.id})

    if notes:
        return jsonify({'success': True, 'notes': notes[0]})
    else:
        return jsonify({'success': True, 'notes': None})

@student_bp.route('/lessons/<int:lesson_id>/notes/api/save', methods=['POST'])
@login_required
def save_lesson_note(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    content = request.form.get('content', '')

    existing_notes = db.find_all('lesson_notes', {'lesson_id': lesson_id, 'user_id': current_user.id})

    if existing_notes:
        success = db.update('lesson_notes', existing_notes[0]['id'], {'content': content, 'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    else:
        note_id = db.insert('lesson_notes', {
            'lesson_id': lesson_id,
            'user_id': current_user.id,
            'content': content,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        success = note_id > 0

    return jsonify({'success': success})

@student_bp.route('/lessons/<int:lesson_id>/bookmarks/api')
@login_required
def get_lesson_bookmarks(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    bookmarks = db.find_all('lesson_bookmarks', {'lesson_id': lesson_id, 'user_id': current_user.id})
    bookmarks.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    result = []
    for bm in bookmarks:
        result.append({
            'id': bm['id'],
            'content': bm.get('content', ''),
            'position': bm.get('position', 0),
            'color': bm.get('color', '#667eea'),
            'created_at': bm.get('created_at', '')
        })

    return jsonify({'success': True, 'bookmarks': result})

@student_bp.route('/lessons/<int:lesson_id>/bookmarks/api/create', methods=['POST'])
@login_required
def create_lesson_bookmark(lesson_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    content = request.form.get('content', '')
    position = request.form.get('position', 0)
    color = request.form.get('color', '#667eea')

    if not content:
        return jsonify({'success': False, 'error': '标注内容不能为空'}), 400

    bookmark_id = db.insert('lesson_bookmarks', {
        'lesson_id': lesson_id,
        'user_id': current_user.id,
        'content': content,
        'position': position,
        'color': color,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    return jsonify({
        'success': True,
        'bookmark': {
            'id': bookmark_id,
            'content': content,
            'position': position,
            'color': color,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@student_bp.route('/bookmarks/<int:bookmark_id>/api/delete', methods=['POST'])
@login_required
def delete_bookmark(bookmark_id):
    from flask import jsonify
    from flask import current_app
    db = current_app.db

    bookmark = db.find_by_id('lesson_bookmarks', bookmark_id)

    if not bookmark or int(bookmark['user_id']) != current_user.id:
        return jsonify({'success': False, 'error': '无权删除此标注'}), 403

    success = db.delete('lesson_bookmarks', bookmark_id)

    return jsonify({'success': success})
