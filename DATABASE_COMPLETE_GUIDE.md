# C语言学习平台 - MySQL数据库完整设计方案

## 📋 项目概述

本项目是一个基于 **Python Flask + MySQL** 的C语言在线学习平台，支持多角色用户（管理员、教师、学生），包含课程管理、编程题库、代码评测、AI助手、社区互动等完整功能模块。

**数据库版本**: MySQL 5.7+ / 8.0+  
**字符集**: utf8mb4  
**排序规则**: utf8mb4_unicode_ci  
**总数据表数量**: **20张**

---

## 🗄️ 数据库架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    learning_platform 数据库                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  users   │◄───│ courses  │◄───│ chapters │              │
│  │ (用户表) │    │ (课程表) │    │ (章节表) │              │
│  └────┬─────┘    └────▲─────┘    └────▲─────┘              │
│       │               │               │                    │
│       │         ┌─────┴─────┐   ┌─────┴─────┐             │
│       │         │  lessons  │   │materials │              │
│       │         │  (课时表) │   │(资料表)  │              │
│       │         └─────┬─────┘   └──────────┘              │
│       │               │                                  │
│       │    ┌──────────┴──────────┐                        │
│       │    │ learning_progress   │                        │
│       │    │   (学习进度表)      │                        │
│       │    └─────────────────────┘                        │
│       │                                                    │
│       ├────────────────────────────────────┐              │
│       │                                    │              │
│  ┌────┴─────┐  ┌──────────────┐  ┌────────┴──────┐        │
│  │problems  │  │submissions   │  │problem_       │        │
│  │(题目表)  │◄─│(提交记录表)  │  │categories     │        │
│  └────▲─────┘  └──────────────┘  │(题目分类表)   │        │
│       │                          └──────────────┘        │
│       │                                                    │
│  ┌────┴──────────────┐  ┌─────────────────────┐          │
│  │teacher_assignments│  │teacher_selected_    │          │
│  │  (教师作业表)     │  │problems(教师选题)   │          │
│  └───────────────────┘  └─────────────────────┘          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              社区功能模块                         │   │
│  │  ┌──────────┐  ┌────────┐  ┌────────────────┐  │   │
│  │  │discussions│◄─│replies │  │discussion_likes│  │   │
│  │  │ (帖子表)  │  │(评论表)│  │ (帖子点赞表)   │  │   │
│  │  └──────────┘  └───┬────┘  └────────────────┘  │   │
│  │                      │                            │   │
│  │              ┌───────┴───────┐                   │   │
│  │              │ reply_likes   │                   │   │
│  │              │ (评论点赞表)  │                   │   │
│  │  ┌──────────┴──────────────┐│                   │   │
│  │  │ code_shares (代码分享)  ││                   │   │
│  │  └─────────────────────────┘┘                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              AI助手模块                           │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐ │   │
│  │  │ai_conversations   │  │caigpt_dialog_history│ │   │
│  │  │ (AI对话记录)      │  │ (CaiGPT对话历史)    │ │   │
│  │  └──────────────────┘  └──────────────────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────┐                              │
│  │ problem_import_logs   │                              │
│  │ (题目导入日志)        │                              │
│  └──────────────────────┘                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 数据表详细说明

### 一、核心用户系统（1张表）

#### 1. users - 用户表
**用途**: 存储所有用户信息（管理员、教师、学生）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(255) | NOT NULL, UNIQUE | 用户名 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希值 |
| role | VARCHAR(50) | DEFAULT 'student' | 角色: admin/teacher/student |
| nickname | VARCHAR(255) | NULLABLE | 昵称 |
| avatar | VARCHAR(500) | NULLABLE | 头像URL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**: 
- `uk_username` (username) - 唯一索引
- `uk_email` (email) - 唯一索引  
- `idx_role` (role) - 普通索引

---

### 二、课程管理系统（4张表）

#### 2. courses - 课程表
**用途**: 存储课程基本信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 课程ID |
| title | VARCHAR(255) | NOT NULL | 课程标题 |
| description | TEXT | NULLABLE | 课程描述 |
| teacher_id | INT | FK → users.id | 授课教师ID |
| category | VARCHAR(100) | NULLABLE | 课程分类 |
| cover | VARCHAR(255) | NULLABLE | 封面图片URL |
| status | VARCHAR(50) | DEFAULT 'draft' | 状态: draft/published/archived |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 3. chapters - 章节表
**用途**: 课程下的章节划分

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 章节ID |
| course_id | INT | FK → courses.id, NOT NULL | 所属课程ID |
| title | VARCHAR(255) | NOT NULL | 章节标题 |
| order_index | INT | DEFAULT 0 | 排序序号 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

