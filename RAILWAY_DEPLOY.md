# Railway 部署指南

## 第一步：准备 GitHub 仓库

1. 确保代码已推送到 GitHub
2. 检查 `.gitignore` 中包含 `.env` 和 `.env.production`
3. 确认以下文件已创建：
   - `Dockerfile`
   - `gunicorn.conf.py`
   - `runtime.txt`

```bash
git add .
git commit -m "添加 Railway 部署配置"
git push origin main
```

---

## 第二步：注册 Railway

1. 访问 https://railway.app
2. 点击 **Start with GitHub**
3. 授权 Railway 访问你的 GitHub 仓库
4. 完成邮箱验证

---

## 第三步：创建项目并添加 MySQL

1. 点击 **New Project**
2. 选择 **Provision MySQL**
3. 等待 MySQL 服务启动完成
4. 点击 MySQL 服务，记录以下信息：
   - `MYSQLHOST` (主机地址)
   - `MYSQLUSER` (用户名)
   - `MYSQLPASSWORD` (密码)
   - `MYSQLDATABASE` (数据库名)
   - `MYSQLPORT` (端口，通常是 3306)

---

## 第四步：部署 Flask 应用

1. 在项目中点击 **New Service**
2. 选择 **GitHub Repo**
3. 选择你的 `C-learning-platform` 仓库
4. Railway 会自动检测 Dockerfile 并开始构建

---

## 第五步：配置环境变量

在 Flask 服务的 **Variables** 标签页添加以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `MYSQL_HOST` | 从 MySQL 服务获取 | 数据库主机 |
| `MYSQL_USER` | 从 MySQL 服务获取 | 数据库用户 |
| `MYSQL_PASSWORD` | 从 MySQL 服务获取 | 数据库密码 |
| `MYSQL_DATABASE` | 从 MySQL 服务获取 | 数据库名 |
| `MYSQL_PORT` | 从 MySQL 服务获取 | 数据库端口 |
| `SECRET_KEY` | 随机字符串 | Flask 密钥 |
| `FLASK_ENV` | production | 生产环境 |
| `GEMINI_API_KEY` | 你的 API Key | AI 功能（可选） |

**快速配置方法：**
1. 点击 MySQL 服务
2. 进入 **Variables** 标签
3. 右键点击变量 → **Reference**
4. 在 Flask 服务中引用这些变量

---

## 第六步：连接数据库服务

1. 进入 Flask 服务设置
2. 找到 **Networking** 或 **Variables**
3. 添加 MySQL 服务的连接：
   - 方式一：使用 Railway 的服务发现（自动）
   - 方式二：手动添加 MySQL 的环境变量引用

---

## 第七步：初始化数据库

Railway 提供了 MySQL 终端，可以执行 SQL：

1. 点击 MySQL 服务
2. 进入 **Query** 标签
3. 执行数据库初始化 SQL（从 `app/mysql_database.py` 中的表结构）

或者使用 Railway CLI：

```bash
railway login
railway link
railway run python -c "from app.mysql_database import MySQLDatabase; import os; db = MySQLDatabase(...); db.init_db()"
```

---

## 第八步：配置域名

1. 进入 Flask 服务
2. 点击 **Settings** → **Networking**
3. 点击 **Generate Domain**
4. 你将获得类似 `xxx.railway.app` 的免费域名

---

## 常见问题

### Q: 部署失败，日志显示端口错误？
A: Railway 会自动设置 `PORT` 环境变量，`gunicorn.conf.py` 已配置读取该变量。

### Q: 数据库连接失败？
A: 确保环境变量名称正确，Railway MySQL 使用的变量名可能与本地不同：
- `MYSQLHOST` 而非 `MYSQL_HOST`
- 检查 Railway MySQL 服务的实际变量名

### Q: 静态文件无法加载？
A: 确保 Dockerfile 中正确复制了 `static` 目录。

### Q: 如何查看日志？
A: 点击服务 → **Deployments** → 选择部署 → 查看日志

---

## 费用监控

1. 点击项目设置 → **Usage**
2. 查看当前用量
3. 免费额度：$5/月，通常足够小型应用

---

## 下一步

- 配置自定义域名（可选）
- 设置自动部署（GitHub 推送自动部署）
- 配置数据库备份
