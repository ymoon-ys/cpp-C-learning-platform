# 🎯 C语言学习平台 - 阿里云部署超细化实操清单

> **当前进度**：✅ RDS MySQL 已创建（实例 ID: rm-bp1d721f394）
>
> **目标**：在 60 分钟内完成全部部署，网站可公网访问
>
> **使用方法**：每完成一项就在前面的 `[ ]` 中打勾 `✅`

---

## 📊 总览：你需要完成的所有步骤（共 25 项）

### 🔴 第一部分：阿里云配置（8项）- 必须先做
- [ ] **步骤 1**: 记录 RDS 连接信息（5个关键数据）
- [ ] **步骤 2**: 创建数据库账号和密码
- [ ] **步骤 3**: 创建 learning_platform 数据库
- [ ] **步骤 4**: 配置 IP 白名单（允许 ECS 连接）
- [ ] **步骤 5**: 创建 ECS 轻量服务器（获取公网 IP）
- [ ] **步骤 6**: 配置 ECS 安全组规则（开放端口）
- [ ] **步骤 7**: 获取 SSH 登录密钥
- [ ] **步骤 8**: 测试 SSH 连接是否成功

### 🟢 第二部分：服务器部署（10项）- 核心工作
- [ ] **步骤 9**: SSH 连接到 ECS 服务器
- [ ] **步骤 10**: 运行一键部署脚本（自动安装 Docker/Nginx/Git）
- [ ] **步骤 11**: 克隆项目代码到服务器
- [ ] **步骤 12**: 创建 .env.production 配置文件
- [ ] **步骤 13**: 填入 RDS 连接信息（关键步骤⭐）
- [ ] **步骤 14**: 填入 AI API Key 和其他配置
- [ ] **步骤 15**: 生成并填入 SECRET_KEY 安全密钥
- [ ] **步骤 16**: 执行 Docker 构建和启动命令
- [ ] **步骤 17**: 等待构建完成（约 5-10 分钟）
- [ ] **步骤 18**: 确认容器运行正常

### 🔵 第三部分：验证测试（7项）- 最后检查
- [ ] **步骤 19**: 浏览器访问测试（输入公网 IP）
- [ ] **步骤 20**: 使用 admin/admin123 登录测试
- [ ] **步骤 21**: 测试 AI 助手功能（发送"你好"）
- [ ] **步骤 22**: 测试课程浏览、社区讨论等功能
- [ ] **步骤 23**: 测试数据持久化（重启后数据不丢）
- [ ] **步骤 24**: 记录最终访问地址和账号信息
- [ ] **步骤 25**: 🎉 **部署完成！**

---

## 🔴 第一部分：阿里云配置（预计 20 分钟）

---

### ✅ 步骤 1：记录 RDS 连接信息（⏱️ 2 分钟）

**你现在看到的界面就是 RDS 控制台**，请找到并记录以下 5 个关键信息：

#### 在 RDS 控制台左侧菜单中：

| 序号 | 信息名称 | 你需要找的位置 | 示例值 | 你的值（请填写） |
|------|---------|---------------|--------|----------------|
| ① | **实例 ID/地址** | 页面顶部"基础信息"区域 | `rm-bp1d721f394.mysql.rds.aliyuncs.com` | `________________` |
| ② | **端口号** | "基础信息"区域 → "端口" | `3306` | `3306` |
| ③ | **用户名** | 左侧菜单 → "账号管理" | `clearning_user` | `________________` |
| ④ | **密码** | 创建账号时设置 | `Glm4H5q@2026!Secure` | `________________` |
| ⑤ | **数据库名** | 左侧菜单 → "数据库管理" | `learning_platform` | `learning_platform` |

**📝 操作提示**：
1. 在截图中我看到你的默认域名是：`clearningdbform.onaliyun.com`
2. 完整的连接地址通常是：`rm-xxxxx.mysql.rds.aliyuncs.com`
3. 如果显示的是内网地址，后面还需要获取外网地址（步骤 4 会用到）

**完成后在此打勾**：[ ]

---

### ✅ 步骤 2：创建数据库账号和密码（⏱️ 3 分钟）

#### 操作路径：
```
RDS 控制台 → 左侧菜单"账号管理" → 点击"创建账号"
```

#### 填写表单：

