# C++学习平台

基于Flask框架开发的C++在线学习平台，集成了完整的社区功能、AI智能助手和在线编程评测系统。

## 功能特性

### 核心功能
- 用户认证系统（登录、注册、角色管理：管理员/教师/学生）
- 课程管理（创建、编辑、删除课程）
- 章节和小节管理（支持视频、文档、图片等多种内容类型）
- 文件上传（支持视频、图片、文档，最大500MB）
- 学习进度追踪与统计
- 连续学习天数记录

### 社区系统（贴吧+抖音风格）
- 帖子发布（支持标题、正文、多图上传）
- 评论和回复（支持嵌套回复）
- 点赞功能（帖子和评论）
- 个人中心（我的帖子、我的回复、回复我的）
- 代码分享功能
- 热门/最新排序

### 在线编程评测
- 题库管理（题目分类、难度分级）
- **在线代码编译执行**（支持C++17标准）
- 代码复杂度分析
- **AI智能代码补全**
- 测试用例自动评判（AC/WA/TLE/CE/RE）
- 教师选题与作业布置
- 题目批量导入功能
- 提交记录查看

### CAIgpt AI智能助手（核心特色）

基于 **Ollama 本地部署的 Qwen3-Coder 大模型** 的专业C++编程教学助手：

- 智能问答（C++学习相关问题）
- 代码分析与审查（指出问题、提供优化建议）
- 代码解释和建议
- 图片OCR识别（支持上传代码截图/题目图片）
- 文件上传分析（.cpp/.h/.txt/.md/PDF）
- **动态教学**（根据学生水平自动调整回答深度）
- 学习资源推荐

#### AI助手高级功能
- 多会话管理（创建、搜索、删除会话）
- 会话标签分类
- 消息收藏功能
- 对话历史持久化存储
- **对话导出**（Markdown/PDF格式）
- 流式输出（实时显示AI回答）
- 用户个性化偏好设置（主题、编辑器样式等）
- 代码自动保存

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask 3.1.3 |
| 数据库 | MySQL / SQLite（可切换） |
| 前端 | HTML5, CSS3, JavaScript |
| 用户认证 | Flask-Login |
| 表单验证 | Flask-WTF |
| 缓存 | Flask-Caching |
| 接口限流 | Flask-Limiter |
| 数据处理 | pandas, openpyxl |
| AI模型 | Ollama + Qwen3-Coder (本地) |
| OCR识别 | 百度OCR API |
| 图像处理 | PIL/Pillow |
| PDF生成 | weasyprint / reportlab |

## 安装步骤

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+ 或 SQLite
- g++ 编译器（MinGW-w64 / GCC / Clang）
- Ollama（用于AI助手，可选）

### 2. 安装MinGW-w64编译器（Windows推荐）

**方式一：直接安装到 C:\mingw64**
- 下载 MinGW-w64: https://www.mingw-w64.org/downloads
- 解压到 `C:\mingw64`
- 将 `C:\mingw64\bin` 添加到系统 PATH

**方式二：MSYS2安装**
```bash
pacman -S mingw-w64-x86_64-gcc
```

**方式三：设置环境变量**
```env
GPP_PATH=C:\mingw64\bin\g++.exe
```

### 3. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# ===== 数据库配置 =====
DB_TYPE=mysql                    # mysql 或 sqlite
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=learning_platform
MYSQL_PORT=3306

# ===== 应用密钥 =====
SECRET_KEY=your-secret-key-here

# ===== Ollama AI配置（CAIgpt）=====
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3-coder:30b
OLLAMA_TIMEOUT=60

# ===== 百度OCR配置（可选）=====
BAIDU_OCR_API_KEY=your_api_key
BAIDU_OCR_SECRET_KEY=your_secret_key

