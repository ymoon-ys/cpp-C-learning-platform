# 🚀 Koyeb 部署完整指南

## 📋 目录
- [前置要求](#前置要求)
- [环境变量配置](#环境变量配置)
- [Koyeb 部署步骤](#koyeb-部署步骤)
- [数据库设置](#数据库设置)
- [AI 服务配置](#ai-服务配置)
- [故障排除](#故障排除)

---

## 前置要求

### ✅ 必须准备
1. **GitHub 仓库** - 代码已推送到 GitHub
2. **MySQL 数据库** - 远程 MySQL 实例（推荐使用云数据库）
3. **Koyeb 账号** - 注册并登录 https://www.koyeb.com

### 🔧 推荐准备（可选）
- Ollama 远程服务（用于 AI 功能）
- 云存储服务（如 AWS S3，用于文件持久化）

---

## 环境变量配置

### 必需环境变量 ⚠️

| 变量名 | 说明 | 示例 | 是否必填 |
|--------|------|------|----------|
| `SECRET_KEY` | Flask Session 密钥 | `abc123...` (32+字符) | ✅ 必须 |
| `MYSQL_HOST` | 数据库主机地址 | `mysql.example.com` | ✅ 必须 |
| `MYSQL_USER` | 数据库用户名 | `lp_user` | ✅ 必须 |
| `MYSQL_PASSWORD` | 数据库密码 | `securePass123!` | ✅ 必须 |
| `MYSQL_DATABASE` | 数据库名称 | `learning_platform` | ✅ 必须 |

### 可选环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_PORT` | 数据库端口 | `3306` |
| `OLLAMA_BASE_URL` | AI 模型服务 URL | 空（禁用 AI） |
| `OLLAMA_MODEL` | AI 模型名称 | `qwen3-coder:30b` |
| `BAIDU_OCR_API_KEY` | 百度 OCR API Key | 空 |
| `FLASK_ENV` | 运行环境 | 自动检测 |

### 生成 SECRET_KEY

```bash
# 方法1: 使用 Python
python -c "import secrets; print(secrets.token_hex(32))"

# 方法2: 使用 OpenSSL
openssl rand -hex 32
```

**⚠️ 重要**: SECRET_KEY 必须是随机字符串，至少 32 个字符！

---

## Koyeb 部署步骤

### 步骤 1: 创建新服务

1. 登录 Koyeb 控制台
2. 点击 **"Create Service"**
3. 选择 **"Git"** 作为部署来源
4. 选择你的 GitHub 仓库
5. 选择分支（通常是 `main` 或 `master`）

### 步骤 2: 配置 Docker 构建

Koyeb 会自动检测 `Dockerfile` 并构建镜像。

**确认 Dockerfile 包含以下内容：**
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y g++ build-essential
```
✅ 已在本次修复中添加

### 步骤 3: 设置端口

- **Port**: `8000` （已在 gunicorn.conf.py 中配置）
- Koyeb 会自动将流量路由到此端口

### 步骤 4: 添加环境变量

在 Koyeb 控制台：
1. 进入 **Settings → Environment Variables**
2. 点击 **"Add Variable"**
3. 添加所有必需的环境变量（参考上方表格）
4. 保存配置

**或者使用 koyeb CLI：**
```bash
koyeb services create learning-platform \
  --git https://github.com/yourusername/C-learning-platform \
  --git-branch main \
  --ports 8000:http \
  --env SECRET_KEY="your-secret-key-here" \
  --env MYSQL_HOST="your-mysql-host.com" \
  --env MYSQL_USER="your_user" \
  --env MYSQL_PASSWORD="your_password" \
  --env MYSQL_DATABASE="learning_platform"
```

### 步骤 5: 部署并验证

1. 点击 **"Deploy"**
2. 等待构建完成（通常 2-5 分钟）
3. 访问 Koyeb 提供的 URL（格式：`https://<service-name>.koyeb.app`）
4. 测试基本功能：
   - ✅ 首页能正常加载
   - ✅ 可以登录默认账户（admin/admin123）
   - ✅ 数据库连接正常

---

## 数据库设置

### 方案 A: 使用云数据库（推荐）

#### 1. Amazon RDS
```bash
# 创建 MySQL 实例后获取连接信息
MYSQL_HOST=your-instance.xxx.region.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=YourStrongPassword!
MYSQL_DATABASE=learning_platform
```

#### 2. PlanetScale（免费额度）
1. 注册 https://planetscale.com
2. 创建数据库 `learning_platform`
3. 获取连接字符串
4. 在 Koyeb 中配置环境变量

#### 3. Railway / Supabase / Neon
这些平台都提供免费的 MySQL/PostgreSQL 数据库。

### 方案 B: 使用 Koyeb 内置数据库

Koyeb 不提供内置数据库，建议使用外部云数据库服务。

### 初始化数据库表

应用启动时会自动创建所有必要的数据库表。如果需要手动初始化：

```sql
-- 连接到 MySQL 后执行 init_database.sql
source init_database.sql;
```

---

## AI 服务配置

### 选项 1: 使用远程 Ollama 服务（推荐）

如果你有自己的服务器运行 Ollama：

1. **安装 Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **下载模型**:
   ```bash
   ollama pull qwen3-coder:30b
   ```

3. **暴露服务** (需要 HTTPS):
   ```bash
   # 使用 Nginx 反向代理 + Let's Encrypt SSL
   # 或者使用 Cloudflare Tunnel
   ```

4. **配置环境变量**:
   ```
   OLLAMA_BASE_URL=https://ollama.yourdomain.com
   ```

### 选项 2: 使用云端 AI API（无需自建）

修改代码使用 OpenAI/Gemini API 替代 Ollama：

```python
# 在 ai_assistant.py 中配置
AI_MODELS = {
    'gemini': {
        'name': 'Gemini',
        'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
        'api_key': os.getenv('GEMINI_API_KEY'),
        'model': 'gemini-pro'
    }
}
```

### 选项 3: 禁用 AI 功能

如果不配置 `OLLAMA_BASE_URL`，AI 助手功能将被禁用，其他功能正常运行。

---

## 故障排除

### ❌ 应用无法启动

**症状**: Koyeb 显示 "CrashLoopBackOff"

**检查步骤**:
1. 查看 Koyeb 日志（Logs 标签页）
2. 常见错误及解决方案：

#### 错误 1: 缺少 SECRET_KEY
```
❌ 缺少必需的环境变量: SECRET_KEY
❌ 生产环境缺少必需配置，应用无法启动！
```
**解决**: 在 Koyeb 环境变量中添加 `SECRET_KEY`

#### 错误 2: 数据库连接失败
```
[✗] MySQL 数据库连接失败！请检查配置
```
**解决**: 
- 检查 MYSQL_HOST/MYSQL_PASSWORD 是否正确
- 确保数据库允许来自 Koyeb IP 的连接
- 确认数据库端口（通常 3306）已开放

#### 错误 3: 编译器未找到
```
✗ 未找到 C++ 编译器 (g++)
```
**解决**: 
- 本次修复已自动在 Dockerfile 中安装 g++
- 如果仍有问题，重新部署即可

### ❌ 页面加载错误

**症状**: 502 Bad Gateway / 504 Timeout

**可能原因**:
1. 数据库响应慢 → 优化查询或升级数据库
2. 内存不足 → 在 Koyeb 中增加实例大小
3. 启动超时 → 增加 gunicorn timeout（已设置为 60s）

### ❌ 无法上传文件

**症状**: 上传失败或文件丢失

**原因**: Docker 容器重启后 uploads 目录被重置

**解决方案**:
1. **短期**: 使用 Koyeb Volume（如果支持）
2. **长期**: 集成云存储（AWS S3 / 阿里云 OSS）

### ❌ AI 功能不可用

**症状**: AI 助手返回错误或无响应

**检查**:
1. 确认 `OLLAMA_BASE_URL` 已正确配置
2. 测试 Ollama 服务是否可访问：
   ```bash
   curl https://your-ollama.com/api/tags
   ```
3. 如果不需要 AI 功能，可以忽略此问题

---

## 性能优化建议

### 1. 实例规格
- **最低要求**: 512MB RAM, 1 vCPU
- **推荐配置**: 1GB RAM, 2 vCPU（支持 AI 功能）

### 2. 数据库优化
- 使用连接池（代码已实现）
- 定期备份数据库
- 为常用查询添加索引

### 3. CDN 加速
- Koyeb 自动提供全球 CDN
- 静态资源会自动缓存

### 4. 监控
- 启用 Koyeb 的监控和告警
- 关注 CPU、内存、网络指标

---

## 安全最佳实践

### ✅ 已实现的安全措施
- HSTS 安全头（仅 HTTPS 时启用）
- XSS 保护
- CSRF 保护（Flask-WTF）
- SQL 注入防护（参数化查询）
- 文件上传安全验证

### 🔒 你需要注意的
1. 定期更换 SECRET_KEY 和数据库密码
2. 不要在代码中硬编码敏感信息
3. 使用强密码策略
4. 定期更新依赖包（`pip install --upgrade -r requirements.txt`）
5. 启用 HTTPS（Koyeb 默认提供）

---

## 更新部署

当代码更新到 GitHub 后：

### 自动部署（推荐）
Koyeb 支持自动部署：
1. Settings → Git
2. 启用 "Autodeploy on push"
3. 每次 push 到 main 分支会自动重新部署

### 手动部署
1. 在 Koyeb 控制台点击 "Redeploy"
2. 或使用 CLI：
   ```bash
   koyeb redeploy <service-id>
   ```

---

## 备份与恢复

### 数据库备份
```bash
# 导出
mysqldump -h MYSQL_HOST -u MYSQL_USER -p MYSQL_DATABASE > backup.sql

# 导入
mysql -h MYSQL_HOST -u MYSQL_USER -p MYSQL_DATABASE < backup.sql
```

### 用户上传文件备份
⚠️ 当前版本：容器重启后上传文件会丢失  
🔧 建议：集成对象存储服务（S3/OSS）

---

## 联系与支持

遇到问题时：

1. **查看日志**: Koyeb 控制台 → Logs
2. **检查配置**: 确认所有环境变量已正确设置
3. **本地测试**: 先在本地测试通过再部署
4. **文档参考**: 
   - Koyeb 官方文档: https://www.koyeb.com/docs
   - Flask 部署文档: https://flask.palletsprojects.com/

---

## 快速检查清单

部署前确认：

- [ ] GitHub 仓库代码最新
- [ ] `.env.production.example` 中的必填项已填写
- [ ] Koyeb 环境变量已全部配置
- [ ] MySQL 数据库可从外网访问
- [ ] 数据库用户有足够权限（CREATE, INSERT, UPDATE, DELETE）
- [ ] SECRET_KEY 已生成且长度 ≥ 32 字符
- [ ] （可选）OLLAMA_BASE_URL 已配置（如需 AI 功能）

部署后验证：

- [ ] 应用成功启动（无 CrashLoopBackOff）
- [ ] 首页可访问（HTTP 200）
- [ ] 可以登录 admin/admin123
- [ ] 数据库操作正常（创建课程等）
- [ ] 文件上传功能正常
- [ ] （可选）AI 助手功能正常

---

**最后更新**: 2026-04-04  
**适用版本**: 修复后的生产就绪版本