| 字段 | 填写内容 | 说明 |
|------|---------|------|
| **数据库账号** | `clearning_user` | 或自定义用户名 |
| **账号类型** | `普通账号` | 不要选高权限 |
| **密码** | `你自己设的强密码` | ⚠️ 必须包含大小写字母+数字+特殊字符 |
| **确认密码** | `同上` | 再次输入 |
| **授权数据库** | `learning_platform` | 步骤 3 创建后再授权也可以 |

**密码要求示例**（符合阿里云要求）：
- ✅ `Glm4H5q@2026!Secure` （推荐）
- ✅ `MyRds#Pass2026$Strong`
- ❌ `123456` （太简单，不允许）
- ❌ `password` （太常见）

**📝 请记录你设置的账号信息**：
```
用户名：________________
密码：________________（请妥善保管，后续要用）
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 3：创建 learning_platform 数据库（⏱️ 2 分钟）

#### 操作路径：
```
RDS 控制台 → 左侧菜单"数据库管理" → 点击"创建数据库"
```

#### 填写表单：

| 字段 | 填写内容 | 说明 |
|------|---------|------|
| **数据库名称** | `learning_platform` | ⚠️ 必须是这个名称 |
| **支持字符集** | `utf8mb4` | 支持中文和 emoji |
| **授权账号** | 选择步骤 2 创建的账号 | `clearning_user` |

**点击"确定"创建**

**验证创建成功**：
- [ ] 在"数据库管理"列表中能看到 `learning_platform`
- [ ] 状态显示为"运行中"

**完成后在此打勾**：[ ]

---

### ✅ 步骤 4：配置 IP 白名单（⏱️ 3 分钟）⭐ 关键步骤！

**这一步决定 ECS 能否连接到 RDS，非常重要！**

#### 操作路径：
```
RDS 控制台 → 左侧菜单"数据安全性" → "白名单设置" → 点击"修改"
```

#### 方案 A：测试阶段（推荐新手）

添加以下 IP 到白名单：

| 组名 | IP 地址 | 说明 |
|------|---------|------|
| default | `0.0.0.0/0` | 允许所有 IP 访问（测试阶段） |

**⚠️ 警告**：`0.0.0.0/0` 表示允许任何 IP 连接数据库，仅用于测试阶段！部署稳定后要改为具体 IP。

#### 方案 B：生产环境（更安全）

如果你已经知道 ECS 的公网 IP（步骤 5 会获取），则填写：

| 组名 | IP 地址 | 说明 |
|------|---------|------|
| default | `<ECS的公网IP>/32` | 只允许这台服务器连接 |

**示例**：如果 ECS IP 是 `47.97.204.90`，则填写 `47.97.204.90/32`

**点击"确定"保存**

**验证白名单生效**：
- [ ] 截图中显示"白名单数：3 / 1000"（你已经配置了 3 个白名单组）
- [ ] 新增的白名单组状态显示为"正常"

**完成后在此打勾**：[ ]

---

### ✅ 步骤 5：创建 ECS 轻量应用服务器（⏱️ 5-10 分钟）

#### 操作路径：
```
阿里云首页 → 产品搜索"轻量应用服务器" → 点击"立即购买"
```

#### 选择配置（根据免费试用方案）：

| 配置项 | 推荐选择 | 说明 |
|--------|---------|------|
| **地域** | `华东1（杭州）` | 与 RDS 同地域（重要！） |
| **镜像** | `Ubuntu 22.04 LTS` | 稳定版本 |
| **套餐规格** | `2核2G` 或 `2核4G` | 根据免费额度选择 |
| **带宽** | `2-5 Mbps` | 够用即可 |
| **登录方式** | `SSH 密钥对` | 更安全（比密码安全） |
| **购买时长** | `1个月` 或 `3个月` | 根据免费额度 |

#### 创建 SSH 密钥对（如果还没有）：

1. 点击"创建密钥对"
2. 密钥对名称：`ecs-deploy-key`（或自定义）
3. **⚠️ 立即下载 `.pem` 私钥文件**（只显示一次！）
4. 保存到电脑的安全位置（如 `C:\Users\18341\Desktop\ecs-key.pem`）

**确认订单并支付 ¥0（免费试用）**

**等待实例启动**（通常 1-3 分钟）

**📝 记录 ECS 信息**：
```
公网 IP 地址：________________（例如：47.97.204.90）
SSH 密钥文件位置：________________（例如：C:\Users\18341\Desktop\ecs-key.pem）
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 6：配置 ECS 安全组规则（⏱️ 2 分钟）

