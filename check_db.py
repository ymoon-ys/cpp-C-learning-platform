from app import create_app

app = create_app()
with app.app_context():
    db = app.db
    
    print('=== 课程数据 ===')
    courses = db.read_table('courses')
    for course in courses:
        print(f'课程ID: {course["id"]}, 标题: {course["title"]}, 封面: {course.get("cover", "")}')
    
    print('\n=== 小节数据 ===')
    lessons = db.read_table('lessons')
    for lesson in lessons[:5]:
        print(f'小节ID: {lesson["id"]}, 标题: {lesson["title"]}')
        content = lesson.get("content", "")
        if content:
            print(f'  content (前150字): {content[:150]}')
        print(f'  content_path: {lesson.get("content_path", "")}')
