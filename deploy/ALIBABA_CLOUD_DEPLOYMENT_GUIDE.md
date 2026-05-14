# 🚀 C语言学习平台 - 阿里云免费部署完整指南

> **目标**：在 60 分钟内将 C语言学习平台部署到阿里云免费服务，无需学生认证！
>
> **适用场景**：Sealos DNS 问题无法解决 → 迁移到阿里云 ECS + RDS 方案

---

## 📋 部署前准备清单

- [ ] 手机号（用于注册阿里云账号）
- [ ] 身份证（用于实名认证）
- [ ] GitHub 账号（代码已托管在 https://github.com/ymoon-ys/cpp-C-learning-platform）
- [ ] 通义千问 API Key：`sk-4e93fc91489940afb7ea78f1839ef80f`（已配置）

---

## 🎯 第一阶段：阿里云资源准备（15-20 分钟）

### 步骤 1.1：注册/登录阿里云

1. 访问 **https://www.aliyun.com/**
2. 点击右上角 **"免费试用"** 或 **"登录/注册"**
3. 使用手机号注册新账号（无需学生邮箱）
4. **实名认证**（必须）：
   - 进入控制台后提示实名认证
   - 上传身份证正反面照片
   - 人脸识别验证
   - ⏰ 通常 5-10 分钟内通过

### 步骤 1.2：创建 ECS 轻量应用服务器（推荐免费方案）

#### 方案 A：轻量应用服务器（推荐⭐）

1. 登录控制台 → 搜索 **"轻量应用服务器"**
2. 点击 **"立即购买"**
3. 选择配置：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 地域 | 华东1（杭州） | 离你近延迟低 |
| 镜像 | Ubuntu 22.04 LTS | 稳定版本 |
| 套餐 | 2核2G 或 2核4G | 根据免费额度选择 |
| 带宽 | 2-5 Mbps | 够用即可 |
| 流量包 | 按需选择 | 免费额度内 |
| 登录方式 | SSH 密钥对 | 更安全 |

4. **设置安全组规则**（重要！）：
   - 入方向添加以下规则：
     - `22/tcp` (SSH)
     - `80/tcp` (HTTP)
     - `443/tcp` (HTTPS)
     - `8000/tcp` (应用端口)

5. 确认订单 → 支付 ¥0（免费试用）
6. **记录公网 IP 地址**（例如：`47.97.204.90`）

#### 方案 B：ECS 云服务器

1. 控制台 → 产品 → **云服务器 ECS**
2. 点击 **"免费试用"**
3. 选择 **"ecs.c7.large"** (2核4G) 或类似规格
4. 其余配置同方案 A

### 步骤 1.3：创建 RDS MySQL 数据库（免费试用）

1. 控制台 → 产品 → **云数据库 RDS**
2. 选择 **MySQL** 引擎
3. 点击 **"立即购买"** 或 **"免费试用"**

#### 数据库配置：

| 配置项 | 推荐值 |
|--------|--------|
| 地域 | **与 ECS 相同地域**（关键！） |
| 可用区 | 与 ECS 同可用区（可选） |
| VPC 网络 | 选择 ECS 所在 VPC（或新建） |
| 实例规格 | 基础版 1核2G |
| 存储空间 | 20GB 或 50GB（免费额度内） |
| MySQL 版本 | 8.0（推荐）或 5.7 |

4. **设置白名单**（允许 ECS 连接数据库）：
   - 进入 RDS 实例详情页
   - 左侧菜单 → **数据安全性** → **白名单设置**
   - 添加 ECS 的公网 IP：`0.0.0.0/0`（测试阶段）或具体 IP
   - ✅ 保存

5. **创建数据库和账号**：
   - 左侧菜单 → **账号管理** → **创建账号**
     - 用户名：`clearning_user`
     - 密码：`生成强密码并记录`（如：`Glm4H5q@2026!Secure`）
     - 权限：读写
   - 左侧菜单 → **数据库管理** → **创建数据库**
     - 数据库名：`learning_platform`
     - 授权账号：选择刚创建的账号
     - 字符集：`utf8mb4`