**安全组相当于防火墙，必须开放必要端口才能访问**

#### 操作路径：
```
ECS 控制台 → 实例列表 → 点击你的实例 → "安全组"标签页 → "配置规则" → "手动添加"
```

#### 添加入方向规则（共 4 条）：

| 序号 | 协议类型 | 端口范围 | 授权对象 | 说明 |
|------|---------|---------|---------|------|
| 1 | TCP | `22/22` | `0.0.0.0/0` | SSH 远程登录 |
| 2 | TCP | `80/80` | `0.0.0.0/0` | HTTP 网站访问 |
| 3 | TCP | `443/443` | `0.0.0.0/0` | HTTPS 加密访问（可选） |
| 4 | TCP | `8000/8000` | `0.0.0.0/0` | 应用直接访问端口 |

**逐条添加并保存**

**验证规则生效**：
- [ ] 安全组列表中显示这 4 条规则
- [ ] 状态均为"已启用"

**完成后在此打勾**：[ ]

---

### ✅ 步骤 7：获取 SSH 登录凭证（⏱️ 1 分钟）

确保你拥有以下两项之一：

#### 方式 A：SSH 密钥对（推荐，步骤 5 已创建）

```bash
# Windows PowerShell 或 Git Bash 中使用
ssh -i C:\Users\18341\Desktop\ecs-key.pem root@<你的ECS公网IP>
```

#### 方式 B：重置密码登录（备选）

1. ECS 控制台 → 实例详情 → "重置密码"
2. 设置新密码（如：`Ecs@Root2026!Secure`）
3. 重启实例使密码生效

**📝 确认凭证可用**：
```
登录方式：□ SSH密钥对  □ 密码登录
密钥文件路径/密码：________________
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 8：测试 SSH 连接（⏱️ 2 分钟）

**在本地电脑打开 PowerShell 或 Git Bash，执行**：

```bash
ssh -i C:\Users\18341\Desktop\ecs-key.pem root@<你的ECS公网IP>
```

**预期输出**：
```
The authenticity of host '47.97.204.90' can't be established.
ED25519 key fingerprint is SHA256:xxxxxx...
Are you sure you want to continue connecting (yes/no)?
```

**操作**：
1. 输入 `yes` 回车
2. 看到 `root@ecs-xxxx:~#` 提示符 = ✅ 连接成功！

**测试基本命令**：
```bash
# 查看 Ubuntu 版本
lsb_release -a
# 应该显示：Ubuntu 22.04.x LTS

# 查看内存
free -h
# 应该显示：Total 约 2G 或 4G
```

**如果连接失败**：
- ❌ "Permission denied" → 检查密钥文件路径是否正确
- ❌ "Connection refused" → 检查安全组是否开放 22 端口
- ❌ "Timeout" → 检查 ECS 实例是否正在运行

**完成后在此打勾**：[ ]

---

## 🟢 第二部分：服务器部署（预计 15-20 分钟）

---

### ✅ 步骤 9：SSH 连接到 ECS 服务器（⏱️ 1 分钟）

**如果你还在步骤 8 的 SSH 会话中，跳过此步。否则重新连接**：

```bash
ssh -i C:\Users\18341\Desktop\ecs-key.pem root@<ECS公网IP>
```

**确认看到提示符**：`root@ecs-xxxx:~#`

**完成后在此打勾**：[ ]

---

### ✅ 步骤 10：运行一键部署脚本（⏱️ 5-10 分钟）⭐ 最重要的一步！

**我已经为你准备好了完整的自动化脚本，只需复制粘贴执行**：

#### 方法 A：完整自动化（推荐⭐）

**在 SSH 终端中依次执行以下命令**：

```bash
# 1️⃣ 进入 /opt 目录
cd /opt

# 2️⃣ 克隆项目代码（约 30 秒）
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git

# 3️⃣ 进入项目目录
cd cpp-C-learning-platform

# 4️⃣ 给脚本执行权限
chmod +x deploy/alibaba-cloud-deploy.sh

# 5️⃣ 运行一键部署脚本（会自动安装所有软件并配置环境）
sudo ./deploy/alibaba-cloud-deploy.sh
```

