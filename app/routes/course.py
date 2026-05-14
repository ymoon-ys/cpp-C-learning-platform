from flask import Blueprint, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

course_bp = Blueprint('course', __name__, url_prefix='/course')

ALLOWED_MATERIAL_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}

@course_bp.route('/<int:course_id>/materials/upload', methods=['POST'])
@login_required
def upload_material(course_id):
    from flask import current_app
    db = current_app.db
    course = db.find_by_id('courses', course_id)
    
    if not course:
        flash('课程不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    if current_user.role != 'teacher' or int(course['teacher_id']) != current_user.id:
        flash('您没有权限上传资料', 'error')
        return redirect(url_for('student.dashboard'))
    
    title = request.form.get('title')
    material_file = request.files.get('material_file')
    
    if not material_file or not material_file.filename:
        flash('请选择要上传的文件', 'error')
        return redirect(url_for('student.dashboard'))
    
    filename = secure_filename(material_file.filename)
    if not filename:
        flash('文件名包含非法字符', 'error')
        return redirect(url_for('student.dashboard'))
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext not in ALLOWED_MATERIAL_EXTENSIONS:
        flash('不支持的文件类型', 'error')
        return redirect(url_for('student.dashboard'))
    
    filename = f"material_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    
    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials'), exist_ok=True)
    material_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials', filename))
    
    material_data = {
        'course_id': course_id,
        'title': title,
        'file_url': f"uploads/materials/{filename}",
        'type': file_ext,
        'uploader_id': current_user.id
    }
    
    db.insert('materials', material_data)
    flash('资料上传成功', 'success')
    return redirect(url_for('student.dashboard'))

@course_bp.route('/materials/<int:material_id>/download')
@login_required
def download_material(material_id):
    from flask import current_app
    from werkzeug.utils import secure_filename
    db = current_app.db
    material = db.find_by_id('materials', material_id)
    
    if not material:
        flash('资料不存在', 'error')
        return redirect(url_for('student.dashboard'))
    
    file_url = material['file_url']
    safe_filename = secure_filename(file_url.split('/')[-1])
    if not safe_filename:
        flash('无效的文件名', 'error')
        return redirect(url_for('student.dashboard'))
    
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file_url, as_attachment=True, download_name=safe_filename)
