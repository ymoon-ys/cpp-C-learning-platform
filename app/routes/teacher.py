from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.utils import get_greeting, get_week_day_chinese

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md'}

@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    courses = db.find_all('courses', {'teacher_id': current_user.id})
    stats = {
        'total_courses': len(courses),
        'total_students': 0,
        'total_chapters': sum(len(db.find_all('chapters', {'course_id': course['id']})) for course in courses),
        'total_lessons': sum(len(db.find_all('lessons', {'chapter_id': chapter['id']})) for course in courses for chapter in db.find_all('chapters', {'course_id': course['id']}))
    }
    
    return render_template('teacher/dashboard.html', courses=courses, stats=stats, 
                         greeting=get_greeting(), week_day=get_week_day_chinese(),
                         consecutive_days=0)

@teacher_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # 获取章节和小节
    chapters = db.find_all('chapters', {'course_id': course_id})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))
    
    for chapter in chapters:
        chapter['lessons'] = db.find_all('lessons', {'chapter_id': chapter['id']})
        chapter['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))
    
    # 获取课程资料
    materials = db.find_all('materials', {'course_id': course_id})

    return render_template('teacher/course_detail.html', course=course, chapters=chapters, materials=materials)

@teacher_bp.route('/courses/<int:course_id>/preview')
@login_required
def preview_as_student(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))

    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)

    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))

    chapters = db.find_all('chapters', {'course_id': course_id})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))

    for chapter in chapters:
        chapter['lessons'] = db.find_all('lessons', {'chapter_id': chapter['id']})
        chapter['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))

        for lesson in chapter['lessons']:
            progress = db.find_by_field('learning_progress', 'user_id', current_user.id)
            progress = [p for p in progress if int(p.get('lesson_id', 0)) == lesson['id']]
            lesson['completed'] = len(progress) > 0 and progress[0].get('status') == 'completed'

    materials = db.find_all('materials', {'course_id': course_id})
    discussions = db.find_all('discussions', {'course_id': course_id})
    reviews = db.find_all('reviews', {'course_id': course_id})

    total_lessons = sum(len(chapter['lessons']) for chapter in chapters)
    completed_lessons = sum(len([l for l in chapter['lessons'] if l.get('completed')]) for chapter in chapters)

    return render_template('student/course_detail.html',
                         course=course,
                         chapters=chapters,
                         materials=materials,
                         discussions=discussions,
                         reviews=reviews,
                         total_lessons=total_lessons,
                         completed_lessons=completed_lessons,
                         is_preview_mode=True)

@teacher_bp.route('/lessons/<int:lesson_id>/preview')
@login_required
def preview_lesson_as_student(lesson_id):
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))

    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)

    if not lesson:
        flash('小节不存在', 'error')
        return redirect(url_for('teacher.dashboard'))

    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    if not chapter:
        flash('章节不存在', 'error')
        return redirect(url_for('teacher.dashboard'))

    course = db.find_by_id('courses', chapter['course_id'])
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))

    chapters = db.find_all('chapters', {'course_id': course['id']})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))

    for c in chapters:
        c['lessons'] = db.find_all('lessons', {'chapter_id': c['id']})
        c['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))

        for l in c['lessons']:
            progress = db.find_by_field('learning_progress', 'user_id', current_user.id)
            progress = [p for p in progress if int(p.get('lesson_id', 0)) == l['id']]
            l['completed'] = len(progress) > 0 and progress[0].get('status') == 'completed'

    discussions = db.find_all('discussions', {'lesson_id': lesson_id})

    total_lessons = sum(len(c['lessons']) for c in chapters)
    completed_lessons = sum(len([l for l in c['lessons'] if l.get('completed')]) for c in chapters)

    all_lessons = []
    for c in chapters:
        all_lessons.extend(c['lessons'])

    all_lessons.sort(key=lambda x: int(x.get('order_index', 0)))

    prev_lesson = None
    next_lesson = None

    current_index = -1
    for i, l in enumerate(all_lessons):
        if l['id'] == lesson['id']:
            current_index = i
            break

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
                         next_lesson=next_lesson,
                         is_preview_mode=True)