**脚本执行过程中会显示**：
```
🚀 开始部署 C语言学习平台到阿里云 ECS...

===== 步骤 1/6: 更新系统包 =====
Get:1 http://archive.ubuntu.com/ubuntu jammy InRelease ...
✅ 系统包更新完成

===== 步骤 2/6: 安装 Docker 和工具 =====
Setting up docker.io ...
✅ Docker 和工具安装完成

... (中间过程省略) ...

===== 步骤 6/6: 构建并启动应用 =====
Building web
Step 1/XX : FROM node:18-alpine as frontend-build
...
Successfully built abc123def456

========================================
CONTAINER ID   IMAGE                          STATUS         PORTS                    NAMES
abc123def456   cpp-c-learning-platform_web    Up 2 minutes   0.0.0.0:8000->8000/tcp   c-learning-web
========================================

===== 配置 Nginx 反向代理 =====
nginx: configuration file /etc/nginx/nginx.conf test is successful
✅ Nginx 配置完成

========================================
🎉 部署完成！
========================================
```

**如果脚本在第 5 步停止并报错**（因为还没创建 .env.production），这是正常的！继续执行步骤 11-15。

**完成后在此打勾**：[ ]

---

### ✅ 步骤 11：克隆项目代码（如果步骤 10 未执行）（⏱️ 1 分钟）

```bash
cd /opt
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git
cd cpp-C-learning-platform
```

**验证克隆成功**：
```bash
ls -la
# 应该看到：app/ deploy/ Dockerfile docker-compose.production.yml 等
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 12：创建 .env.production 配置文件（⏱️ 1 分钟）

```bash
# 从模板复制
cp .env.production.example .env.production

# 编辑配置文件
nano .env.production
```

**你会看到一个类似这样的文件**（部分内容省略）：
```bash
FLASK_ENV=production
SECRET_KEY=请替换为强随机密钥至少32位
DB_TYPE=mysql
MYSQL_HOST=你的RDS内网地址或公网地址.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=你的RDS用户名
MYSQL_PASSWORD=你的RDS密码
MYSQL_DATABASE=learning_platform
AI_PROVIDER=qwen
QWEN_API_KEY=sk-你的通义千问API密钥
QWEN_MODEL=qwen-turbo
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 13：填入 RDS 连接信息（⏱️ 2 分钟）⭐⭐⭐ 最关键！

**在 nano 编辑器中，修改以下 5 行**（使用键盘上下键移动光标）：

#### ① 修改 MYSQL_HOST（第 18 行左右）

**原始值**：
```bash
MYSQL_HOST=你的RDS内网地址或公网地址.rds.aliyuncs.com
```

**改为**（填入你在步骤 1 记录的地址）：
```bash
MYSQL_HOST=rm-bp1d721f394.mysql.rds.aliyuncs.com
```

> 💡 **提示**：如果你的 RDS 和 ECS 不在同一 VPC，可能需要使用**外网地址**
> 外网地址格式通常也是 `rm-xxxxx.mysql.rds.aliyuncs.com`
> 可以在 RDS 控制台 → 实例详情 → "数据库连接" 中查看

#### ② 修改 MYSQL_USER（第 20 行左右）

**原始值**：
```bash
MYSQL_USER=你的RDS用户名
```

**改为**（填入步骤 2 创建的用户名）：
```bash
MYSQL_USER=clearning_user
```

#### ③ 修改 MYSQL_PASSWORD（第 21 行左右）

**原始值**：
```bash
MYSQL_PASSWORD=你的RDS密码
```

**改为**（填入步骤 2 设置的密码）：
```bash
MYSQL_PASSWORD=Glm4H5q@2026!Secure
```

#### ④ 确认 MYSQL_DATABASE（第 22 行左右）

**应该已经是**：
```bash
MYSQL_DATABASE=learning_platform
```

✅ 如果是就不用改。

#### ⑤ 确认 MYSQL_PORT（第 19 行左右）

**应该已经是**：
```bash
MYSQL_PORT=3306
```

✅ 如果是就不用改。

