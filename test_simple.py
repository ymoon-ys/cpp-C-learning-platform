from app import create_app

app = create_app()

print('=== 直接测试图片访问 ===')
print(f'UPLOAD_FOLDER: {app.config["UPLOAD_FOLDER"]}')

with app.app_context():
    db = app.db
    
    courses = db.read_table('courses')
    for course in courses:
        print(f'\n课程: {course["title"]}')
        cover = course.get('cover')
        print(f'数据库路径: {cover}')
        
        if cover:
            import os
            print('\n尝试直接访问文件:')
            
            if cover.startswith('uploads/'):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover[8:])
            else:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover.lstrip('/'))
            
            print(f'文件路径: {file_path}')
            print(f'文件存在: {os.path.exists(file_path)}')
            
            if os.path.exists(file_path):
                print(f'文件大小: {os.path.getsize(file_path)} bytes')
                print('\n建议的URL:')
                if cover.startswith('/'):
                    print(f'URL: {cover}')
                elif cover.startswith('uploads/'):
                    print(f'URL: /{cover}')
                else:
                    print(f'URL: /uploads/{cover}')