#### 4. lessons - 课时表
**用途**: 章节下的具体课时内容

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 课时ID |
| chapter_id | INT | FK → chapters.id, NOT NULL | 所属章节ID |
| title | VARCHAR(255) | NOT NULL | 课时标题 |
| description | TEXT | NULLABLE | 课时描述 |
| content | TEXT | NULLABLE | 内容（富文本） |
| content_type | VARCHAR(50) | DEFAULT 'text' | 类型: text/video/document |
| content_path | VARCHAR(255) | NULLABLE | 文件路径 |
| duration | VARCHAR(50) | NULLABLE | 时长（视频用） |
| order_index | INT | DEFAULT 0 | 排序序号 |

#### 5. materials - 课程资料表
**用途**: 教师上传的课程资料文件

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 资料ID |
| course_id | INT | FK → courses.id, NOT NULL | 所属课程ID |
| title | VARCHAR(255) | NOT NULL | 资料标题 |
| file_url | VARCHAR(255) | NOT NULL | 文件存储路径 |
| type | VARCHAR(50) | NULLABLE | 文件类型: pdf/doc/xls等 |
| uploader_id | INT | FK → users.id, NOT NULL | 上传者ID |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

---

### 三、学习进度系统（2张表）

#### 6. learning_progress - 学习进度表
**用途**: 记录学生的学习进度和完成情况

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 进度记录ID |
| user_id | INT | FK → users.id, NOT NULL | 学生用户ID |
| course_id | INT | FK → courses.id, NOT NULL | 课程ID |
| chapter_id | INT | FK → chapters.id | 章节ID |
| lesson_id | INT | FK → lessons.id | 课时ID |
| progress | INT | DEFAULT 0 | 学习进度百分比 (0-100) |
| completed | TINYINT(1) | DEFAULT 0 | 是否完成: 0/1 |
| updated_at | DATETIME | ON UPDATE | 最后更新时间 |

**特殊约束**: `UNIQUE KEY uk_user_lesson (user_id, lesson_id)` - 每个学生对每个课时只有一条进度记录

#### 7. reviews - 课程评价表
**用途**: 学生对课程的评价和评分

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 评价ID |
| course_id | INT | FK → courses.id, NOT NULL | 课程ID |
| user_id | INT | FK → users.id, NOT NULL | 评价用户ID |
| rating | INT | NOT NULL | 评分 (1-5星) |
| comment | TEXT | NULLABLE | 评价内容 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**特殊约束**: `UNIQUE KEY uk_user_course (user_id, course_id)` - 每个用户对每个课程只能评价一次

---

### 四、编程题库系统（3张表）

#### 8. problem_categories - 题目分类表
**用途**: 编程题目的分类体系（支持多级分类）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 分类ID |
| name | VARCHAR(255) | NOT NULL | 分类名称 |
| parent_id | INT | FK → self.id | 父分类ID（NULL=顶级） |
| description | TEXT | NULLABLE | 分类描述 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**特点**: 支持树形结构，通过`parent_id`实现自引用外键

#### 9. problems - 编程题目表 ⭐ 核心表
**用途**: 存储C/C++编程题目（项目核心功能）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 题目ID |
| title | VARCHAR(255) | NOT NULL | 题目标题 |
| description | TEXT | NULLABLE | 题目描述 |
| input_format | TEXT | NULLABLE | 输入格式说明 |
| output_format | TEXT | NULLABLE | 输出格式说明 |
| sample_input | TEXT | NULLABLE | 样例输入 |
| sample_output | TEXT | NULLABLE | 样例输出 |
| difficulty | VARCHAR(50) | DEFAULT 'medium' | 难度: easy/medium/hard |
| category_id | INT | FK → problem_categories.id | 所属分类ID |
| time_limit | INT | DEFAULT 1 | 时间限制（秒） |
| memory_limit | INT | DEFAULT 256 | 内存限制（MB） |
| test_cases | JSON | NULLABLE | 测试用例（JSON数组） |
| source | VARCHAR(100) | NULLABLE | 来源平台: luogu/hdoj/leetcode |
| source_id | VARCHAR(100) | NULLABLE | 来源平台题目ID |
| source_url | VARCHAR(500) | NULLABLE | 来源链接 |
| is_public | TINYINT(1) | DEFAULT 0 | 是否公开: 0/1 |
| tags | VARCHAR(500) | NULLABLE | 标签（JSON字符串） |
| hint | TEXT | NULLABLE | 提示信息 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**全文索引**: `FULLTEXT KEY ft_title_description (title, description)` - 支持标题和描述的全文搜索