**保存退出 nano 编辑器**：
1. 按 `Ctrl + O`（字母O，不是零）
2. 按 `Enter` 确认保存
3. 按 `Ctrl + X` 退出编辑器

**验证修改成功**：
```bash
grep -E "MYSQL_(HOST|USER|PASSWORD|DATABASE)" .env.production
```

**应显示**：
```
MYSQL_HOST=rm-bp1d721f394.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=clearning_user
MYSQL_PASSWORD=Glm4H5q@2026!Secure
MYSQL_DATABASE=learning_platform
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 14：填入 AI API Key 和其他配置（⏱️ 1 分钟）

**再次编辑配置文件**：
```bash
nano .env.production
```

#### 修改 QWEN_API_KEY（第 38 行左右）

**原始值**：
```bash
QWEN_API_KEY=sk-你的通义千问API密钥
```

**改为**（我已为你配置好）：
```bash
QWEN_API_KEY=sk-4e93fc91489940afb7ea78f1839ef80f
```

#### 确认以下配置保持默认（无需修改）：

```bash
AI_PROVIDER=qwen                    # ✅ 保持不变
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # ✅ 保持不变
QWEN_MODEL=qwen-turbo               # ✅ 保持不变
QWEN_TIMEOUT=120                    # ✅ 保持不变
GUNICORN_WORKERS=2                  # ✅ 保持不变
GUNICORN_THREADS=4                  # ✅ 保持不变
```

**保存退出**（Ctrl+O → Enter → Ctrl+X）

**完成后在此打勾**：[ ]

---

### ✅ 步骤 15：生成 SECRET_KEY 安全密钥（⏱️ 1 分钟）

**这个密钥用于加密用户的 Session Cookie，必须是一个随机字符串！**

#### 方法：自动生成（推荐）

**在 SSH 终端执行**：
```bash
# 生成随机密钥并直接写入配置文件
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env.production

# 验证是否替换成功
grep "SECRET_KEY=" .env.production
```

**应显示类似**：
```bash
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

✅ 这是一串 64 位的十六进制随机字符串，非常安全！

**完成后在此打勾**：[ ]

---

### ✅ 步骤 16：执行 Docker 构建和启动（⏱️ 5-10 分钟）⭐

**现在开始构建 Docker 镜像并启动容器**：

#### 如果之前运行了一键脚本但中途停止：

```bash
# 重新运行部署脚本（这次不会停止了）
sudo ./deploy/alibaba-cloud-deploy.sh
```

#### 如果是全新部署（未运行过脚本）：

```bash
# 使用生产环境配置启动 Docker Compose
docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
```

**你会看到大量构建日志**（首次构建需要下载依赖，耗时较长）：

```
Building web
[+] Building 85.2s (25/25) DONE
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.21kB
 => [internal] load .dockerignore
 => => transferring context: 2.50kB
 => [frontend-build 1/8] FROM node:18-alpine
 => => resolve docker.io/library/node:18-alpine@sha256:xxx
 => [frontend-build 2/8] WORKDIR /app/frontend
 => [frontend-build 3/8] COPY package.json package-lock.json ./
 => [frontend-build 4/8] RUN npm ci --prefer-offline
 ... (中间省略几十行) ...
 => exporting to image
 => => exporting layers
 => => writing image sha256:abc123def456
 => => naming to docker.io/library/cpp-c-learning-platform_web:latest

Use 'docker scan' to run vulnerability analysis.

[+] Running 1/1
 ✔ Container c-learning-web  Started
```

**✅ 看到 "Container c-learning-web Started" = 构建成功！**

**如果构建失败**：
- ❌ "Cannot connect to the Docker daemon" → 执行 `systemctl start docker`
- ❌ "OOM killed"（内存不足）→ ECS 规格太小，考虑升级到 2核4G
- ❌ "pip install failed" → 网络问题，重试一次

**完成后在此打勾**：[ ]

---

### ✅ 步骤 17：等待并监控启动过程（⏱️ 2-3 分钟）

**容器启动后，查看实时日志确认应用正常运行**：

```bash
# 查看最新 100 行日志
docker logs --tail 100 c-learning-web

# 或者持续跟踪日志（按 Ctrl+C 退出）
docker logs -f c-learning-web
```

**预期看到的关键信息**：

