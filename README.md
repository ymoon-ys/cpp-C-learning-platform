# C++学习平台

基于Flask框架开发的C++在线学习平台，使用MySQL数据库作为数据存储，集成了完整的社区功能、AI助手和在线编程评测系统。

## 功能特性

### 核心功能
- 用户认证系统（登录、注册、角色管理）
- 课程管理（创建、编辑、删除）
- 章节和小节管理（支持视频、文档、图片等多种内容类型）
- 文件上传（支持视频、图片、文档）
- 学习进度追踪

### 社区系统
- 帖子发布（支持标题、正文、图片上传）
- 评论和回复（支持嵌套回复）
- 点赞功能（帖子和评论）
- 个人中心（我的帖子、我的回复、回复我的）
- 代码分享功能

### 在线编程评测
- 题库管理（题目分类、难度分级）
- 在线代码提交与评测
- 支持C++代码编译运行
- 测试用例自动评判（AC/WA/TLE/CE/RE）
- 教师选题与作业布置
- 题目批量导入功能

### AI助手
- 智能问答（C++学习相关问题）
- 代码解释和建议
- 学习资源推荐
- 支持多种AI模型（Gemini、ChatGPT、Deepseek）

## 技术栈

- 后端：Flask 3.1.3
- 数据库：MySQL
- 前端：HTML5, CSS3, JavaScript
- 认证：Flask-Login
- 表单：Flask-WTF
- 缓存：Flask-Caching
- 限流：Flask-Limiter
- 数据处理：pandas, openpyxl
- AI API：Gemini, ChatGPT, Deepseek

## 安装步骤

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+
- g++ 编译器（用于代码评测）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置数据库
创建MySQL数据库，并在`.env`文件中配置数据库连接信息：
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=learning_platform
```

### 4. 配置AI助手（可选）
在`.env`文件中添加AI API密钥：
```env
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 5. 运行应用
```bash
python run.py
```

### 6. 访问应用
- 默认地址：http://localhost:5001
- 管理员账户：用户名 `admin`，密码 `admin123`
- 教师账户：用户名 `teacher`，密码 `teacher123`
- 学生账户：用户名 `student`，密码 `student123`

## 目录结构

```
C-learning-platform/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── mysql_database.py
│   ├── utils.py
│   ├── cache_utils.py
│   ├── exceptions.py
│   ├── recommendation.py
│   ├── forms/
│   │   ├── __init__.py
│   │   └── forms.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── community.py
│   │   ├── ai_assistant.py
│   │   └── recommendation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── learning_progress_service.py
│   │   └── user_service.py
│   └── templates/
│       ├── base.html
│       ├── community.html
│       ├── post_detail.html
│       ├── ai_assistant.html
│       ├── recommendations.html
│       ├── auth/
│       ├── admin/
│       ├── teacher/
│       ├── student/
│       └── errors/
├── static/
│   ├── style.css
│   └── script.js
├── uploads/
│   ├── covers/
│   ├── videos/
│   ├── images/
│   ├── documents/
│   ├── materials/
│   └── community/
├── run.py
├── .env
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

## 用户角色

### 管理员
- 用户管理（创建、编辑、删除用户）
- 课程管理
- 题库管理（添加、编辑、导入题目）
- 系统统计
- 社区管理

### 教师
- 创建和管理课程
- 添加章节和小节
- 上传视频、图片、文档
- 管理课程资料
- 从题库选题布置作业
- 管理社区帖子

### 学生
- 浏览和学习课程
- 下载课程资料
- 参与社区讨论（发布帖子、评论、点赞）
- 在线编程练习
- 提交作业
- 使用AI助手进行学习问答
- 分享代码片段

## 主要功能详情

### 课程学习
- 视频课程播放
- 文档资料阅读
- 学习进度记录
- 课程评价

### 在线编程
- 支持C++语言
- 实时代码编译
- 自动测试用例评判
- 评测状态：AC（通过）、WA（答案错误）、TLE（超时）、CE（编译错误）、RE（运行时错误）

### 题库系统
- 题目分类管理
- 难度分级（简单、中等、困难）
- 支持批量导入题目
- 题目来源追踪

### 作业系统
- 教师选题布置
- 作业时间设置
- 学生提交记录
- 批改与反馈

## 数据库表结构

| 表名 | 说明 |
|------|------|
| users | 用户信息 |
| courses | 课程信息 |
| chapters | 章节信息 |
| lessons | 小节信息 |
| learning_progress | 学习进度 |
| materials | 课程资料 |
| discussions | 社区帖子 |
| replies | 帖子回复 |
| discussion_likes | 帖子点赞 |
| reply_likes | 回复点赞 |
| code_shares | 代码分享 |
| reviews | 课程评价 |
| problem_categories | 题目分类 |
| problems | 题库 |
| submissions | 代码提交记录 |
| ai_conversations | AI对话记录 |
| teacher_assignments | 教师作业 |
| teacher_selected_problems | 教师选题 |
| problem_import_logs | 题目导入日志 |

## 配置说明

### 应用配置
编辑 `app/config.py` 文件：
- `SECRET_KEY`：应用密钥
- `UPLOAD_FOLDER`：上传文件目录
- `MAX_CONTENT_LENGTH`：最大上传文件大小（默认500MB）
- `PERMANENT_SESSION_LIFETIME`：会话有效期（默认7天）

### 环境变量
在 `.env` 文件中配置：
```env
SECRET_KEY=your_secret_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=learning_platform
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 开发说明

- 修改配置：编辑 `app/config.py`
- 添加路由：在 `app/routes/` 目录下创建或修改路由文件
- 添加表单：在 `app/forms/forms.py` 中定义
- 添加服务：在 `app/services/` 目录下创建服务类
- 修改模板：在 `app/templates/` 目录下编辑HTML文件

## 注意事项

1. 首次运行会自动创建数据库表和默认账户
2. 上传的文件存储在 `uploads` 目录
3. 代码评测功能需要系统安装 g++ 编译器
4. AI功能需要配置相应的API密钥
5. 建议定期备份数据库

## 许可证

MIT License
