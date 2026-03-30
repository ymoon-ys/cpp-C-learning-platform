from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    stats = {
        'total_users': db.count('users'),
        'total_courses': db.count('courses'),
        'total_teachers': db.count('users', {'role': 'teacher'}),
        'total_students': db.count('users', {'role': 'student'})
    }
    
    users = User.get_all()
    courses = db.read_table('courses')
    
    return render_template('admin/dashboard.html', stats=stats, users=users, courses=courses)

@admin_bp.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    users = User.get_all()
    
    # 按角色分组
    admins = [user for user in users if user.role == 'admin']
    teachers = [user for user in users if user.role == 'teacher']
    students = [user for user in users if user.role == 'student']
    
    return render_template('admin/users.html', users=users, admins=admins, teachers=teachers, students=students)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    if user_id == current_user.id:
        flash('不能删除自己的账户', 'error')
        return redirect(url_for('admin.users'))
    
    from flask import current_app
    db = current_app.db
    db.delete('users', user_id)
    flash('用户已删除', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/courses')
@login_required
def courses():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    courses = db.read_table('courses')
    return render_template('admin/courses.html', courses=courses)

@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    db.delete('courses', course_id)
    flash('课程已删除', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    return render_template('admin/settings.html')

@admin_bp.route('/problems')
@login_required
def problems():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, ProblemCategory
    from app.utils import get_difficulty_label
    db = current_app.db
    
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty')
    source = request.args.get('source')
    search = request.args.get('search', '')
    
    categories = ProblemCategory.get_all()
    main_categories = [c for c in categories if c.parent_id is None]
    
    for main_cat in main_categories:
        main_cat.subcategories = [c for c in categories if c.parent_id == main_cat.id]
    
    problem_list = Problem.get_all()
    
    if category_id:
        problem_list = Problem.get_by_category(category_id)
    
    if difficulty:
        problem_list = [p for p in problem_list if p.difficulty == difficulty]
    
    if source:
        problem_list = [p for p in problem_list if p.source == source]
    
    if search:
        problem_list = [p for p in problem_list if search.lower() in p.title.lower()]
    
    sources = set()
    for p in Problem.get_all():
        if p.source:
            sources.add(p.source)
    
    return render_template('admin/problems.html', 
                          categories=main_categories, 
                          problems=problem_list, 
                          current_category_id=category_id,
                          current_difficulty=difficulty,
                          current_source=source,
                          current_search=search,
                          sources=list(sources),
                          get_difficulty_label=get_difficulty_label)

@admin_bp.route('/problems/add', methods=['GET', 'POST'])
@login_required
def add_problem():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, ProblemCategory
    from app.utils import convert_difficulty, DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD
    import json
    from datetime import datetime
    db = current_app.db
    
    categories = ProblemCategory.get_all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        input_format = request.form.get('input_format')
        output_format = request.form.get('output_format')
        sample_input = request.form.get('sample_input')
        sample_output = request.form.get('sample_output')
        difficulty = request.form.get('difficulty')
        category_id = request.form.get('category_id', type=int)
        time_limit = request.form.get('time_limit', type=int, default=1)
        memory_limit = request.form.get('memory_limit', type=int, default=256)
        
        source = request.form.get('source')
        source_id = request.form.get('source_id')
        source_url = request.form.get('source_url')
        hint = request.form.get('hint')
        tags_str = request.form.get('tags')
        is_public = 1 if request.form.get('is_public') else 0
        
        test_cases_input = request.form.get('test_cases')
        test_cases = []
        if test_cases_input:
            try:
                test_cases = json.loads(test_cases_input)
            except:
                test_cases = []
        
        tags = None
        if tags_str:
            tags = json.dumps([t.strip() for t in tags_str.split(',') if t.strip()], ensure_ascii=False)
        
        problem = Problem(
            title=title,
            description=description,
            input_format=input_format,
            output_format=output_format,
            sample_input=sample_input,
            sample_output=sample_output,
            difficulty=difficulty,
            category_id=category_id,
            time_limit=time_limit,
            memory_limit=memory_limit,
            test_cases=test_cases,
            source=source,
            source_id=source_id,
            source_url=source_url,
            is_public=is_public,
            tags=tags,
            hint=hint
        )
        problem.save()
        
        flash('题目添加成功', 'success')
        return redirect(url_for('admin.problems'))
    
    return render_template('admin/problem_form.html', categories=categories, problem=None)

@admin_bp.route('/problems/<int:problem_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_problem(problem_id):
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, ProblemCategory
    from app.utils import convert_difficulty
    import json
    db = current_app.db
    
    problem = Problem.get_by_id(problem_id)
    
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('admin.problems'))
    
    categories = ProblemCategory.get_all()
    
    if request.method == 'POST':
        problem.title = request.form.get('title')
        problem.description = request.form.get('description')
        problem.input_format = request.form.get('input_format')
        problem.output_format = request.form.get('output_format')
        problem.sample_input = request.form.get('sample_input')
        problem.sample_output = request.form.get('sample_output')
        problem.difficulty = request.form.get('difficulty')
        problem.category_id = request.form.get('category_id', type=int)
        problem.time_limit = request.form.get('time_limit', type=int, default=1)
        problem.memory_limit = request.form.get('memory_limit', type=int, default=256)
        
        problem.source = request.form.get('source')
        problem.source_id = request.form.get('source_id')
        problem.source_url = request.form.get('source_url')
        problem.hint = request.form.get('hint')
        problem.is_public = 1 if request.form.get('is_public') else 0
        
        tags_str = request.form.get('tags')
        if tags_str:
            problem.tags = json.dumps([t.strip() for t in tags_str.split(',') if t.strip()], ensure_ascii=False)
        else:
            problem.tags = None
        
        test_cases_input = request.form.get('test_cases')
        if test_cases_input:
            try:
                problem.test_cases = json.loads(test_cases_input)
            except:
                pass
        
        problem.save()
        
        flash('题目更新成功', 'success')
        return redirect(url_for('admin.problems'))
    
    return render_template('admin/problem_form.html', categories=categories, problem=problem)

@admin_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
@login_required
def delete_problem(problem_id):
    if current_user.role != 'admin':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem
    db = current_app.db
    db.delete('problems', problem_id)
    flash('题目已删除', 'success')
    return redirect(url_for('admin.problems'))

@admin_bp.route('/problems/import', methods=['GET', 'POST'])
@login_required
def import_problems_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, ProblemCategory
    from app.utils import (parse_json_import, parse_csv_import, import_problems,
                          get_import_template_json, get_import_template_csv,
                          get_difficulty_stats, get_difficulty_label)
    db = current_app.db
    
    if request.method == 'POST':
        import_type = request.form.get('import_type')
        source = request.form.get('source', '')
        
        if import_type == 'json':
            file = request.files.get('json_file')
            if not file or not file.filename:
                flash('请选择JSON文件', 'error')
                return redirect(url_for('admin.import_problems_page'))
            
            try:
                file_content = file.read().decode('utf-8')
                success, problems, error = parse_json_import(file_content)
                
                if not success:
                    flash(error, 'error')
                    return redirect(url_for('admin.import_problems_page'))
                
                result = import_problems(problems, current_user.id, source)
                
                if result['status'] == 'success':
                    flash(f"成功导入 {result['success']} 道题目", 'success')
                elif result['status'] == 'partial':
                    flash(f"部分导入成功：成功 {result['success']} 道，失败 {result['failed']} 道", 'warning')
                else:
                    flash('导入失败', 'error')
                
            except Exception as e:
                flash(f'导入出错：{str(e)}', 'error')
            
            return redirect(url_for('admin.import_problems_page'))
        
        elif import_type == 'csv':
            file = request.files.get('csv_file')
            if not file or not file.filename:
                flash('请选择CSV文件', 'error')
                return redirect(url_for('admin.import_problems_page'))
            
            try:
                file_content = file.read().decode('utf-8')
                success, problems, error = parse_csv_import(file_content)
                
                if not success:
                    flash(error, 'error')
                    return redirect(url_for('admin.import_problems_page'))
                
                result = import_problems(problems, current_user.id, source)
                
                if result['status'] == 'success':
                    flash(f"成功导入 {result['success']} 道题目", 'success')
                elif result['status'] == 'partial':
                    flash(f"部分导入成功：成功 {result['success']} 道，失败 {result['failed']} 道", 'warning')
                else:
                    flash('导入失败', 'error')
                
            except Exception as e:
                flash(f'导入出错：{str(e)}', 'error')
            
            return redirect(url_for('admin.import_problems_page'))
    
    problems = Problem.get_all()
    stats = get_difficulty_stats(problems)
    
    return render_template('admin/problems_import.html', 
                          problems=problems, 
                          stats=stats,
                          get_difficulty_label=get_difficulty_label)

@admin_bp.route('/problems/import/template/<template_type>')
@login_required
def download_template(template_type):
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from app.utils import get_import_template_json, get_import_template_csv
    
    if template_type == 'json':
        content = get_import_template_json()
        return Response(
            content,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment;filename=problems_template.json'}
        )
    elif template_type == 'csv':
        content = get_import_template_csv()
        return Response(
            content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=problems_template.csv'}
        )
    else:
        flash('不支持的模板类型', 'error')
        return redirect(url_for('admin.import_problems_page'))

@admin_bp.route('/problems/import/logs')
@login_required
def import_logs():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import ProblemImportLog, User
    db = current_app.db
    
    logs = ProblemImportLog.get_all()
    logs.sort(key=lambda x: x.created_at if x.created_at else '', reverse=True)
    
    for log in logs:
        log.admin = User.get_by_id(log.admin_id)
    
    return render_template('admin/import_logs.html', logs=logs)