```
* Serving Flask app 'run'
* Debug mode: off
* WARNING: This is a development server. Do not use it in a production deployment.
* Running on http://0.0.0.0:8000 (Press CTRL+C to quit)
* [INFO] Starting gunicorn 21.x.x
* [INFO] Listening at: http://0.0.0.0:8000 (x)
* [INFO] Using worker: sync
* [INFO] Booting worker with pid: xxx
* [INFO] Booting worker with pid: yyy
```

**✅ 看到 "Running on http://0.0.0.0:8000" = 应用启动成功！**

**如果看到数据库错误**：
- ❌ "Can't connect to MySQL server" → 检查步骤 13 的 MYSQL_HOST 是否正确
- ❌ "Access denied for user" → 检查步骤 13 的 MYSQL_USER/PASSWORD 是否正确
- ❌ "Unknown database" → 检查步骤 3 是否创建了 learning_platform 数据库

**修复后重启容器**：
```bash
docker-compose restart
```

**完成后在此打勾**：[ ]

---

### ✅ 步骤 18：确认容器运行状态（⏱️ 1 分钟）

```bash
# 查看容器状态
docker ps

# 应该看到类似输出：
# CONTAINER ID   IMAGE                          STATUS         PORTS                    NAMES
# abc123def456   cpp-c-learning-platform_web    Up 5 minutes   0.0.0.0:8000->8000/tcp   c-learning-web
```

**检查要点**：
- [ ] STATUS 显示 `Up X minutes`（运行中）
- [ ] PORTS 显示 `0.0.0.0:8000->8000/tcp`（端口映射正确）
- [ ] NAMES 显示 `c-learning-web`（容器名称正确）

**同时检查 Nginx 状态**：
```bash
systemctl status nginx
# 应该显示: active (running)
```

**测试内部访问**（在 ECS 上用 curl 测试）：
```bash
curl -I http://localhost:8000
# 应该返回: HTTP/1.1 200 OK

curl -I http://localhost:80
# 应该返回: HTTP/1.1 200 OK（通过 Nginx 代理）
```

**✅ 全部正常 = 服务端部署完成！**

**完成后在此打勾**：[ ]

---

## 🔵 第三部分：验证测试（预计 10 分钟）

---

### ✅ 步骤 19：浏览器访问测试（⏱️ 2 分钟）

**在你本地电脑的浏览器中打开**：

#### 方式 A：直接访问应用端口（推荐先测这个）

```
http://<你的ECS公网IP>:8000
```

**示例**：`http://47.97.204.90:8000`

#### 方式 B：通过 Nginx 代理访问（80 端口）

```
http://<你的ECS公网IP>
```

**示例**：`http://47.97.204.90`

**预期结果**：
- ✅ 看到 C语言学习平台的**登录页面**
- ✅ 页面正常加载，有用户名/密码输入框
- ✅ 页面标题显示"C语言学习平台"或类似文字

**如果无法访问**：
- ❌ 浏览器转圈很久 → 检查 ECS 安全组是否开放 8000 端口（步骤 6）
- ❌ "无法访问此网站" → 检查容器是否在运行（步骤 18）
- ❌ 502 Bad Gateway → Nginx 配置有问题，查看日志：`tail -f /var/log/nginx/error.log`

**截图保存**：📸 建议截一张图作为纪念！

**完成后在此打勾**：[ ]

---

### ✅ 步骤 20：管理员登录测试（⏱️ 1 分钟）

**在登录页面输入**：

| 字段 | 输入内容 |
|------|---------|
| 用户名 | `admin` |
| 密码 | `admin123` |

**点击"登录"按钮**

**预期结果**：
- ✅ 成功进入**后台管理仪表盘**
- ✅ 可以看到左侧菜单栏（课程管理、用户管理等）
- ✅ 页面顶部显示"欢迎, Admin"

**尝试其他账号登录**（可选测试）：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 教师 | `teacher` | `teacher123` |
| 学生 | `student` | `student123` |

**完成后在此打勾**：[ ]

---

### ✅ 步骤 21：AI 助手功能测试（⏱️ 2 分钟）⭐ 重点功能！

**这是你最关心的通义千问 AI 集成测试！**

#### 操作步骤：