@teacher_bp.route('/courses/<int:course_id>/edit')
@login_required
def course_edit(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # 获取章节和小节
    chapters = db.find_all('chapters', {'course_id': course_id})
    chapters.sort(key=lambda x: int(x.get('order_index', 0)))
    
    for chapter in chapters:
        chapter['lessons'] = db.find_all('lessons', {'chapter_id': chapter['id']})
        chapter['lessons'].sort(key=lambda x: int(x.get('order_index', 0)))
    
    return render_template('teacher/course_edit.html', course=course, chapters=chapters)

@teacher_bp.route('/lessons/<int:lesson_id>/content')
@login_required
def get_lesson_content(lesson_id):
    if current_user.role != 'teacher':
        return {'success': False, 'error': '权限不足'}, 403
    
    from flask import current_app, jsonify
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        return jsonify({'success': False, 'error': '小节不存在'})
    
    return jsonify({'success': True, 'lesson': lesson})

@teacher_bp.route('/lessons/<int:lesson_id>/save', methods=['POST'])
@login_required
def save_lesson_content(lesson_id):
    if current_user.role != 'teacher':
        return {'success': False, 'error': '权限不足'}, 403
    
    from flask import current_app, jsonify, request
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        return jsonify({'success': False, 'error': '小节不存在'})
    
    # 支持JSON和FormData两种格式
    if request.is_json:
        data = request.get_json()
        title = data.get('title', lesson.get('title'))
        description = data.get('description', lesson.get('description', ''))
        content = data.get('content', lesson.get('content', ''))
        media_files = data.get('media_files', '[]')
    else:
        title = request.form.get('title', lesson.get('title'))
        description = request.form.get('description', lesson.get('description', ''))
        content = request.form.get('content', lesson.get('content', ''))
        media_files = request.form.get('media_files', '[]')
    
    print(f'[DEBUG] 保存小节 {lesson_id}')
    print(f'[DEBUG] 标题: {title}')
    print(f'[DEBUG] 内容长度: {len(content) if content else 0}')
    print(f'[DEBUG] 多媒体文件数: {len(media_files) if media_files else 0}')
    
    lesson_data = {
        'title': title,
        'description': description,
        'content': content,
        'media_files': media_files
    }
    
    success = db.update('lessons', lesson_id, lesson_data)
    
    print(f'[DEBUG] 更新结果: {success}')
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '数据库更新失败'})

@teacher_bp.route('/lessons/<int:lesson_id>/update-title', methods=['POST'])
@login_required
def update_lesson_title(lesson_id):
    if current_user.role != 'teacher':
        return {'success': False, 'error': '权限不足'}, 403
    
    from flask import current_app, jsonify
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    
    if not lesson:
        return jsonify({'success': False, 'error': '小节不存在'})
    
    title = request.form.get('title')
    
    if title:
        success = db.update('lessons', lesson_id, {'title': title})
        return jsonify({'success': success})
    
    return jsonify({'success': False, 'error': '标题不能为空'})

@teacher_bp.route('/upload-editor-image', methods=['POST'])
@login_required
def upload_editor_image():
    if current_user.role != 'teacher':
        return {'error': '权限不足'}, 403
    
    from flask import current_app, jsonify
    import os
    
    if 'upload' not in request.files:
        return jsonify({'error': '没有上传文件'})
    
    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'error': '文件名包含非法字符'})
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': '不支持的图片格式，仅支持 PNG、JPG、GIF、WEBP 格式'})
    
    filename = f"editor_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    folder = 'images'
    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
    url = f"/uploads/{folder}/{filename}"
    return jsonify({'url': url, 'uploaded': True})

@teacher_bp.route('/upload-video', methods=['POST'])
@login_required
def upload_video():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    from flask import current_app, jsonify
    import os
    
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': '没有上传文件'})
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'success': False, 'error': '文件名包含非法字符'})
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
        return jsonify({'success': False, 'error': '不支持的视频格式'})
    
    filename = f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    folder = 'videos'
    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
    url = f"/uploads/{folder}/{filename}"
    return jsonify({'success': True, 'url': url, 'filename': filename})

