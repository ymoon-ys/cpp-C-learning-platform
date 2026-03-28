# 快速部署检查清单

## 部署前准备

### 1. 推送到 GitHub
```bash
# 如果网络允许，执行以下命令
git push origin main
```

### 2. 准备 Railway 环境变量
在 Railway 部署时，需要配置以下环境变量：

**数据库配置**（从 Railway MySQL 服务获取）：
- `MYSQL_HOST` - Railway 会自动提供
- `MYSQL_USER` - Railway 会自动提供  
- `MYSQL_PASSWORD` - Railway 会自动提供
- `MYSQL_DATABASE` - Railway 会自动提供
- `MYSQL_PORT` - 通常是 3306

**应用配置**：
- `SECRET_KEY` - 生成一个随机字符串
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```
- `FLASK_ENV=production`

**AI API Key**（可选，如果需要使用 AI 功能）：
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`

---

## Railway 部署步骤

### 步骤 1：访问 Railway
1. 打开 https://railway.app
2. 点击 **Start with GitHub** 登录
3. 授权访问你的 GitHub 仓库

### 步骤 2：创建 MySQL 数据库
1. 点击 **New Project**
2. 选择 **Provision MySQL**
3. 等待 MySQL 服务启动

### 步骤 3：部署 Flask 应用
1. 在项目中点击 **New** → **GitHub Repo**
2. 选择 `C-learning-platform` 仓库
3. Railway 会自动识别 Dockerfile 并开始构建

### 步骤 4：配置环境变量
1. 点击 Flask 服务
2. 进入 **Variables** 标签
3. 添加环境变量（参考上面的列表）

**快速连接 MySQL：**
- Railway 会自动注入 MySQL 连接变量
- 变量名可能是 `MYSQLHOST` 而不是 `MYSQL_HOST`
- 在 Flask 服务中添加变量引用指向 MySQL 服务

### 步骤 5：生成域名
1. 进入 Flask 服务 → **Settings** → **Networking**
2. 点击 **Generate Domain**
3. 获得 `xxx.railway.app` 域名

### 步骤 6：初始化数据库
1. 点击 MySQL 服务 → **Query**
2. 执行数据库初始化 SQL

---

## 验证部署

1. 访问生成的域名
2. 检查是否能正常访问登录页面
3. 测试注册和登录功能
4. 检查数据库连接是否正常

---

## 故障排查

### 部署失败
- 查看部署日志：点击服务 → **Deployments** → 选择部署 → 查看日志
- 常见错误：
  - 端口错误：确保 `gunicorn.conf.py` 读取 `PORT` 环境变量
  - 依赖错误：检查 `requirements.txt` 是否完整

### 数据库连接失败
- 检查环境变量名称是否正确
- Railway MySQL 可能使用 `MYSQLHOST` 而不是 `MYSQL_HOST`
- 确保 Flask 服务正确引用了 MySQL 服务

### 静态文件不加载
- 检查 `static` 目录是否在 Dockerfile 中正确复制
- 查看浏览器控制台错误信息

---

## 费用说明

- Railway 每月提供 $5 免费额度
- Flask 应用 + MySQL 每月消耗约 $3-4
- 可在 **Usage** 页面查看用量

---

## 安全提示

⚠️ **重要**：
- 不要将 `.env.production` 提交到 Git
- 使用强密码和随机生成的 `SECRET_KEY`
- 定期更新依赖包
- 监控 Railway 用量避免超额

---

## 后续优化

- [ ] 配置自定义域名（可选）
- [ ] 设置 GitHub 自动部署
- [ ] 配置数据库定期备份
- [ ] 设置用量告警