1. 登录后，在左侧菜单找到 **"AI 助手"** 并点击
2. 在聊天框输入测试消息：**"你好，我是C语言初学者"**
3. 点击 **"发送"** 按钮

**预期结果**：
- ✅ 几秒后收到回复消息
- ✅ 回复内容专业，与 C/C++ 教学相关
- ✅ 回复以**流式方式**显示（逐字出现，而不是等很久才一次性显示）
- ✅ 如果回复中有代码，代码会有**语法高亮**（不同颜色）

**测试更多问题**（可选）：

| 测试问题 | 预期回复方向 |
|---------|------------|
| "什么是指针？" | 解释指针概念，举例说明 |
| "如何写 Hello World？" | 提供完整代码示例 |
| "数组和指针有什么区别？" | 对比讲解两者异同 |
| "帮我解释一下这段代码的错误" | 分析错误原因并给出修正建议 |

**如果 AI 无响应**：
- ❌ 发送后无反应 → 检查网络连接（ECS 需要能访问外网）
- ❌ 报错"API Key invalid" → 检查步骤 14 的 QWEN_API_KEY
- ❌ 回复很慢 → 正常现象，首次调用可能需要 3-5 秒

**🎉 如果 AI 助手正常工作 = 核心功能验证通过！**

**完成后在此打勾**：[ ]

---

### ✅ 步骤 22：核心功能快速测试（⏱️ 3 分钟）

**逐一测试以下功能模块**：

#### ① 课程浏览功能（1 分钟）

1. 点击左侧菜单 **"课程中心"** 或 **"课程浏览"**
2. 应该显示课程列表页面
3. 点击某个课程查看详情
4. ✅ 课程内容正常显示

#### ② 编程练习功能（1 分钟）

1. 点击左侧菜单 **"编程练习"**
2. 应该显示练习题目列表
3. ✅ 可以看到练习题目和代码编辑区

#### ③ 社区讨论功能（1 分钟）

1. 点击左侧菜单 **"社区讨论"**
2. 应该显示帖子列表
3. 点击 **"发帖"** 按钮
4. 输入标题："测试帖子" + 内容："这是一条测试消息"
5. 点击 **"发布"**
6. ✅ 帖子发布成功，可以在列表中看到

#### ④ 文件上传功能（可选，30 秒）

1. 找到上传入口（可能在个人资料或某个管理页面）
2. 上传一个小文件（< 1MB 的图片或文本）
3. ✅ 上传成功，可以下载或预览

**测试结果汇总**：
- [ ] 课程浏览：✅ 正常 / ❌ 有问题
- [ ] 编程练习：✅ 正常 / ❌ 有问题
- [ ] 社区发帖：✅ 正常 / ❌ 有问题
- [ ] 文件上传：✅ 正常 / ❌ 有问题 / ⏭️ 未测试

**完成后在此打勾**：[ ]

---

### ✅ 步骤 23：数据持久化验证（⏱️ 2 分钟）

**这一步验证数据是否真的保存在 RDS MySQL 中（而不是丢失）**

#### 操作步骤：

1. **创建一些测试数据**（如果在步骤 22 中已经发过帖，可以跳过此步）
   - 在社区再发一条帖子，标题："持久化测试"
   
2. **重启 Docker 容器**（模拟服务器重启）：
   ```bash
   # 在 SSH 终端执行
   docker-compose restart
   ```
   
3. **等待 10 秒**让容器完全重启

4. **刷新浏览器页面**（按 F5 或 Ctrl+F5 强制刷新）

5. **重新登录**（admin/admin123）

6. **回到社区讨论页面**

**预期结果**：
- ✅ 之前发的 **"持久化测试"** 帖子依然存在
- ✅ 所有课程数据、用户数据都还在
- ✅ 数据没有丢失

**✅ 数据持久化验证通过 = 部署真正成功！**

**如果数据丢失**：
- ❌ 数据库连接到了错误的实例 → 检查 .env.production 的 MYSQL_HOST
- ❌ 数据库被重建了 → 检查是否有初始化脚本清空了数据

**完成后在此打勾**：[ ]

---

### ✅ 步骤 24：记录最终信息（⏱️ 1 分钟）

**恭喜你即将完成部署！现在记录所有关键信息以便日后使用**：

#### 📋 部署成功信息汇总卡

