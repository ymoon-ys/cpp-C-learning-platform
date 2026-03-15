from app import create_app

app = create_app()
with app.app_context():
    db = app.db
    
    print('=== 测试上传文件访问 ===')
    print(f'UPLOAD_FOLDER: {app.config["UPLOAD_FOLDER"]}')
    
    courses = db.read_table('courses')
    for course in courses:
        print(f'\n课程: {course["title"]}')
        cover = course.get('cover')
        print(f'封面路径: {cover}')
        
        if cover:
            from app.utils import ensure_url_path
            url_path = ensure_url_path(cover)
            print(f'处理后的URL: {url_path}')
            
            import os
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover.lstrip('/'))
            print(f'文件路径: {file_path}')
            print(f'文件存在: {os.path.exists(file_path)}')