@teacher_bp.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    from flask import current_app, jsonify
    import os
    
    if 'document' not in request.files:
        return jsonify({'success': False, 'error': '没有上传文件'})
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'success': False, 'error': '文件名包含非法字符'})
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return jsonify({'success': False, 'error': '不支持的文档格式'})
    
    filename = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    folder = 'documents'
    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
    url = f"/uploads/{folder}/{filename}"
    return jsonify({'success': True, 'url': url, 'filename': filename})

@teacher_bp.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    from flask import current_app, jsonify
    import os
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'success': False, 'error': '文件名包含非法字符'})
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
    video_extensions = ['mp4', 'webm', 'ogg', 'avi', 'mov']
    pdf_extensions = ['pdf']
    document_extensions = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md']
    
    if file_ext in image_extensions:
        folder = 'images'
        file_type = 'image'
    elif file_ext in video_extensions:
        folder = 'videos'
        file_type = 'video'
    elif file_ext in pdf_extensions:
        folder = 'documents'
        file_type = 'pdf'
    elif file_ext in document_extensions:
        folder = 'documents'
        file_type = 'document'
    else:
        folder = 'documents'
        file_type = 'other'
    
    max_size = 50 * 1024 * 1024
    file_content = file.read()
    if len(file_content) > max_size:
        return jsonify({'success': False, 'error': '文件大小超过限制(50MB)'})
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(save_path, exist_ok=True)
    
    with open(os.path.join(save_path, unique_filename), 'wb') as f:
        f.write(file_content)
    
    url = f"/uploads/{folder}/{unique_filename}"
    
    return jsonify({
        'success': True,
        'url': url,
        'filename': filename,
        'file_type': file_type,
        'message': '文件上传成功'
    })

@teacher_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    
    if request.method == 'POST':
        try:
            print(f'[DEBUG] 开始创建课程，用户ID: {current_user.id}')
            
            title = request.form.get('title')
            description = request.form.get('description')
            category = request.form.get('category', '')
            duration = request.form.get('duration', '')
            difficulty = request.form.get('difficulty', '')
            cover = request.files.get('cover_image')
            
            print(f'[DEBUG] 课程信息: title={title}, category={category}, difficulty={difficulty}')
            
            if not title or not description:
                flash('请填写完整的课程信息', 'error')
                return redirect(url_for('teacher.create_course'))
            
            cover_path = ''
            if cover and cover.filename:
                print(f'[DEBUG] 处理封面图片: {cover.filename}')
                
                filename = secure_filename(cover.filename)
                if not filename:
                    flash('文件名包含非法字符', 'error')
                    return redirect(url_for('teacher.create_course'))
                
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                    flash('不支持的图片格式，仅支持 PNG、JPG、GIF、WEBP 格式', 'error')
                    return redirect(url_for('teacher.create_course'))
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"course_{timestamp}_{filename}"
                
                covers_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers')
                os.makedirs(covers_dir, exist_ok=True)
                
                cover_path_full = os.path.join(covers_dir, filename)
                cover.save(cover_path_full)
                cover_path = f"/uploads/covers/{filename}"
                
                print(f'[DEBUG] 封面图片已保存: {cover_path}')
            
            course_data = {
                'title': title,
                'description': description,
                'category': category,
                'difficulty': difficulty,
                'teacher_id': current_user.id,
                'cover': cover_path
            }
            
            print(f'[DEBUG] 准备插入数据库: {course_data}')
            
            new_id = db.insert('courses', course_data)
            
            if new_id > 0:
                print(f'[OK] 课程创建成功，ID: {new_id}')
                flash('课程创建成功', 'success')
                return redirect(url_for('teacher.dashboard'))
            else:
                print(f'[ERR] 课程插入失败，返回ID: {new_id}')
                flash('课程创建失败，请稍后重试', 'error')
                return redirect(url_for('teacher.create_course'))
                
        except Exception as e:
            print(f'[ERR] 创建课程时发生异常: {str(e)}')
            import traceback
            traceback.print_exc()
            flash(f'创建课程时发生错误: {str(e)}', 'error')
            return redirect(url_for('teacher.create_course'))
    
    return render_template('teacher/create_course.html')