```
═══════════════════════════════════════════════════════
🎉 C语言学习平台 - 阿里云部署成功！
═══════════════════════════════════════════════════════

【网站访问地址】
  直接访问：http://________:8000
  Nginx代理：http://________

【管理员账号】
  用户名：admin
  密码：admin123

【其他测试账号】
  教师账号：teacher / teacher123
  学生账号：student / student123

【服务器信息】
  ECS 公网 IP：________
  SSH 登录：ssh -i ________ root@________

【数据库信息】
  RDS 地址：rm-bp1d721f394.mysql.rds.aliyuncs.com
  数据库名：learning_platform
  用户名：clearning_user

【AI 服务】
  通义千问：已集成（每月100万tokens免费额度）
  API Key：sk-4e93fc91489940afb7ea78f1839ef80f

【部署时间】
  日期：2026年____月____日
  耗时：约 ____ 分钟

【常用运维命令】
  查看日志：docker logs -f c-learning-web
  重启服务：docker-compose restart
  停止服务：docker-compose down
  更新代码：git pull && docker-compose up -d --build
═══════════════════════════════════════════════════════
```

**📸 建议**：将以上信息保存到一个文本文件或截图保存！

**完成后在此打勾**：[ ]

---

### ✅ 步骤 25：🎉 部署完成！（⏱️ 0 分钟）

---

## 🎊 恭喜你完成了所有步骤！

### ✅ 最终验收清单

请在下面确认所有核心功能正常：

- [ ] **网站可访问**：通过公网 IP 能打开登录页面
- [ ] **管理员可登录**：admin/admin123 成功进入后台
- [ ] **AI 助手可用**：通义千问能正常回复消息
- [ ] **核心功能正常**：课程、练习、社区均可使用
- [ ] **数据持久化**：重启后数据不丢失
- [ ] **性能达标**：页面加载 < 5 秒

### 🚀 下一步可选优化（未来再做）

1. **绑定域名**（购买域名 → DNS 解析到 ECS IP → 配置 HTTPS）
2. **开启 HTTPS**（Let's Encrypt 免费证书 → 自动续期）
3. **配置监控**（阿里云云监控 → CPU/内存/磁盘告警）
4. **自动备份**（RDS 自动备份策略 → 定时快照）
5. **CDN 加速**（静态资源走 CDN → 提升全球访问速度）

### 📞 遇到问题？

**查看详细故障排查指南**：
👉 [deploy/ALIBABA_CLOUD_DEPLOYMENT_GUIDE.md](./ALIBABA_CLOUD_DEPLOYMENT_GUIDE.md)

**常见快速修复**：
```bash
# 问题：网站打不开
docker-compose restart

# 问题：数据库连不上
# 检查 .env.production 中的 MYSQL_HOST/MYSQL_USER/MYSQL_PASSWORD

# 问题：AI 助手无响应
# 检查网络：curl https://dashscope.aliyuncs.com

# 问题：想更新代码
cd /opt/cpp-C-learning-platform
git pull origin main
docker-compose up -d --build
```

---

## 📊 进度统计

### 你已完成的部分：

- [ ] 第一部分：阿里云配置（8/8 项）
- [ ] 第二部分：服务器部署（10/10 项）
- [ ] 第三部分：验证测试（7/7 项）
- [ ] **总计：25/25 项** ✅

### 预计总耗时：

| 部分 | 预计时间 | 实际用时 |
|------|---------|---------|
| 阿里云配置 | 20 分钟 | _______ 分钟 |
| 服务器部署 | 20 分钟 | _______ 分钟 |
| 验证测试 | 10 分钟 | _______ 分钟 |
| **总计** | **50-70 分钟** | **_______ 分钟** |

---

## 💡 最后的建议

1. **收藏本文件**：以后维护时可以参考
2. **备份 .env.production**：虽然代码在 GitHub，但这个文件包含敏感信息不要提交
3. **定期更新**：每周执行一次 `git pull && docker-compose up -d --build` 获取最新代码
4. **监控资源使用**：关注 ECS 的 CPU 和内存使用率，避免超出免费额度
5. **享受成果**：邀请朋友访问你的 C语言学习平台吧！🎉

---

**祝你部署顺利！如有任何问题，随时查看部署指南或寻求帮助！** 💪

**最后更新时间**：2026年04月11日