#### 10. submissions - 代码提交记录表
**用途**: 学生提交代码的评测记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 提交记录ID |
| user_id | INT | FK → users.id, NOT NULL | 提交用户ID |
| problem_id | INT | FK → problems.id, NOT NULL | 题目ID |
| code | TEXT | NOT NULL | 提交的代码 |
| status | VARCHAR(50) | DEFAULT 'pending' | 评测状态 |
| error_message | TEXT | NULLABLE | 错误信息 |
| submit_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 提交时间 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**评测状态说明**:
- `AC` - Accepted (答案正确)
- `WA` - Wrong Answer (答案错误)
- `TLE` - Time Limit Exceeded (超时)
- `MLE` - Memory Limit Exceeded (超内存)
- `CE` - Compile Error (编译错误)
- `RE` - Runtime Error (运行时错误)
- `pending` - 待评测

---

### 五、教师管理系统（2张表）

#### 11. teacher_assignments - 教师作业表
**用途**: 教师布置的作业任务

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 作业ID |
| teacher_id | INT | FK → users.id, NOT NULL | 教师用户ID |
| problem_id | INT | FK → problems.id, NOT NULL | 关联题目ID |
| title | VARCHAR(255) | NULLABLE | 作业标题 |
| description | TEXT | NULLABLE | 作业描述 |
| start_time | DATETIME | NULLABLE | 开始时间 |
| end_time | DATETIME | NULLABLE | 截止时间 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

#### 12. teacher_selected_problems - 教师选中题目表
**用途**: 教师为课程选择的练习题目（支持可见性控制）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 记录ID |
| teacher_id | INT | FK → users.id, NOT NULL | 教师用户ID |
| problem_id | INT | FK → problems.id, NOT NULL | 题目ID |
| course_id | INT | FK → courses.id | 关联课程ID |
| selected_at | DATETIME | DEFAULT NOW | 选择时间 |
| visible_start | DATETIME | NULLABLE | 可见开始时间 |
| visible_end | DATETIME | NULLABLE | 可见结束时间 |
| notes | TEXT | NULLABLE | 备注说明 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**特殊约束**: `UNIQUE KEY uk_teacher_problem (teacher_id, problem_id)` - 同一教师不能重复选择同一题目

---

### 六、社区互动系统（5张表）

#### 13. discussions - 讨论区帖子表 🎯 社区核心
**用途**: 社区讨论帖子（贴吧风格，支持图片、置顶）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 帖子ID |
| course_id | INT | FK → courses.id | 关联课程ID（可选） |
| user_id | INT | FK → users.id, NOT NULL | 发帖用户ID |
| title | VARCHAR(255) | NOT NULL | 帖子标题 |
| content | TEXT | NULLABLE | 帖子内容 |
| images | JSON | NULLABLE | 图片列表（JSON数组） |
| category | VARCHAR(100) | DEFAULT 'general' | 分类 |
| tags | VARCHAR(500) | NULLABLE | 标签（逗号分隔） |
| view_count | INT | DEFAULT 0 | 浏览次数 |
| like_count | INT | DEFAULT 0 | 点赞数 |
| is_sticky | TINYINT(1) | DEFAULT 0 | 是否置顶: 0/1 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**全文索引**: `FULLTEXT KEY ft_title_content (title, content)` - 支持帖子搜索

#### 14. replies - 评论回复表
**用途**: 帖子的评论和嵌套回复（抖音风格）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 评论ID |
| discussion_id | INT | FK → discussions.id, NOT NULL | 所属帖子ID |
| user_id | INT | FK → users.id, NOT NULL | 评论用户ID |
| parent_id | INT | FK → self.id | 父评论ID（NULL=根评论） |
| content | TEXT | NOT NULL | 评论内容 |
| like_count | INT | DEFAULT 0 | 点赞数 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

**特点**: 通过`parent_id`自引用实现无限层级嵌套评论

#### 15. discussion_likes - 帖子点赞表
**用途**: 记录用户对帖子的点赞操作

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 点赞记录ID |
| discussion_id | INT | FK → discussions.id, NOT NULL | 帖子ID |
| user_id | INT | FK → users.id, NOT NULL | 点赞用户ID |
| created_at | DATETIME | DEFAULT NOW | 点赞时间 |

**约束**: `UNIQUE KEY uk_discussion_user (discussion_id, user_id)` - 防止重复点赞