# ===== 编译器路径（可选，自动检测）=====
GPP_PATH=C:\mingw64\bin\g++.exe
```

### 5. 安装Ollama和AI模型（AI助手必需）

```bash
# 安装 Ollama
# Windows: https://ollama.ai/download
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 下载 Qwen3-Coder 模型
ollama pull qwen3-coder:30b
```

### 6. 运行应用
```bash
python run.py
```

### 7. 访问应用
- 默认地址：http://localhost:5001
- 管理员账户：用户名 `admin`，密码 `admin123`
- 教师账户：用户名 `teacher`，密码 `teacher123`
- 学生账户：用户名 `student`，密码 `student123`

## 目录结构

```
C-learning-platform/
├── app/
│   ├── __init__.py              # 应用初始化
│   ├── config.py                # 应用配置
│   ├── models.py                # 数据模型
│   ├── mysql_database.py        # MySQL数据库操作
│   ├── sqlite_database.py       # SQLite数据库操作
│   ├── utils.py                 # 工具函数
│   ├── cache_utils.py           # 缓存工具
│   ├── exceptions.py            # 自定义异常
│   ├── recommendation.py        # 推荐算法
│   ├── forms/
│   │   └── forms.py             # 表单定义
│   ├── routes/
│   │   ├── auth.py              # 认证路由
│   │   ├── admin.py             # 管理员路由
│   │   ├── teacher.py           # 教师路由
│   │   ├── student.py           # 学生路由
│   │   ├── course.py            # 课程路由
│   │   ├── community.py         # 社区路由
│   │   ├── ai_assistant.py      # AI助手路由（CAIgpt）
│   │   └── recommendation.py    # 推荐路由
│   ├── services/
│   │   ├── auth_service.py      # 认证服务
│   │   ├── learning_progress_service.py  # 学习进度服务
│   │   └── user_service.py      # 用户服务
│   └── templates/
│       ├── base.html
│       ├── community.html       # 社区页面
│       ├── post_detail.html     # 帖子详情
│       ├── ai_assistant.html    # AI助手页面
│       ├── recommendations.html # 推荐页面
│       ├── auth/                # 认证模板
│       ├── admin/               # 管理员模板
│       ├── teacher/             # 教师模板
│       ├── student/             # 学生模板
│       └── errors/              # 错误页面
├── static/
│   ├── style.css
│   └── script.js
├── uploads/
│   ├── covers/                  # 课程封面
│   ├── videos/                  # 视频文件
│   ├── images/                  # 图片文件
│   ├── documents/               # 文档文件
│   ├── materials/               # 课程资料
│   ├── community/               # 社区图片
│   └── avatars/                 # 用户头像
├── run.py                       # 入口文件
├── .env                         # 环境变量配置
├── .env.example                 # 环境变量示例
├── requirements.txt             # Python依赖
└── requirements-dev.txt         # 开发依赖
```

## 用户角色与权限

### 管理员
- 用户管理（创建、编辑、删除用户）
- 课程管理
- 题库管理（添加、编辑、导入题目）
- 题目批量导入（Excel格式）
- 系统统计仪表盘
- 社区管理
- 导入日志查看

### 教师
- 创建和管理课程
- 添加章节和小节
- 上传视频、图片、文档
- 管理课程资料
- 从题库选题布置作业
- 设置作业时间
- 查看学生提交记录
- 管理社区帖子

### 学生
- 浏览和学习课程
- 下载课程资料
- 在线编写和运行C++代码
- 参与社区讨论（发布帖子、评论、点赞）
- 完成编程作业
- 使用CAIgpt AI助手进行学习问答
- 代码分享与交流
- 查看学习进度和连续学习天数

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
| caigpt_dialog_history | CAIgpt对话历史 |
| caigpt_sessions | CAIgpt会话 |
| caigpt_favorites | CAIgpt收藏 |
| ai_user_preferences | 用户AI偏好设置 |

## API接口说明

### AI助手接口 (`/ai`)
| 接口 | 方法 | 说明 |
|------|------|------|
| `/ai/chat` | POST | 发送消息给AI |
| `/ai/chat/stream` | POST | 流式对话 |
| `/ai/code/execute` | POST | 编译执行C++代码 |
| `/ai/code/analyze` | POST | 代码复杂度分析 |
| `/ai/code/complete` | POST | AI代码补全 |
| `/ai/sessions` | GET/POST | 获取/创建会话 |
| `/ai/sessions/<id>` | GET/DELETE | 会话详情/删除 |
| `/ai/favorites` | GET/POST/DELETE | 收藏管理 |
| `/ai/export/<id>` | GET | 导出对话(MD/PDF) |
| `/ai/preferences` | GET/POST | 用户偏好设置 |
| `/ai/code/compiler-info` | GET | 获取编译器信息 |

### 社区接口 (`/community`)
| 接口 | 方法 | 说明 |
|------|------|------|
| `/community/discussions` | GET | 获取帖子列表 |
| `/community/discussions` | POST | 发布帖子 |
| `/community/discussions/<id>` | GET | 帖子详情 |
| `/community/replies` | POST | 发表评论 |
| `/community/replies/<id>/like` | POST | 点赞评论 |

## 配置说明

### 数据库切换
```env
# 使用MySQL
DB_TYPE=mysql

# 使用SQLite（无需安装MySQL，适合开发测试）
DB_TYPE=sqlite
```

### AI模型配置
项目默认使用本地Ollama部署的Qwen3-Coder模型，无需API密钥，保护数据隐私。

如需使用云端API，可在 `app/routes/ai_assistant.py` 中配置：
- Gemini (Google)
- ChatGPT (OpenAI)
- Deepseek

### 编译器配置
系统会自动查找g++编译器，按以下顺序：
1. 环境变量 `GPP_PATH`
2. 系统PATH中的g++
3. Windows常见路径（C:\mingw64\bin等）
4. Linux/macOS常见路径

## 开发指南

### 添加新功能
1. 在 `app/routes/` 创建路由文件
2. 在 `app/__init__.py` 注册Blueprint
3. 在 `app/templates/` 创建模板
4. 如需数据模型，在 `app/models.py` 定义

### 添加新服务
在 `app/services/` 目录下创建服务类，遵循现有模式。

### 代码规范
- 使用中文注释
- 遵循PEP 8风格
- 错误处理使用自定义异常 `BusinessException`

## 注意事项

1. 首次运行会自动创建数据库表和默认账户
2. 上传的文件存储在 `uploads` 目录
3. 代码评测功能需要安装 g++ 编译器（推荐MinGW-w64）
4. AI功能需要运行Ollama服务并下载模型
5. 百度OCR为可选功能，不配置不影响主要功能
6. 建议定期备份数据库
7. 生产环境请修改 `SECRET_KEY`

## 许可证

MIT License
