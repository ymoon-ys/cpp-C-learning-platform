# C++ 学习平台 - 项目架构文档

> 本文档为 AI 辅助开发提供项目全局视角，阅读本文档后应能理解项目架构、开发规范和常见开发场景。

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈概览](#2-技术栈概览)
3. [目录结构](#3-目录结构)
4. [核心架构设计](#4-核心架构设计)
5. [开发规范](#5-开发规范)
6. [常见开发场景指南](#6-常见开发场景指南)
7. [数据库设计](#7-数据库设计)
8. [技术债与注意事项](#8-技术债与注意事项)
9. [快速参考](#9-快速参考)

---

## 1. 项目概述

### 1.1 项目简介

这是一个基于 Flask 的 C++ 在线学习平台，采用传统服务端渲染（SSR）模式，集成了课程管理、在线编程评测、社区交流和 AI 助手等功能。

### 1.2 核心功能模块

| 模块 | 功能描述 | 用户角色 |
|------|---------|---------|
| 用户认证 | 登录、注册、角色管理 | 全部 |
| 课程学习 | 视频课程、文档资料、学习进度 | 学生 |
| 在线编程 | C++ 代码提交、自动评测 | 学生 |
| 题库管理 | 题目增删改查、批量导入 | 管理员 |
| 作业系统 | 教师选题、学生提交 | 教师、学生 |
| 社区交流 | 帖子、评论、点赞 | 学生 |
| AI 助手 | 智能问答、代码解释 | 学生 |

### 1.3 用户角色

```
├── admin    - 管理员：用户管理、课程管理、题库管理
├── teacher  - 教师：创建课程、布置作业、管理学生
└── student  - 学生：学习课程、提交作业、参与社区
```

---

## 2. 技术栈概览

### 2.1 后端技术

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | Flask | 3.1.3 | 核心框架 |
| 数据库 | MySQL | 5.7+ | 数据存储 |
| 数据库驱动 | mysql-connector-python | 8.4.0 | 数据库连接 |
| 用户认证 | Flask-Login | 0.6.3 | 会话管理 |
| 表单验证 | Flask-WTF | 1.1.1 | 表单处理 |
| 缓存 | Flask-Caching | 2.1.0 | 数据缓存 |
| 限流 | Flask-Limiter | 3.5.0 | 请求限流 |
| 数据处理 | pandas | 2.0.3 | Excel 导入 |
| 密码加密 | Werkzeug | 3.1.3 | 密码哈希 |

### 2.2 前端技术

| 类别 | 技术 | 引入方式 |
|------|------|---------|
| CSS 框架 | Bootstrap 5.1.3 | CDN |
| 图标库 | Font Awesome 6.0.0 | CDN |
| 模板引擎 | Jinja2 | Flask 内置 |
| 原生技术 | HTML5 + CSS3 + JavaScript | - |

### 2.3 AI 集成

支持三种 AI 模型 API：
- Google Gemini
- OpenAI ChatGPT
- Deepseek

### 2.4 开发环境

- Python 3.8+
- MySQL 5.7+
- g++ 编译器（用于代码评测）
- 运行端口：5001

---

## 3. 目录结构

```
C-learning-platform/
│
├── app/                              # 主应用目录
│   ├── __init__.py                   # 应用工厂函数 create_app()
│   ├── config.py                     # 配置类（开发/生产/测试）
│   ├── models.py                     # 数据模型层（User, Problem, Submission 等）
│   ├── mysql_database.py             # 自定义 MySQL 数据库操作类
│   ├── utils.py                      # 通用工具函数
│   ├── cache_utils.py                # 缓存相关工具
│   ├── exceptions.py                 # 自定义业务异常类
│   ├── recommendation.py             # 学习推荐算法
│   │
│   ├── forms/                        # 表单定义层
│   │   ├── __init__.py
│   │   └── forms.py                  # WTForms 表单类
│   │
│   ├── routes/                       # 路由控制器层
│   │   ├── __init__.py
│   │   ├── auth.py                   # 认证路由（/auth）
│   │   ├── admin.py                  # 管理员路由（/admin）
│   │   ├── teacher.py                # 教师路由（/teacher）
│   │   ├── student.py                # 学生路由（/student）
│   │   ├── course.py                 # 课程路由（/course）
│   │   ├── community.py              # 社区路由（/community）
│   │   ├── ai_assistant.py           # AI 助手路由（/ai）
│   │   └── recommendation.py         # 学习推荐路由（/recommendation）
│   │
│   ├── services/                     # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py           # 认证服务
│   │   ├── learning_progress_service.py  # 学习进度服务
│   │   └── user_service.py           # 用户服务
│   │
│   └── templates/                    # Jinja2 模板层
│       ├── base.html                 # 基础布局模板
│       ├── community.html
│       ├── post_detail.html
│       ├── ai_assistant.html
│       ├── recommendations.html
│       ├── auth/                     # 认证页面
│       │   ├── login.html
│       │   └── register.html
│       ├── admin/                    # 管理员页面
│       │   ├── dashboard.html
│       │   ├── users.html
│       │   ├── courses.html
│       │   └── problems.html
│       ├── teacher/                  # 教师页面
│       │   ├── dashboard.html
│       │   ├── course_detail.html
│       │   └── problem_bank.html
│       ├── student/                  # 学生页面
│       │   ├── dashboard.html
│       │   ├── course_detail.html
│       │   ├── lesson_detail.html
│       │   ├── practice.html
│       │   └── problem_detail.html
│       └── errors/                   # 错误页面
│           ├── 404.html
│           └── 500.html
│
├── static/                           # 静态资源目录
│   ├── style.css                     # 全局样式（约 5700 行）
│   └── script.js                     # 全局脚本（约 1250 行）
│
├── uploads/                          # 文件上传目录
│   ├── covers/                       # 课程封面
│   ├── videos/                       # 视频文件
│   ├── images/                       # 图片文件
│   ├── documents/                    # 文档文件
│   ├── materials/                    # 课程资料
│   └── community/                    # 社区图片
│
├── run.py                            # 应用入口文件
├── requirements.txt                  # Python 依赖
├── requirements-dev.txt              # 开发依赖
├── .env.example                      # 环境变量示例
└── PROJECT_ARCHITECTURE.md           # 本文档
```

---

## 4. 核心架构设计

### 4.1 架构模式

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端（浏览器）                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask 应用（服务端渲染）                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Routes（路由层）                       │   │
│  │  auth_bp │ admin_bp │ teacher_bp │ student_bp │ ...     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Services（服务层）                      │   │
│  │  AuthService │ UserService │ LearningProgressService    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Models（模型层）                       │   │
│  │  User │ Problem │ Submission │ LearningProgress │ ...   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               MySQLDatabase（数据访问层）                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MySQL 数据库                             │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 请求处理流程

```
HTTP 请求
    │
    ▼
Flask 路由匹配（Blueprint）
    │
    ▼
@login_required 装饰器（认证检查）
    │
    ▼
路由函数处理
    │
    ├──▶ 调用 Service 层（业务逻辑）
    │        │
    │        ▼
    │    调用 Model 层（数据操作）
    │        │
    │        ▼
    │    MySQLDatabase 执行 SQL
    │
    ▼
返回响应
    │
    ├──▶ render_template() → HTML 页面
    ├──▶ redirect() → 重定向
    └──▶ jsonify() → JSON 数据
```

### 4.3 路由蓝图注册

```python
# app/__init__.py

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.teacher import teacher_bp
from app.routes.student import student_bp
from app.routes.course import course_bp
from app.routes.ai_assistant import ai_bp
from app.routes.community import community_bp
from app.routes.recommendation import recommendation_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(course_bp, url_prefix='/course')
app.register_blueprint(ai_bp, url_prefix='/ai')
app.register_blueprint(community_bp, url_prefix='/community')
app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
```

### 4.4 认证机制

```python
# 使用 Flask-Login 的 Session 机制
from flask_login import LoginManager, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# 在模板中访问当前用户
{{ current_user.username }}
{{ current_user.role }}
{% if current_user.is_authenticated %}
```

---

## 5. 开发规范

### 5.1 添加新页面

#### 步骤 1：创建模板文件

```html
<!-- app/templates/student/new_page.html -->
{% extends "base.html" %}

{% block title %}新页面 - C++学习平台{% endblock %}

{% block content %}
<div class="container">
    <h1>新页面标题</h1>
    <!-- 页面内容 -->
</div>
{% endblock %}

{% block scripts %}
<script>
    // 页面专属脚本
</script>
{% endblock %}
```

#### 步骤 2：添加路由

```python
# app/routes/student.py

@student_bp.route('/new-page')
@login_required
def new_page():
    db = current_app.db
    data = db.read_table('some_table')
    return render_template('student/new_page.html', data=data)
```

#### 步骤 3：添加导航链接

```html
<!-- app/templates/student/dashboard.html 或 base.html -->
<li><a href="{{ url_for('student.new_page') }}">新页面</a></li>
```

### 5.2 添加新 API 接口

```python
# app/routes/api.py（如需创建新的 API 蓝图）

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/data', methods=['GET'])
@login_required
def get_data():
    """获取数据 API"""
    try:
        db = current_app.db
        data = db.read_table('some_table')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data', methods=['POST'])
@login_required
def create_data():
    """创建数据 API"""
    data = request.get_json()
    # 处理逻辑
    return jsonify({'success': True, 'id': new_id})
```

### 5.3 添加新数据模型

```python
# app/models.py

class NewModel(BaseModel):
    table_name = 'new_table'
    
    def __init__(self, id=None, name=None, description=None, created_at=None):
        super().__init__(id)
        self.name = name
        self.description = description
        self.created_at = created_at
    
    def _to_dict(self):
        return {
            'name': self.name,
            'description': self.description
        }
    
    @classmethod
    def _from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            created_at=data.get('created_at')
        )
    
    @staticmethod
    def get_by_name(name):
        from flask import current_app
        db = current_app.db
        data = db.find_by_field('new_table', 'name', name)
        return [NewModel._from_dict(item) for item in data]
```

### 5.4 添加表单验证

```python
# app/forms/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class NewForm(FlaskForm):
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(min=2, max=100, message='标题长度应在2-100个字符之间')
    ])
    content = TextAreaField('内容', validators=[
        Optional(),
        Length(max=5000, message='内容长度不能超过5000个字符')
    ])
    category = SelectField('分类', choices=[
        ('type1', '类型1'),
        ('type2', '类型2')
    ], validators=[DataRequired(message='请选择分类')])
```

### 5.5 添加服务层方法

```python
# app/services/new_service.py

from typing import List, Optional
from flask import current_app
from app.models import NewModel
from app.exceptions import ValidationError, NotFoundError

class NewService:
    """新功能服务类"""
    
    @staticmethod
    def create(name: str, description: str) -> NewModel:
        """创建新记录"""
        if not name:
            raise ValidationError("名称不能为空")
        
        model = NewModel(name=name, description=description)
        return model.save()
    
    @staticmethod
    def get_by_id(record_id: int) -> Optional[NewModel]:
        """根据 ID 获取记录"""
        record = NewModel.get_by_id(record_id)
        if not record:
            raise NotFoundError("记录不存在")
        return record
```

### 5.6 数据库操作规范

```python
# 使用 current_app.db 访问数据库
from flask import current_app

db = current_app.db

# 查询所有记录
records = db.read_table('table_name')

# 根据 ID 查询
record = db.find_by_id('table_name', record_id)

# 根据字段查询
records = db.find_by_field('table_name', 'field_name', value)

# 多条件查询
records = db.find_all('table_name', {'field1': value1, 'field2': value2})

# 插入记录
new_id = db.insert('table_name', {'name': 'value', 'description': 'value'})

# 更新记录
db.update('table_name', record_id, {'name': 'new_value'})

# 删除记录
db.delete('table_name', record_id)

# 统计记录数
count = db.count('table_name')
count = db.count('table_name', {'status': 'active'})
```

### 5.7 异常处理规范

```python
# 使用自定义异常
from app.exceptions import ValidationError, NotFoundError, AuthenticationError

# 在服务层抛出异常
if not user:
    raise AuthenticationError("用户名或密码错误")

# 在路由层捕获异常
try:
    user = AuthService.authenticate(username, password)
except AuthenticationError as e:
    flash(str(e), 'error')
    return redirect(url_for('auth.login'))
```

### 5.8 权限控制规范

```python
from flask_login import login_required, current_user
from flask import flash, redirect, url_for

# 方式 1：装饰器
@login_required
def protected_page():
    # 只有登录用户可访问
    pass

# 方式 2：角色检查
@admin_bp.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('student.dashboard'))
    # 管理员逻辑
    pass

# 方式 3：使用工具函数
from app.utils import check_role_and_redirect

def some_route():
    redirect_result = check_role_and_redirect('admin')
    if redirect_result:
        return redirect_result
    # 业务逻辑
    pass
```

---

## 6. 常见开发场景指南

### 6.1 场景：添加新的课程类型

```python
# 1. 修改数据库表结构（如需要）
# 在 mysql_database.py 的 create_tables() 中添加字段

# 2. 修改模型
# app/models.py - Course 类添加新字段

# 3. 修改表单
# app/forms/forms.py - CourseForm 添加新字段

# 4. 修改路由
# app/routes/teacher.py - 处理新字段

# 5. 修改模板
# app/templates/teacher/course_edit.html - 添加表单输入
```

### 6.2 场景：添加新的评测状态

```python
# 1. 修改 models.py 中的 evaluate_code() 函数
def evaluate_code(code: str, test_cases: list, time_limit: int = 1) -> dict:
    # 添加新的状态判断
    if some_condition:
        return {
            'status': 'NEW_STATUS',
            'message': '状态描述'
        }

# 2. 修改模板显示
<!-- app/templates/student/problem_detail.html -->
<div class="submission-item status-NEW_STATUS">
    <!-- 新状态样式 -->
</div>

# 3. 修改 CSS
/* static/style.css */
.submission-item.status-NEW_STATUS {
    border-left: 4px solid #color;
    background-color: #bgcolor;
}
```

### 6.3 场景：添加新的用户角色

```python
# 1. 修改数据库（users 表 role 字段）

# 2. 修改注册表单
# app/forms/forms.py
role = SelectField('角色', choices=[
    ('student', '学生'),
    ('teacher', '教师'),
    ('new_role', '新角色')  # 添加
])

# 3. 创建新蓝图
# app/routes/new_role.py

# 4. 注册蓝图
# app/__init__.py
from app.routes.new_role import new_role_bp
app.register_blueprint(new_role_bp, url_prefix='/new-role')

# 5. 修改登录重定向逻辑
# app/services/auth_service.py
def get_login_redirect_url(user: User) -> str:
    if user.role == 'admin':
        return url_for('admin.dashboard')
    elif user.role == 'teacher':
        return url_for('teacher.dashboard')
    elif user.role == 'new_role':  # 添加
        return url_for('new_role.dashboard')
    else:
        return url_for('student.dashboard')

# 6. 创建模板目录
# app/templates/new_role/
```

### 6.4 场景：添加文件上传功能

```python
# 路由处理
@teacher_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    from werkzeug.utils import secure_filename
    import os
    
    file = request.files.get('file')
    if not file:
        flash('请选择文件', 'error')
        return redirect(url_for('teacher.some_page'))
    
    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'subfolder')
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # 保存到数据库
    db.insert('files', {
        'filename': filename,
        'path': f'/uploads/subfolder/{filename}',
        'user_id': current_user.id
    })
    
    flash('文件上传成功', 'success')
    return redirect(url_for('teacher.some_page'))
```

### 6.5 场景：添加 AJAX 交互

```javascript
// static/script.js 或页面内脚本

async function likePost(postId) {
    try {
        const response = await fetch(`/community/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 更新 UI
            document.querySelector('.like-count').textContent = data.count;
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

```python
# 后端路由
@community_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    db = current_app.db
    
    # 检查是否已点赞
    existing = db.find_all('likes', {
        'user_id': current_user.id,
        'post_id': post_id
    })
    
    if existing:
        # 取消点赞
        db.delete('likes', existing[0]['id'])
        liked = False
    else:
        # 添加点赞
        db.insert('likes', {
            'user_id': current_user.id,
            'post_id': post_id
        })
        liked = True
    
    count = len(db.find_by_field('likes', 'post_id', post_id))
    
    return jsonify({
        'success': True,
        'liked': liked,
        'count': count
    })
```

---

## 7. 数据库设计

### 7.1 核心数据表

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `users` | 用户信息 | id, username, email, password_hash, role, nickname, avatar |
| `courses` | 课程信息 | id, title, description, teacher_id, category, cover |
| `chapters` | 章节信息 | id, course_id, title, order_index |
| `lessons` | 小节信息 | id, chapter_id, title, content, content_type, content_path |
| `learning_progress` | 学习进度 | id, user_id, course_id, lesson_id, progress, completed |
| `materials` | 课程资料 | id, course_id, title, file_path, file_type |
| `problems` | 题库 | id, title, description, difficulty, test_cases, time_limit |
| `submissions` | 代码提交 | id, user_id, problem_id, code, status, submit_time |
| `discussions` | 社区帖子 | id, user_id, title, content, images, created_at |
| `replies` | 帖子回复 | id, discussion_id, user_id, content, parent_id |
| `ai_conversations` | AI 对话 | id, user_id, question, answer, model_name |
| `teacher_assignments` | 教师作业 | id, teacher_id, problem_id, title, start_time, end_time |

### 7.2 数据库连接配置

```python
# 从环境变量读取
db = MySQLDatabase(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', '123456'),
    database=os.getenv('MYSQL_DATABASE', 'learning_platform')
)
```

### 7.3 重要说明

- 项目**不使用 ORM**，使用自定义的 `MySQLDatabase` 类
- 所有数据库操作通过 `current_app.db` 访问
- 模型类继承 `BaseModel`，封装 CRUD 操作

---

## 8. 技术债与注意事项

### 8.1 高优先级问题

#### ⚠️ 安全隐患：localStorage 存储密码

```javascript
// static/script.js 中存在明文密码存储
const savedPassword = localStorage.getItem('password') || '123456';
```

**建议**：移除此功能，依赖服务端 Session 管理。

#### ⚠️ 代码评测使用 subprocess

```python
# app/models.py
compile_result = subprocess.run(['g++', source_file_path, '-o', executable_path])
```

**风险**：
- 需要服务器安装 g++ 编译器
- 潜在的沙箱逃逸风险
- 建议使用 Docker 容器隔离

#### ⚠️ 自定义数据库类

- 没有 ORM 的便利性（关联查询、懒加载等）
- 需要手动处理事务
- SQL 注入风险（已使用参数化查询，但需注意）

### 8.2 中优先级问题

#### 硬编码的默认值

```python
# 默认用户密码
default_users = [
    {'username': 'admin', 'password_hash': generate_password_hash('admin123')}
]
```

**建议**：生产环境应通过环境变量或初始化脚本设置。

#### 前后端逻辑重复

前端 JS 中有独立的代码分析逻辑，与后端评测逻辑可能不一致。

#### 调试代码残留

```python
print(f'\n=== 上传文件调试 ===')
```

**建议**：使用 Python logging 模块替代 print。

### 8.3 低优先级问题

- 部分代码缺少类型注解
- 异常处理风格不统一
- 缺少单元测试

### 8.4 开发注意事项

1. **修改数据库结构**：需要同时更新 `mysql_database.py` 的 `create_tables()` 和相关模型类
2. **添加新路由**：记得在 `__init__.py` 中注册蓝图
3. **表单验证**：使用 WTForms，不要在前端单独验证
4. **权限控制**：所有需要登录的页面都要加 `@login_required`
5. **文件上传**：注意检查文件类型和大小限制

---

## 9. 快速参考

### 9.1 常用命令

```bash
# 启动开发服务器
python run.py

# 安装依赖
pip install -r requirements.txt

# 检查数据库连接
python check_db.py
```

### 9.2 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher | teacher123 |
| 学生 | student | student123 |

### 9.3 重要文件路径

| 用途 | 路径 |
|------|------|
| 应用入口 | `run.py` |
| 应用工厂 | `app/__init__.py` |
| 配置文件 | `app/config.py` |
| 数据模型 | `app/models.py` |
| 数据库操作 | `app/mysql_database.py` |
| 表单定义 | `app/forms/forms.py` |
| 全局样式 | `static/style.css` |
| 全局脚本 | `static/script.js` |
| 基础模板 | `app/templates/base.html` |

### 9.4 URL 前缀速查

| 蓝图 | URL 前缀 | 用途 |
|------|---------|------|
| auth_bp | `/auth` | 认证相关 |
| admin_bp | `/admin` | 管理员后台 |
| teacher_bp | `/teacher` | 教师工作台 |
| student_bp | `/student` | 学生学习 |
| course_bp | `/course` | 课程管理 |
| ai_bp | `/ai` | AI 助手 |
| community_bp | `/community` | 社区交流 |
| recommendation_bp | `/recommendation` | 学习推荐 |

### 9.5 模板变量

在所有模板中可用的全局变量：

```jinja2
{{ current_user }}          # 当前登录用户对象
{{ current_user.username }} # 用户名
{{ current_user.role }}     # 用户角色
{{ current_user.nickname }} # 用户昵称
{{ current_user.avatar }}   # 用户头像

{{ url_for('route_name') }} # 生成 URL
{{ flash_messages() }}      # 显示消息提示
```

### 9.6 环境变量

```env
# .env 文件配置
SECRET_KEY=your_secret_key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=learning_platform
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2024-03-24 | 1.0 | 初始版本 |

---

> 本文档由 AI 生成并维护，如有疑问请参考源代码或联系项目维护者。