6. **记录连接信息**（后续配置需要）：
   ```
   内网地址: rm-xxxxx.mysql.rds.aliyuncs.com (如果同VPC)
   外网地址: rm-xxxxx.mysql.rds.aliyuncs.com (备选)
   端口: 3306
   用户名: clearning_user
   密码: 你的密码
   数据库: learning_platform
   ```

---

## 🔧 第二阶段：ECS 服务器环境配置（10-15 分钟）

### 步骤 2.1：SSH 连接到 ECS

**Windows 用户（推荐 PowerShell 或 Git Bash）：**

```bash
# 如果使用密钥对登录
ssh -i your-key.pem root@<你的ECS公网IP>

# 示例
ssh -i ~/Downloads/ecs-key.pem root@47.97.204.90
```

**首次连接提示**：
```
The authenticity of host '47.97.204.90' can't be established.
Are you sure you want to continue connecting (yes/no)? yes
```
输入 `yes` 回车即可。

✅ 连接成功标志：看到 `root@ecs-xxxx:~#` 提示符

### 步骤 2.2：运行一键部署脚本（推荐⭐）

我已经为你准备好了完整的一键部署脚本，只需执行以下命令：

```bash
# 克隆项目代码
cd /opt
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git
cd cpp-C-learning-platform

# 给脚本执行权限
chmod +x deploy/alibaba-cloud-deploy.sh

# 执行一键部署脚本
sudo ./deploy/alibaba-cloud-deploy.sh
```

**脚本会自动完成**：
- ✅ 更新系统包
- ✅ 安装 Docker、Nginx、Git、Python3 等
- ✅ 配置防火墙（开放 22/80/443/8000 端口）
- ✅ 克隆最新代码
- ✅ 检查环境配置文件
- ✅ 构建 Docker 镜像并启动容器
- ✅ 配置 Nginx 反向代理

### 步骤 2.3：手动安装（备选方案）

如果不使用一键脚本，手动执行以下命令：

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装必要工具
apt install -y git curl wget nginx python3 python3-pip python3-venv docker.io docker-compose-v2 certbot python3-certbot-nginx

# 3. 启动 Docker
systemctl enable docker && systemctl start docker

# 4. 配置防火墙
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8000/tcp comment 'Application'

# 启用 UFW（交互式确认）
ufw enable
```

---

## 🐳 第三阶段：部署 C语言学习平台（10-15 分钟）

### 步骤 3.1：克隆代码（如果还没做）

```bash
cd /opt || cd /home
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git
cd cpp-C-learning-platform
```

### 步骤 3.2：创建生产环境配置文件（核心步骤⭐）

```bash
# 从模板复制
cp .env.production.example .env.production

# 编辑配置文件
nano .env.production  # 或 vim .env.production
```

**修改以下关键配置项**：

```bash
# ===== 必须修改的部分 =====

# 1. 安全密钥（生成强随机字符串）
SECRET_KEY=你的强随机密钥至少32位字符
# 生成方法: python3 -c "import secrets; print(secrets.token_hex(32))"

# 2. RDS MySQL 连接信息（填入步骤 1.3 记录的信息）
MYSQL_HOST=rm-xxxxx.mysql.rds.aliyuncs.com  # 替换为你的RDS地址
MYSQL_PORT=3306
MYSQL_USER=clearning_user                    # 替换为你的RDS用户名
MYSQL_PASSWORD=你的RDS密码                   # 替换为你的密码
MYSQL_DATABASE=learning_platform

# 3. AI 配置（保持默认即可）
QWEN_API_KEY=sk-4e93fc91489940afb7ea78f1839ef80f  # 已配置好的Key

# ===== 可以保持默认的部分 =====
FLASK_ENV=production
DB_TYPE=mysql
AI_PROVIDER=qwen
QWEN_MODEL=qwen-turbo
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
```

**保存退出**：
- Nano 编辑器：`Ctrl+O` 保存 → `Enter` 确认 → `Ctrl+X` 退出
- Vim 编辑器：按 `Esc` → 输入 `:wq` → 回车

### 步骤 3.3：使用 Docker Compose 部署（推荐）

```bash
# 构建并启动（使用生产环境配置）
docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build

