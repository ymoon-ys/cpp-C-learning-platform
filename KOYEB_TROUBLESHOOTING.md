# Koyeb部署问题排查指南

## ✅ 已修复的问题（2026-04-04）

### 1. 静态资源文件名不匹配问题（根本原因）
**问题描述**：Vite构建生成带hash的文件名，但base.html中硬编码了旧hash
**影响范围**：所有页面无法加载CSS/JS → 页面白屏或样式错乱
**修复方案**：
- 修改 [vite.config.js](vite.config.js)：移除文件名中的hash
- 更新 [base.html](app/templates/base.html)：使用固定文件名
- 创建 [update_assets.py](update_assets.py)：自动化更新脚本
- 更新 [Dockerfile](Dockerfile)：构建后自动同步文件名
- 更新 [package.json](package.json)：添加postbuild钩子

### 2. Dashboard模板变量缺失
**问题描述**：`dashboard()`函数缺少`total_students`和`consecutive_days`变量
**影响范围**：教师仪表盘页面渲染失败
**修复位置**：[app/routes/teacher.py:23-33](app/routes/teacher.py)

### 3. MySQL连接池多Worker冲突
**问题描述**：类级别连接池在Gunicorn多Worker环境下不安全
**影响范围**：数据库操作间歇性失败
**修复位置**：[app/mysql_database.py](app/mysql_database.py)

---

## 🔧 Koyeb环境变量配置清单

### 必需环境变量

| 变量名 | 说明 | 示例值 | 是否必需 |
|--------|------|--------|----------|
| `MYSQL_HOST` | MySQL服务地址 | `koyeb-mysql-service.koyeb` | ✅ 是 |
| `MYSQL_USER` | 数据库用户名 | `root` 或 Koyeb提供 | ✅ 是 |
| `MYSQL_PASSWORD` | 数据库密码 | `your_password_here` | ✅ 是 |
| `MYSQL_DATABASE` | 数据库名称 | `learning_platform` | ✅ 是 |
| `MYSQL_PORT` | MySQL端口 | `3306` | ✅ 是 |
| `DB_TYPE` | 数据库类型 | `mysql` | ✅ 是 |
| `SECRET_KEY` | Flask密钥 | `random-string-here` | ✅ 是 |
| `FLASK_ENV` | 运行环境 | `production` | ⚠️ 推荐 |

### 可选环境变量（AI功能）

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OLLAMA_BASE_URL` | Ollama服务地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | AI模型名称 | `qwen3-coder:30b` |
| `BAIDU_OCR_API_KEY` | 百度OCR密钥 | (空) |
| `OPENAI_API_KEY` | OpenAI API密钥 | (空) |

---

## 🚀 部署步骤

### 1. 推送代码到Git仓库
```bash
git add .
git commit -m "fix: 修复Koyeb课程创建显示问题和静态资源加载"
git push origin main
```

### 2. 在Koyeb控制台配置

#### 方案A：使用Koyeb内置MySQL服务
1. 创建MySQL服务：
   - Services → New Service → MySQL
   - 记录连接信息（Host, User, Password, Database）

2. 配置Web应用环境变量：
   - 进入你的Flask应用 → Environment Variables
   - 添加上述所有必需变量
   - 确保MySQL Host指向正确的内部服务地址

3. 重新部署：
   - Deployments → Redeploy
   - 等待构建完成（约2-3分钟）

#### 方案B：使用外部MySQL服务
如果你使用外部MySQL（如Railway, PlanetScale等）：

```env
MYSQL_HOST=your-external-mysql-host.com
MYSQL_USER=your_username
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=learning_platform
MYSQL_PORT=3306
```

---

## 🐛 调试方法

### 1. 查看构建日志
在Koyeb控制台 → 你的应用 → Deployments → 选择最新部署 → Logs

**正常启动日志应该包含**：
```
[OK] Using MySQL database: learning_platform
Connection: mysql-host:3306
[OK] Database connection pool created successfully
[OK] Got database connection from pool
[OK] Table created: users
[OK] Table created: courses
... (其他表)
[OK] Upload folder ready: /app/uploads
[OK] Created default user: admin
[OK] All default users already exist
```

**错误日志示例及解决方案**：

#### 错误1：数据库连接失败
```
[ERR] Failed to create connection pool (attempt 1/3): Access denied for user
[ERR] Failed to connect to MySQL database: Can't connect to MySQL server
```
**解决**：检查MySQL环境变量是否正确，特别是密码和主机地址

#### 错误2：静态资源404
```
GET /static/dist/assets/main.css HTTP/1.1" 404
GET /static/dist/assets/main.js HTTP/1.1" 404
```
**解决**：已通过本次修复解决（移除hash）

#### 错误3：模板渲染错误
```
Error: jinja2.exceptions.UndefinedError: 'total_students' is undefined
```
**解决**：已通过本次修复解决（添加缺失变量）

### 2. 使用浏览器开发者工具
按F12打开开发者工具：

1. **Console标签页**：查看JavaScript错误
2. **Network标签页**：检查哪些请求失败（红色）
3. **Elements标签页**：检查HTML结构是否完整

### 3. 测试API端点
使用curl或Postman测试关键接口：

```bash
# 测试教师仪表盘API（需要先登录获取cookie）
curl -H "Cookie: session_token=YOUR_TOKEN" https://your-app.koyeb.app/teacher/dashboard

# 应该返回200状态码和HTML内容
```

---

## 📋 课程创建功能测试清单

### 前置条件
- [ ] 已登录教师账号
- [ ] MySQL数据库连接正常
- [ ] 页面能正常加载CSS/JS（无404）

### 测试步骤
1. **访问教师仪表盘**
   - URL: `/teacher/dashboard`
   - 预期：看到统计卡片和"创建课程"按钮

2. **点击创建课程**
   - URL: `/teacher/courses/create`
   - 预期：显示完整的课程创建表单

3. **填写并提交**
   - 标题、描述、分类、难度（必填）
   - 封面图片（可选）
   - 点击"创建课程"

4. **验证结果**
   - 成功提示："课程创建成功"
   - 自动跳转到教师仪表盘
   - 新课程出现在"我的课程"列表中

---

## 🆘 常见问题FAQ

### Q1: 页面完全空白？
A: 检查浏览器Console是否有JS错误，Network标签是否有404。最可能是静态资源加载失败。

### Q2: 显示500 Internal Server Error？
A: 查看Koyeb日志，通常是数据库连接或模板渲染错误。

### Q3: 登录后跳转到空白页？
A: 检查用户角色是否为teacher，以及dashboard路由是否正常工作。

### Q4: 课程创建成功但不显示？
A: 检查数据库courses表是否有记录，确认teacher_id与当前用户一致。

### Q5: 上传封面图片失败？
A: 检查uploads目录权限，确保Docker容器有写入权限。

---

## 📞 技术支持

如果以上方法都无法解决问题，请收集以下信息：

1. **浏览器截图**：F12 Console和Network的错误信息
2. **Koyeb部署日志**：完整的启动日志
3. **环境变量确认**：（隐藏敏感信息）确认哪些变量已配置
4. **复现步骤**：详细描述从登录到出错的每一步操作

提交Issue时请包含上述信息，以便快速定位问题。

---

## 🎯 下一步优化建议

1. **添加健康检查端点**：`/healthz` 用于监控
2. **集成日志系统**：如Sentry进行错误追踪
3. **CDN加速**：将静态资源托管到CDN
4. **数据库迁移工具**：使用Alembic管理数据库版本
5. **CI/CD流水线**：自动运行测试后再部署

---

最后更新：2026-04-04
修复版本：v1.0.1-hotfix