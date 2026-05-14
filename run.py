from app import create_app
import os

app = create_app()


@app.route('/')
def index():
    from flask_login import current_user
    from flask import redirect, url_for

    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    else:
        return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