# 查看构建进度（首次构建可能需要 5-10 分钟）
docker-compose -f docker-compose.production.yml logs -f web
```

**预期输出**：
```
Building web
Step 1/XX : FROM node:18-alpine as frontend-build
...
Step XX/XX : CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
Successfully built abc123def456
Successfully tagged cpp-c-learning-platform_web:latest
Creating c-learning-web ... done
```

**验证容器运行状态**：

```bash
docker ps
```

应看到类似输出：
```
CONTAINER ID   IMAGE                          STATUS         PORTS                    NAMES
abc123def456   cpp-c-learning-platform_web    Up 2 minutes   0.0.0.0:8000->8000/tcp   c-learning-web
```

**查看启动日志**（确认无错误）：

```bash
docker logs c-learning-web
```

✅ 成功标志：看到 `Running on http://0.0.0.0:8000`

---

## 🌐 第四阶段：Nginx 反向代理配置（10 分钟）

### 步骤 4.1：配置 Nginx

如果你使用了**一键部署脚本**，此步骤已完成！跳过。

**手动配置**：

```bash
# 复制 Nginx 配置文件
cp deploy/nginx/c-learning.conf /etc/nginx/sites-available/c-learning

# 启用站点
ln -s /etc/nginx/sites-available/c-learning /etc/nginx/sites-enabled/

# 删除默认站点（避免冲突）
rm -f /etc/nginx/sites-enabled/default

# 测试配置语法
nginx -t

# 重启 Nginx
systemctl restart nginx
systemctl enable nginx
```

✅ 成功标志：
```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 步骤 4.2：配置 HTTPS（可选，推荐）

**前提条件**：你有域名并已解析到 ECS 公网 IP

```bash
# 安装 Certbot（Let's Encrypt 免费证书）
apt install -y certbot python3-certbot-nginx

# 申请证书（替换为你的域名）
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 测试自动续期
certbot renew --dry-run
```

✅ 成功标志：
```
Congratulations! You have successfully enabled HTTPS on yourdomain.com
```

---

## ✅ 第五阶段：验证与测试（10 分钟）

### 步骤 5.1：基础功能验证

打开浏览器访问：

- **直接访问**：`http://<ECS公网IP>:8000`
- **通过 Nginx**：`http://<ECS公网IP>` （如果配置了 Nginx）

**预期结果**：
- ✅ 看到 C语言学习平台登录页面
- ✅ 页面正常加载，无报错

**使用默认管理员账号登录**：
- 用户名：`admin`
- 密码：`admin123`

✅ 成功进入后台管理界面！

### 步骤 5.2：核心功能测试

逐项检查以下功能：

| 功能 | 操作 | 预期结果 |
|------|------|----------|
| 课程浏览 | 点击左侧"课程中心" | 显示课程列表 |
| 编程练习 | 点击"编程练习" | 显示练习页面 |
| 社区讨论 | 点击"社区讨论" | 显示帖子列表 |
| 发帖测试 | 在社区发一个测试帖 | 发帖成功并可查看 |
| 文件上传 | 上传一个小文件（<100MB） | 上传成功 |

### 步骤 5.3：AI 助手测试（重点⭐）

1. 点击左侧菜单 **"AI 助手"**
2. 在输入框输入测试消息：**"你好，我是C语言初学者"**
3. 点击发送

**预期结果**：
- ✅ 收到通义千问的专业回复
- ✅ 回复内容包含 C/C++ 教学相关内容
- ✅ 回复以流式方式显示（逐字出现）
- ✅ 代码部分有高亮显示

**测试更多问题**：
- "什么是指针？"
- "如何写一个 Hello World？"
- "解释一下数组和指针的区别"

### 步骤 5.4：数据持久化验证

1. 创建一个测试课程或帖子
2. 重启 Docker 容器：

```bash
docker-compose restart
```

3. 等待 10 秒后重新访问网站
4. 确认刚才创建的数据依然存在

✅ 数据持久化成功！

### 步骤 5.5：性能与安全检查

**性能测试**：
- 首次加载页面：< 5 秒
- 二次加载（有缓存）：< 3 秒

**安全检查**：

```bash
# 检查仅开放了必要端口
ss -tlnp | grep -E ':(22|80|443|8000) '

# 查看 Docker 日志有无 ERROR
docker logs c-learning-web 2>&1 | grep -i error | head -20

# 确认 SSH 仅支持密钥登录
grep "^PasswordAuthentication" /etc/ssh/sshd_config
# 应该显示: PasswordAuthentication no
```