#### 16. reply_likes - 评论点赞表
**用途**: 记录用户对评论的点赞操作

结构同上，关联到`replies`表

#### 17. code_shares - 代码分享表
**用途**: 社区代码分享功能

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 分享ID |
| user_id | INT | FK → users.id, NOT NULL | 分享用户ID |
| title | VARCHAR(255) | NOT NULL | 分享标题 |
| code | TEXT | NOT NULL | 代码内容 |
| description | TEXT | NULLABLE | 描述说明 |
| language | VARCHAR(50) | DEFAULT 'cpp' | 编程语言 |
| tags | VARCHAR(500) | NULLABLE | 标签 |
| view_count | INT | DEFAULT 0 | 浏览次数 |
| like_count | INT | DEFAULT 0 | 点赞数 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

---

### 七、AI助手系统（2张表）

#### 18. ai_conversations - AI对话记录表
**用途**: AI助手与用户的对话历史

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 对话ID |
| user_id | INT | FK → users.id, NOT NULL | 用户ID |
| problem_id | INT | FK → problems.id | 关联题目ID（可选） |
| question | TEXT | NULLABLE | 用户问题 |
| answer | TEXT | NULLABLE | AI回答 |
| model_name | VARCHAR(100) | NULLABLE | 使用的AI模型名称 |
| conversation_type | VARCHAR(100) | DEFAULT 'general' | 对话类型 |
| has_code | TINYINT(1) | DEFAULT 0 | 是否包含代码 |
| has_image | TINYINT(1) | DEFAULT 0 | 是否包含图片 |
| created_at/updated_at | DATETIME | 自动管理 | 时间戳 |

#### 19. caigpt_dialog_history - CaiGPT对话历史表
**用途**: CaiGPT专用对话历史（支持图片消息）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 记录ID |
| user_id | INT | FK → users.id, NOT NULL | 用户ID |
| role | VARCHAR(50) | NOT NULL | 角色: user/assistant/system |
| content | TEXT | NOT NULL | 消息内容 |
| images | JSON | NULLABLE | 图片列表（JSON数组） |
| created_at | TIMESTAMP | DEFAULT NOW | 创建时间 |

---

### 八、系统管理（1张表）

#### 20. problem_import_logs - 题目导入日志表
**用途**: 记录管理员批量导入题目的操作日志

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 日志ID |
| admin_id | INT | FK → users.id, NOT NULL | 操作管理员ID |
| source | VARCHAR(100) | NULLABLE | 数据来源 |
| count | INT | NULLABLE | 导入数量 |
| status | VARCHAR(50) | DEFAULT 'pending' | 状态: success/failed/pending |
| error_message | TEXT | NULLABLE | 错误信息 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

---

## 🔧 数据库关系图（ER图）

```
users (1) ─────────< (N) courses
  │                     │
  │                     ├──< (N) chapters
  │                     │           │
  │                     │           └──< (N) lessons
  │                     │                      │
  │                     ├──< (N) materials      │
  │                     │                      └──< (N) learning_progress >── users
  │                     │
  │                     └──< (N) reviews >── users
  │
  ├──< (N) submissions >── problems
  │                        │
  │                        ├──< (N) teacher_assignments >── users
  │                        │
  │                        └──< (N) teacher_selected_problems >── users
  │                                                              │
  │                                                              └──> courses
  │
  ├──< (N) discussions
  │       │
  │       ├──< (N) replies >── users
  │       │       │
  │       │       └──< (N) reply_likes >── users
  │       │
  │       └──< (N) discussion_likes >── users
  │
  ├──< (N) code_shares
  │
  ├──< (N) ai_conversations
  │       └──> problems (optional)
  │
  ├──< (N) caigpt_dialog_history
  │
  └──< (N) problem_import_logs

problem_categories (self-referencing for tree structure)
  └──< (N) problems
```

---

## 🚀 快速开始指南

### 1️⃣ 配置数据库连接

编辑 `.env.mysql` 文件：

```env
# 数据库配置
DB_TYPE=mysql

# MySQL配置
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=learning_platform
MYSQL_PORT=3306
```

### 2️⃣ 初始化数据库

**方式一：使用SQL脚本（推荐）**

```bash
# 连接到MySQL
mysql -u root -p

# 执行初始化脚本
source init_database.sql

# 或者一行命令
mysql -u root -p < init_database.sql
```

**方式二：使用Python脚本**

```bash
# 测试连接
python test_mysql_complete.py

# 初始化数据库
python test_mysql_complete.py --init
```

