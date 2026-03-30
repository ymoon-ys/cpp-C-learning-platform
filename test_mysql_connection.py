
from app import create_app

app = create_app()
app.app_context().push()

db = app.db

print('数据库连接成功！')

users = db.fetch_all('SELECT id, username, role FROM users')
print(f'当前用户数量: {len(users)}')
print('用户列表:')
for u in users:
    print(f'  ID: {u["id"]}, 用户名: {u["username"]}, 角色: {u["role"]}')