---

## 🎉 部署完成！

### 访问信息汇总

| 项目 | 值 |
|------|-----|
| **直接访问地址** | `http://<ECS公网IP>:8000` |
| **Nginx 代理地址** | `http://<ECS公网IP>` |
| **管理员账号** | admin / admin123 |
| **教师账号** | teacher / teacher123 |
| **学生账号** | student / student123 |

### 常用运维命令

```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs -f c-learning-web

# 重启服务
docker-compose -f docker-compose.production.yml restart

# 停止服务
docker-compose -f docker-compose.production.yml down

# 更新代码并重新部署
cd /opt/cpp-C-learning-platform
git pull origin main
docker-compose -f docker-compose.production.yml up -d --build

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 进入容器内部调试
docker exec -it c-learning-web bash
```

### 故障排查速查表

| 问题现象 | 可能原因 | 解决方案 |
|----------|----------|----------|
| 无法访问 `:8000` | Docker 未启动 | `systemctl start docker` |
| 无法访问 `:80` | Nginx 未启动 | `systemctl start nginx` |
| 数据库连接失败 | RDS 白名单未配置 | 检查 RDS 白名单设置 |
| AI 助手无响应 | API Key 错误 | 检查 `.env.production` 中的 QWEN_API_KEY |
| 页面加载慢 | 首次构建缓存未生效 | 等待 2-3 分钟或重启容器 |
| 文件上传失败 | 文件过大 | 检查 `MAX_CONTENT_LENGTH` 设置（默认100MB） |
| 502 Bad Gateway | 应用未启动 | `docker-compose restart` |

### 下一步优化建议（可选）

1. **域名绑定**：购买域名并解析到 ECS IP，配置 HTTPS
2. **监控告警**：配置阿里云云监控，设置 CPU/内存告警
3. **自动备份**：配置 RDS 自动备份 + 定时快照
4. **CDN 加速**：开启阿里云 CDN 加速静态资源
5. **日志收集**：接入阿里云 SLS 日志服务

---

## 📞 需要帮助？

如果在部署过程中遇到问题：

1. **查看日志**：`docker logs -f c-learning-web`
2. **检查配置**：确认 `.env.production` 所有必填项都已填写
3. **验证网络**：`curl http://localhost:8000` 在 ECS 内部测试
4. **重启服务**：`docker-compose restart` 解决大部分临时问题

---

## ✨ 部署架构图

```
┌─────────────────┐
│   用户浏览器     │
└────────┬────────┘
         │ HTTP/HTTPS
         ▼
┌─────────────────┐
│    Nginx (:80)   │ ← 反向代理 + 静态资源缓存
│  SSL 终结       │
└────────┬────────┘
         │ Proxy Pass
         ▼
┌─────────────────────────────┐
│  Docker Container (:8000)   │
│  ┌───────────────────────┐  │
│  │ Gunicorn WSGI Server │  │
│  │ Flask Application    │  │
│  │ - 用户认证           │  │
│  │ - 课程管理           │  │
│  │ - 编程练习           │  │
│  │ - 社区讨论           │  │
│  │ - AI助手(Qwen)       │  │
│  └───────────────────────┘  │
└──────────────┬──────────────┘
               │ MySQL Protocol
               ▼
┌─────────────────────────────┐
│  Alibaba Cloud RDS MySQL    │
│  Host: rm-xxx.rds.aliyuncs.com │
│  Database: learning_platform │
│  Port: 3306                 │
└─────────────────────────────┘
               │ HTTPS API
               ▼
┌─────────────────────────────┐
│  通义千问 (Qwen-turbo)      │
│  API Endpoint: dashscope    │
│  Free: 100万 tokens/月       │
└─────────────────────────────┘
```

---

**🎊 恭喜！你的 C语言学习平台已成功部署到阿里云！**

现在你可以：
- 通过公网 IP 访问网站
- 使用通义千问 AI 助手进行 C++ 教学
- 邀请他人体验你的平台

**预计总耗时**：55-70 分钟（含实名认证时间）

祝部署顺利！🚀