### 3️⃣ 启动应用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Flask应用
python run.py
```

应用启动时会自动连接MySQL数据库并创建所有表（如果不存在）。

---

## 📈 性能优化建议

### 已实施的优化措施

✅ **索引优化**
- 所有外键字段都已添加索引
- 常用查询字段（role, status, difficulty等）已添加索引
- 唯一性约束防止重复数据
- 全文索引支持搜索功能

✅ **数据类型优化**
- 使用合适的字段长度（VARCHAR而非TEXT）
- 使用TINYINT存储布尔值
- 使用JSON类型存储结构化数据（test_cases, images等）
- 时间字段使用自动更新的DEFAULT值

✅ **外键约束**
- 确保数据引用完整性
- 设置合理的删除策略（CASCADE/SET NULL）

### 推荐的进一步优化

🔹 **读写分离**
- 主库负责写操作
- 从库负责读操作（适合高并发场景）

🔹 **分库分表**
- submissions表可按时间或用户ID分区
- discussions表可按月归档历史数据

🔹 **缓存层**
- Redis缓存热门课程、题目
- 缓存用户会话和学习进度

🔹 **查询优化**
- 为复杂查询创建视图
- 使用EXPLAIN分析慢查询
- 定期ANALYZE TABLE更新统计信息

---

## 🔒 安全性设计

### 数据安全

✅ 密码存储：使用Werkzeug的`generate_password_hash()`进行哈希加密  
✅ SQL注入防护：使用参数化查询（%s占位符）  
✅ XSS防护：模板引擎自动转义  
✅ CSRF保护：Flask-WTF表单验证  

### 访问控制

✅ 角色权限：admin/teacher/student三级权限体系  
✅ 登录认证：Flask-Login会话管理  
✅ API限流：Flask-Limiter频率限制  
✅ 文件上传：白名单限制文件类型  

---

## 📊 数据统计示例

```sql
-- 统计各角色用户数量
SELECT role, COUNT(*) as count FROM users GROUP BY role;

-- 统计各难度题目数量
SELECT difficulty, COUNT(*) as count FROM problems GROUP BY difficulty;

-- 统计最活跃的前10个用户
SELECT u.username, COUNT(s.id) as submission_count
FROM users u
LEFT JOIN submissions s ON u.id = s.user_id
GROUP BY u.id
ORDER BY submission_count DESC
LIMIT 10;

-- 统计课程平均评分
SELECT c.title, AVG(r.rating) as avg_rating
FROM courses c
LEFT JOIN reviews r ON c.id = r.course_id
GROUP BY c.id
HAVING avg_rating IS NOT NULL
ORDER BY avg_rating DESC;
```

---

## 🛠️ 维护命令

### 备份数据库

```bash
# 完整备份
mysqldump -u root -p learning_platform > backup_$(date +%Y%m%d).sql

# 仅备份数据（不含建表语句）
mysqldump -u root -p --no-create-info learning_platform > data_backup.sql
```

### 恢复数据库

```bash
mysql -u root -p learning_platform < backup_20260402.sql
```

### 性能监控

```sql
-- 查看表大小
SELECT 
    table_name,
    ROUND(data_length/1024/1024, 2) AS "Size (MB)",
    table_rows
FROM information_schema.tables 
WHERE table_schema = 'learning_platform'
ORDER BY data_length DESC;

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
```

---

## ❓ 常见问题

### Q1: 连接MySQL时报错 "Can't connect to MySQL server"
**A**: 检查MySQL服务是否启动，端口是否正确，防火墙是否放行3306端口。

### Q2: 中文显示乱码
**A**: 确保数据库、表、连接都使用utf8mb4字符集。检查`.env.mysql`配置。

### Q3: 外键约束导致删除失败
**A**: 先删除子表数据，或修改外键的ON DELETE策略为SET NULL。

### Q4: 如何重置数据库？
**A**: 
```sql
DROP DATABASE learning_platform;
CREATE DATABASE learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
source init_database.sql
```

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-04-02 | 完整重构，添加索引、外键、JSON字段 |
| v1.0 | 2026-03-xx | 初始版本，基础表结构 |

---

## 👨‍💻 技术支持

如有问题，请检查：
1. 日志输出（控制台和日志文件）
2. MySQL错误日志：`/var/log/mysql/error.log`
3. 应用日志：查看Flask控制台输出

---

**文档生成时间**: 2026-04-02  
**适用版本**: MySQL 5.7+ / 8.0+  
**维护状态**: ✅ 积极维护中
