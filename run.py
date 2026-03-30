from app import create_app
from app.models import User
import os
from flask import send_from_directory, make_response

app = create_app()

@app.route('/')
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            from flask import redirect, url_for
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            from flask import redirect, url_for
            return redirect(url_for('teacher.dashboard'))
        else:
            from flask import redirect, url_for
            return redirect(url_for('student.dashboard'))
    else:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

@app.route('/static/<path:filename>')
def serve_static_with_cache(filename):
    response = make_response(send_from_directory(app.config['STATIC_FOLDER'], filename))
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'covers'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'materials'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'community'), exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
