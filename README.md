# C++学习平台 - Flask版本

基于Flask框架开发的C++学习平台，使用Access数据库作为数据存储，集成了完整的社区功能和AI助手。

## 功能特性

- 用户认证系统（登录、注册、角色管理）
- 课程管理（创建、编辑、删除）
- 章节和小节管理（支持视频、文档、图片等多种内容类型）
- 文件上传（支持视频、图片、文档）
- 完整的社区系统（帖子发布、评论、点赞、嵌套回复）
- AI助手（智能问答功能）
- 代码分享功能
- 响应式设计

## 技术栈

- 后端：Flask
- 数据存储：Microsoft Access
- 前端：HTML5, CSS3, JavaScript
- 认证：Flask-Login
- AI API：DeepSeek, Doubao

## 安装步骤

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python run.py
```

3. 访问应用：
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
│   ├── database.py
│   ├── access_database.py
│   ├── models.py
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
│   └── templates/
│       ├── base.html
│       ├── community.html
│       ├── auth/
│       ├── admin/
│       ├── teacher/
│       └── student/
├── database/
│   └── Database1.accdb
├── uploads/
│   ├── covers/
│   ├── videos/
│   ├── images/
│   ├── documents/
│   ├── materials/
│   └── community/
├── run.py
├── .env
└── requirements.txt
```

## 用户角色

- **管理员**：系统管理、用户管理、课程管理、社区管理
- **教师**：创建课程、上传内容、管理章节、管理社区帖子
- **学生**：学习课程、下载资料、参与社区讨论、使用AI助手

## 主要功能

### 教师功能
- 创建和管理课程
- 添加章节和小节
- 上传视频、图片、文档
- 管理课程资料
- 管理社区帖子

### 学生功能
- 浏览和学习课程
- 下载课程资料
- 参与社区讨论（发布帖子、评论、点赞）
- 使用AI助手进行学习问答
- 分享代码片段

### 管理员功能
- 用户管理（创建、编辑、删除用户）
- 课程管理
- 系统统计
- 社区管理

### 社区功能
- 发布帖子（支持标题、正文、图片上传）
- 评论和回复（支持嵌套回复）
- 点赞功能（帖子和评论）
- 个人中心（我的帖子、我的回复、回复我的）
- 代码分享功能

### AI助手功能
- 智能问答（C语言学习相关问题）
- 代码解释和建议
- 学习资源推荐

## 数据存储

系统使用Microsoft Access数据库存储所有数据：
- 数据库文件：database/Database1.accdb
- 表结构：users, courses, chapters, lessons, materials, discussions, replies, discussion_likes, reply_likes, code_shares等

## 注意事项

1. 首次运行会自动创建管理员账户和必要的数据库表
2. 上传的文件存储在uploads目录
3. 数据库文件存储在database目录
4. 建议定期备份数据库文件
5. AI功能需要配置API密钥（在.env文件中设置）

## 开发说明

- 修改配置：编辑app/config.py
- 添加新功能：在app/routes/目录下创建新的路由文件
- 修改模板：在app/templates/目录下编辑HTML文件
- 配置AI API：编辑.env文件

## 许可证

MIT License