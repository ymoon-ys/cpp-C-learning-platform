from app import create_app

app = create_app()
with app.app_context():
    db = app.db
    
    print('=== 直接测试图片URL ===')
    
    courses = db.read_table('courses')
    for course in courses:
        print(f'\n课程: {course["title"]}')
        cover = course.get('cover')
        print(f'原始路径: {cover}')
        
        if cover:
            import os
            print(f'\n尝试几种可能的文件路径:')
            
            test1 = os.path.join(app.config['UPLOAD_FOLDER'], cover)
            print(f'1: {test1} -> {os.path.exists(test1)}')
            
            if cover.startswith('uploads/'):
                test2 = os.path.join(app.config['UPLOAD_FOLDER'], cover[8:])
                print(f'2: {test2} -> {os.path.exists(test2)}')
            
            print(f'\n建议的URL:')
            if cover.startswith('/'):
                print(f'URL: {cover}')
            elif cover.startswith('uploads/'):
                print(f'URL: /{cover}')
            else:
                print(f'URL: /uploads/{cover}')