@teacher_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # 删除所有相关章节
    chapters = db.find_all('chapters', {'course_id': course_id})
    for chapter in chapters:
        # 删除章节下的所有小节
        lessons = db.find_all('lessons', {'chapter_id': chapter['id']})
        for lesson in lessons:
            db.delete('lessons', lesson['id'])
        db.delete('chapters', chapter['id'])
    
    # 删除所有相关资料
    materials = db.find_all('materials', {'course_id': course_id})
    for material in materials:
        db.delete('materials', material['id'])
    
    # 删除课程本身
    db.delete('courses', course_id)
    
    flash('课程删除成功', 'success')
    return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/courses/<int:course_id>/chapters/create', methods=['POST'])
@login_required
def create_chapter(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    title = request.form.get('title')
    
    existing_chapters = db.find_all('chapters', {'course_id': course_id})
    order_index = len(existing_chapters) + 1
    
    chapter_data = {
        'course_id': course_id,
        'title': title,
        'order_index': order_index
    }
    
    db.insert('chapters', chapter_data)
    flash('章节创建成功', 'success')
    return redirect(url_for('teacher.course_detail', course_id=course_id))

@teacher_bp.route('/chapters/<int:chapter_id>/lessons/create', methods=['POST'])
@login_required
def create_lesson(chapter_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    chapter = db.find_by_id('chapters', chapter_id)
    course = db.find_by_id('courses', chapter['course_id'])
    
    if int(course['teacher_id']) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    content_type = request.form.get('content_type', 'text')
    duration = request.form.get('duration', '')
    
    content_path = ''
    content = ''
    
    if content_type == 'text':
        content = request.form.get('content_text', '')
    elif content_type == 'video':
        content_file = request.files.get('content_video')
        if content_file and content_file.filename:
            filename = secure_filename(content_file.filename)
            if not filename:
                flash('文件名包含非法字符', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
                flash('不支持的视频格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            filename = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            folder = 'videos'
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
            content_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
            content_path = f"uploads/{folder}/{filename}"
    elif content_type == 'image':
        content_file = request.files.get('content_image')
        if content_file and content_file.filename:
            filename = secure_filename(content_file.filename)
            if not filename:
                flash('文件名包含非法字符', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                flash('不支持的图片格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            filename = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            folder = 'images'
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
            content_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
            content_path = f"uploads/{folder}/{filename}"
    elif content_type == 'document':
        content_file = request.files.get('content_document')
        if content_file and content_file.filename:
            filename = secure_filename(content_file.filename)
            if not filename:
                flash('文件名包含非法字符', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
                flash('不支持的文档格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            
            filename = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            folder = 'documents'
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
            content_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
            content_path = f"uploads/{folder}/{filename}"
    
    existing_lessons = db.find_all('lessons', {'chapter_id': chapter_id})
    order_index = len(existing_lessons) + 1
    
    lesson_data = {
        'chapter_id': chapter_id,
        'title': title,
        'description': description,
        'content': content,
        'content_type': content_type,
        'content_path': content_path,
        'duration': duration,
        'order_index': order_index
    }
    
    db.insert('lessons', lesson_data)
    flash('小节创建成功', 'success')
    return redirect(url_for('teacher.course_detail', course_id=chapter['course_id']))

@teacher_bp.route('/chapters/<int:chapter_id>/edit', methods=['POST'])
@login_required
def edit_chapter(chapter_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    chapter = db.find_by_id('chapters', chapter_id)
    course = db.find_by_id('courses', chapter['course_id'])
    
    if int(course['teacher_id']) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    title = request.form.get('title')
    
    db.update('chapters', chapter_id, {'title': title})
    flash('章节更新成功', 'success')
    return redirect(url_for('teacher.course_detail', course_id=chapter['course_id']))

@teacher_bp.route('/chapters/<int:chapter_id>/delete', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    chapter = db.find_by_id('chapters', chapter_id)
    course = db.find_by_id('courses', chapter['course_id'])
    
    if int(course['teacher_id']) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # 删除章节下的所有小节
    lessons = db.find_all('lessons', {'chapter_id': chapter_id})
    for lesson in lessons:
        db.delete('lessons', lesson['id'])
    
    db.delete('chapters', chapter_id)
    flash('章节已删除', 'success')
    return redirect(url_for('teacher.course_detail', course_id=chapter['course_id']))

@teacher_bp.route('/lessons/<int:lesson_id>/edit', methods=['POST'])
@login_required
def edit_lesson(lesson_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    course = db.find_by_id('courses', chapter['course_id'])
    
    if int(course['teacher_id']) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    content_type = request.form.get('content_type_edit', lesson.get('content_type', 'text'))
    duration = request.form.get('duration', '')
    content = request.form.get('content_edit', lesson.get('content', ''))
    content_path = lesson.get('content_path', '')
    
    content_file = request.files.get('content_file_edit')
    if content_file and content_file.filename:
        filename = secure_filename(content_file.filename)
        if not filename:
            flash('文件名包含非法字符', 'error')
            return redirect(url_for('teacher.course_detail', course_id=course['id']))
        
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if content_type == 'video':
            if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
                flash('不支持的视频格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            folder = 'videos'
        elif content_type == 'image':
            if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                flash('不支持的图片格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            folder = 'images'
        else:
            if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
                flash('不支持的文档格式', 'error')
                return redirect(url_for('teacher.course_detail', course_id=course['id']))
            folder = 'documents'
        
        if content_path:
            old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], content_path.replace('uploads/', ''))
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        filename = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
        content_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename))
        content_path = f"uploads/{folder}/{filename}"
    
    lesson_data = {
        'title': title,
        'description': description,
        'content': content,
        'content_type': content_type,
        'content_path': content_path,
        'duration': duration
    }
    
    db.update('lessons', lesson_id, lesson_data)
    flash('小节更新成功', 'success')
    return redirect(url_for('teacher.course_detail', course_id=chapter['course_id']))

@teacher_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
def delete_lesson(lesson_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    lesson = db.find_by_id('lessons', lesson_id)
    chapter = db.find_by_id('chapters', lesson['chapter_id'])
    course = db.find_by_id('courses', chapter['course_id'])
    
    if int(course['teacher_id']) != current_user.id:
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    db.delete('lessons', lesson_id)
    flash('小节已删除', 'success')
    return redirect(url_for('teacher.course_detail', course_id=chapter['course_id']))

@teacher_bp.route('/courses/<int:course_id>/publish', methods=['POST'])
@login_required
def publish_course(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    db.update('courses', course_id, {'status': 'published'})
    flash('课程已发布', 'success')
    return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/courses/<int:course_id>/unpublish', methods=['POST'])
@login_required
def unpublish_course(course_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course or int(course['teacher_id']) != current_user.id:
        flash('课程不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    db.update('courses', course_id, {'status': 'draft'})
    flash('课程已取消发布', 'success')
    return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/assignments')
@login_required
def assignments():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, TeacherAssignment, ProblemCategory
    db = current_app.db
    
    category_id = request.args.get('category_id', type=int)
    
    categories = ProblemCategory.get_all()
    main_categories = [c for c in categories if c.parent_id is None]
    
    for main_cat in main_categories:
        main_cat.subcategories = [c for c in categories if c.parent_id == main_cat.id]
    
    if category_id:
        problem_list = Problem.get_by_category(category_id)
    else:
        problem_list = Problem.get_all()
    
    assignments = TeacherAssignment.get_by_teacher(current_user.id)
    
    return render_template('teacher/assignments.html', 
                         categories=main_categories, 
                         problems=problem_list, 
                         current_category_id=category_id,
                         assignments=assignments)

@teacher_bp.route('/assignments/create', methods=['POST'])
@login_required
def create_assignment():
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import TeacherAssignment
    db = current_app.db
    
    problem_id = request.form.get('problem_id', type=int)
    title = request.form.get('title')
    description = request.form.get('description')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not problem_id:
        flash('请选择题目', 'error')
        return redirect(url_for('teacher.assignments'))
    
    problem = db.find_by_id('problems', problem_id)
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('teacher.assignments'))
    
    assignment = TeacherAssignment(
        teacher_id=current_user.id,
        problem_id=problem_id,
        title=title or problem['title'],
        description=description or problem['description'],
        start_time=start_time,
        end_time=end_time
    )
    assignment.save()
    
    flash('题目布置成功', 'success')
    return redirect(url_for('teacher.assignments'))

@teacher_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import TeacherAssignment
    db = current_app.db
    
    assignment = TeacherAssignment.get_by_id(assignment_id)
    
    if not assignment or assignment.teacher_id != current_user.id:
        flash('布置不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.assignments'))
    
    assignment.delete()
    flash('布置已删除', 'success')
    return redirect(url_for('teacher.assignments'))

@teacher_bp.route('/assignments/batch_create', methods=['POST'])
@login_required
def batch_create_assignment():
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import TeacherAssignment
    db = current_app.db
    
    problem_ids_str = request.form.get('problem_ids')
    title = request.form.get('title')
    description = request.form.get('description')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not problem_ids_str:
        flash('请选择题目', 'error')
        return redirect(url_for('teacher.assignments'))
    
    problem_ids = [int(id) for id in problem_ids_str.split(',')]
    
    for problem_id in problem_ids:
        problem = db.find_by_id('problems', problem_id)
        if not problem:
            flash(f'题目ID {problem_id} 不存在', 'error')
            continue
        
        assignment = TeacherAssignment(
            teacher_id=current_user.id,
            problem_id=problem_id,
            title=title or problem['title'],
            description=description or problem['description'],
            start_time=start_time,
            end_time=end_time
        )
        assignment.save()
    
    flash(f'成功布置 {len(problem_ids)} 个题目', 'success')
    return redirect(url_for('teacher.assignments'))

@teacher_bp.route('/add-exercise')
@login_required
def add_exercise():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import ProblemCategory, Problem
    db = current_app.db
    
    category_id = request.args.get('category_id', type=int)
    
    categories = ProblemCategory.get_all()
    main_categories = [c for c in categories if c.parent_id is None]
    
    for main_cat in main_categories:
        main_cat.subcategories = [c for c in categories if c.parent_id == main_cat.id]
    
    if category_id:
        problem_list = Problem.get_by_category(category_id)
    else:
        problem_list = Problem.get_all()
    
    return render_template('teacher/assignments.html', 
                         categories=main_categories, 
                         problems=problem_list, 
                         current_category_id=category_id)

@teacher_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import jsonify
    
    if request.method == 'POST':
        db = current_app.db
        
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            if filename:
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if file_ext in ALLOWED_IMAGE_EXTENSIONS:
                    filename = f"avatar_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
                    avatar_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', filename))
                    avatar_path = f"/uploads/avatars/{filename}"
                    db.update('users', current_user.id, {'avatar': avatar_path})
        
        nickname = request.form.get('nickname', '')
        email = request.form.get('email', '')
        bio = request.form.get('bio', '')
        
        update_data = {}
        if nickname:
            update_data['nickname'] = nickname
        if email:
            update_data['email'] = email
        if bio:
            update_data['bio'] = bio
        
        if update_data:
            db.update('users', current_user.id, update_data)
        
        flash('设置保存成功', 'success')
        return redirect(url_for('teacher.settings'))
    
    return render_template('teacher/settings.html')

@teacher_bp.route('/problems')
@login_required
def problem_bank():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, ProblemCategory, TeacherSelectedProblem
    from app.utils import get_difficulty_label, get_difficulty_icon
    db = current_app.db
    
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty')
    source = request.args.get('source')
    search = request.args.get('search', '')
    jaundice = request.args.get('jaundice')
    chapter = request.args.get('chapter')
    bank_source = request.args.get('bank_source')
    station = request.args.get('station')
    
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
    
    selected_problems = TeacherSelectedProblem.get_by_teacher(current_user.id)
    selected_ids = [sp.problem_id for sp in selected_problems]
    
    for problem in problem_list:
        problem.is_selected = problem.id in selected_ids
    
    return render_template('teacher/problem_bank.html',
                          categories=main_categories,
                          problems=problem_list,
                          current_category_id=category_id,
                          current_difficulty=difficulty,
                          current_source=source,
                          current_search=search,
                          current_jaundice=jaundice,
                          current_chapter=chapter,
                          current_bank_source=bank_source,
                          current_station=station,
                          sources=list(sources),
                          get_difficulty_label=get_difficulty_label,
                          get_difficulty_icon=get_difficulty_icon)

@teacher_bp.route('/problems/<int:problem_id>')
@login_required
def problem_detail(problem_id):
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, TeacherSelectedProblem
    from app.utils import get_difficulty_label, get_difficulty_icon
    db = current_app.db
    
    problem = Problem.get_by_id(problem_id)
    
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('teacher.problem_bank'))
    
    selected = TeacherSelectedProblem.get_by_teacher_and_problem(current_user.id, problem_id)
    
    return render_template('teacher/problem_detail.html',
                          problem=problem,
                          is_selected=selected is not None,
                          selected_info=selected,
                          get_difficulty_label=get_difficulty_label,
                          get_difficulty_icon=get_difficulty_icon)

@teacher_bp.route('/problems/<int:problem_id>/select', methods=['POST'])
@login_required
def select_problem(problem_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, TeacherSelectedProblem
    db = current_app.db
    
    problem = Problem.get_by_id(problem_id)
    if not problem:
        flash('题目不存在', 'error')
        return redirect(url_for('teacher.problem_bank'))
    
    existing = TeacherSelectedProblem.get_by_teacher_and_problem(current_user.id, problem_id)
    if existing:
        flash('该题目已在您的选题列表中', 'warning')
        return redirect(url_for('teacher.problem_bank'))
    
    visible_start = request.form.get('visible_start')
    visible_end = request.form.get('visible_end')
    notes = request.form.get('notes')
    
    selected = TeacherSelectedProblem(
        teacher_id=current_user.id,
        problem_id=problem_id,
        visible_start=visible_start,
        visible_end=visible_end,
        notes=notes
    )
    selected.save()
    
    flash('题目已添加到您的选题列表', 'success')
    return redirect(url_for('teacher.problem_bank'))

@teacher_bp.route('/problems/<int:problem_id>/unselect', methods=['POST'])
@login_required
def unselect_problem(problem_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('student.dashboard'))
    
    from app.models import TeacherSelectedProblem
    
    selected = TeacherSelectedProblem.get_by_teacher_and_problem(current_user.id, problem_id)
    if not selected:
        flash('该题目不在您的选题列表中', 'warning')
        return redirect(url_for('teacher.selected_problems'))
    
    selected.delete()
    flash('已取消选择该题目', 'success')
    return redirect(url_for('teacher.selected_problems'))

@teacher_bp.route('/problems/selected')
@login_required
def selected_problems():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    
    from flask import current_app
    from app.models import Problem, TeacherSelectedProblem
    from app.utils import get_difficulty_label, get_difficulty_icon
    db = current_app.db
    
    selected_list = TeacherSelectedProblem.get_by_teacher(current_user.id)
    
    for selected in selected_list:
        selected.problem = Problem.get_by_id(selected.problem_id)
    
    return render_template('teacher/selected_problems.html',
                          selected_list=selected_list,
                          get_difficulty_label=get_difficulty_label,
                          get_difficulty_icon=get_difficulty_icon)

@teacher_bp.route('/problems/selected/<int:selected_id>/edit', methods=['POST'])
@login_required
def edit_selected_problem(selected_id):
    if current_user.role != 'teacher':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('teacher.selected_problems'))
    
    from app.models import TeacherSelectedProblem
    
    selected = TeacherSelectedProblem.get_by_id(selected_id)
    
    if not selected or selected.teacher_id != current_user.id:
        flash('选题记录不存在或您没有权限操作', 'error')
        return redirect(url_for('teacher.selected_problems'))
    
    selected.visible_start = request.form.get('visible_start')
    selected.visible_end = request.form.get('visible_end')
    selected.notes = request.form.get('notes')
    selected.save()
    
    flash('选题设置已更新', 'success')
    return redirect(url_for('teacher.selected_problems'))
