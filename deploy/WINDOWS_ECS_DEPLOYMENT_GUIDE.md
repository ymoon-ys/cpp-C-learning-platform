# 🖥️ C语言学习平台 - Windows ECS 部署完整指南

> **适用系统**：Windows Server 2022（阿里云 ECS）
>
> **你的服务器信息**：
>
> - 实例名：`iZx7xl1jm9j79Z`
> - 公网 IP：`47.97.204.90`
> - 系统：Windows Server 2022 数据中心版 64位
> - 配置：2核(vCPU) 4G内存
>
> **预计总耗时**：40-60 分钟

***

## 📋 你需要完成的所有步骤（共 20 步）

### 🔴 第一部分：RDS 数据库配置（6步）- 先做这个！

- [ ] **步骤 1**: 进入 RDS 控制台并创建 MySQL 实例
- [ ] **步骤 2**: 创建数据库账号和密码
- [ ] **步骤 3**: 创建 learning\_platform 数据库
- [ ] **步骤 4**: 配置 IP 白名单（允许 Windows ECS 连接）
- [ ] **步骤 5**: 获取数据库连接地址（内网/外网）
- [ ] **步骤 6**: 测试数据库连接是否成功

### 🟢 第二部分：Windows ECS 配置（8步）- 核心工作

- [ ] **步骤 7**: 重置 ECS 登录密码（获取远程桌面密码）
- [ ] **步骤 8**: 远程桌面连接到 Windows ECS
- [ ] **步骤 9**: 安装 Python 3.11（从官网下载）
- [ ] **步骤 10**: 安装 Git 和代码克隆工具
- [ ] **步骤 11**: 克隆项目代码到服务器
- [ ] **步骤 12**: 创建 Python 虚拟环境并安装依赖
- [ ] **步骤 13**: 配置 .env.production 环境变量文件
- [ ] **步骤 14**: 初始化数据库（自动建表+默认数据）

### 🔵 第三部分：启动服务与验证（6步）- 最后检查

- [ ] **步骤 15**: 启动 Flask 应用服务（使用 Waitress）
- [ ] **步骤 16**: 安装并配置 Nginx 反向代理
- [ ] **步骤 17**: 浏览器访问测试（公网 IP）
- [ ] **步骤 18**: 管理员登录测试（admin/admin123）
- [ ] **步骤 19**: AI 助手功能测试（通义千问）
- [ ] **步骤 20**: 🎉 **部署完成！记录访问信息**

***

## 🔴 第一部分：RDS MySQL 数据库配置（预计 15 分钟）

***

### ✅ 步骤 1：进入 RDS 控制台并创建 MySQL 实例（⏱️ 5 分钟）

#### 操作路径：

```
阿里云控制台首页 → 搜索"RDS" → 点击"云数据库 RDS版"
→ 选择"MySQL" → 点击"立即购买"或"免费试用"
```

#### 选择实例配置（推荐）：

| 配置项       | 推荐选择             | 说明              |
| --------- | ---------------- | --------------- |
| **计费方式**  | `包年包月` 或 `按量付费`  | 免费试用选包年包月       |
| **地域**    | `华东1（杭州）`        | ⚠️ 必须与 ECS 同地域！ |
| **可用区**   | `可用区 H`          | 与 ECS 尽量同可用区    |
| **数据库引擎** | `MySQL`          | <br />          |
| **版本**    | `8.0`（推荐）或 `5.7` | 8.0 更新更安全       |
| **产品系列**  | `基础版`            | 免费额度内           |
| **节点规格**  | `1核2G` 或 `2核4G`  | 根据免费额度选择        |
| **存储空间**  | `20GB` 或 `50GB`  | 够用即可            |
| **网络类型**  | `专有网络（VPC）`      | 默认即可            |

#### ⚠️ 重要提示：

1. **地域必须选"华东1（杭州）"**，因为你的 ECS 在杭州！
2. 如果看到"VPC 网络"选项，**尽量选择与 ECS 相同的 VPC**（如果不知道就保持默认）
3. **确认订单**，如果是免费试用应该显示 ¥0 或很低的费用

**等待实例创建完成**（通常 3-10 分钟）

**验证创建成功**：

- [ ] 在 RDS 实例列表中能看到新创建的实例
- [ ] 状态显示为"运行中"（不是"创建中"）

**📝 记录实例 ID**：

```
实例 ID：________________（例如：rm-bp1d721f394）
```

**完成后在此打勾**：\[ √]

***

### ✅ 步骤 2：创建数据库账号和密码（⏱️ 2 分钟）

#### 操作路径：

```
RDS 控制台 → 左侧菜单"账号管理" → 点击"创建账号"
```

#### 填写表单：

| 字段        | 填写内容             | 示例值      |
| --------- | ---------------- | -------- |
| **数据库账号** | `clearning_user` | 或自定义     |
| **账号类型**  | `普通账号`           | 不要选高权限账号 |
| **密码**    | `你自己设的强密码`       | 见下方要求    |
| **确认密码**  | `再次输入相同密码`       | <br />   |

**密码要求**（阿里云强制）：

- ✅ 长度 8-32 个字符
- ✅ 包含至少 3 种：大写字母、小写字母、数字、特殊字符
- ✅ 示例：`Glm4H5q@2026!Secure`
- ❌ 不能包含用户名
- ❌ 不能是常见弱密码

**点击"确定"**

**📝 请务必记录**（后续要用！）：

```
用户名：clearning_user
密码：________________（请妥善保存！）
```

**完成后在此打勾**：\[ √]

***

### ✅ 步骤 3：创建 learning\_platform 数据库（⏱️ 1 分钟）

#### 操作路径：

```
RDS 控制台 → 左侧菜单"数据库管理" → 点击"创建数据库"
```

#### 填写表单：

| 字段        | 填写内容                        | 说明          |
| --------- | --------------------------- | ----------- |
| **数据库名称** | `learning_platform`         | ⚠️ 必须是这个名称！ |
| **支持字符集** | `utf8mb4`                   | 支持中文和 emoji |
| **授权账号**  | 勾选步骤 2 创建的 `clearning_user` | 授予该账号权限     |

**点击"确定"**

**验证创建成功**：

- [ ] 在"数据库管理"列表中能看到 `learning_platform`
- [ ] 状态显示正常

**完成后在此打勾**：\[ √]

***

### ✅ 步骤 4：配置 IP 白名单（⏱️ 3 分钟）⭐ 关键！

**这一步决定你的 Windows ECS 能否连接到 RDS！**

#### 操作路径：

```
RDS 控制台 → 左侧菜单"数据安全性" → "白名单设置" → 点击"修改"
```

#### 添加白名单规则：

**方案 A：测试阶段（推荐新手）**

| 组名      | IP 地址       | 说明               |
| ------- | ----------- | ---------------- |
| default | `0.0.0.0/0` | 允许所有 IP 访问（仅测试用） |

**方案 B：生产环境（更安全）**

| 组名         | IP 地址             | 说明           |
| ---------- | ----------------- | ------------ |
| ecs-access | `47.97.204.90/32` | 只允许你的 ECS 连接 |

**点击"确定"保存**

**验证白名单生效**：

- [ ] 白名单列表中新增了刚才添加的组
- [ ] 状态显示"正常"

**完成后在此打勾**：\[√ ]

***

### ✅ 步骤 5：获取数据库连接地址（⏱️ 2 分钟）

#### 操作路径：

```
RDS 控制台 → 点击你创建的实例名称 → 查看"基本信息"区域
```

#### 找到并记录以下信息：

| 信息项        | 在哪里找                 | 示例值                              | 你的值                |
| ---------- | -------------------- | -------------------------------- | ------------------ |
| **① 内网地址** | "网络信息"→"内网地址"        | `rm-xxxx.mysql.rds.aliyuncs.com` | `________________` |
| **② 外网地址** | "网络信息"→"外网地址"（需单独申请） | `rm-xxxx.mysql.rds.aliyuncs.com` | `________________` |
| **③ 端口号**  | "端口"                 | `3306`                           | `3306`             |

**💡 重要说明**：

- **如果 ECS 和 RDS 在同一 VPC** → 使用**内网地址**（更快更安全）
- **如果不在同一 VPC 或不确定** → 使用**外网地址**（需要在控制台申请开通外网访问）

**如何申请外网地址**（如果需要）：

```
实例详情页 → "连接信息"区域 → 点击"申请外网地址"
→ 确认申请 → 等待几分钟生成
```

**📝 最终确定的连接信息**：

```
MYSQL_HOST=________________（内网或外网地址）
MYSQL_PORT=3306
MYSQL_USER=clearning_user
MYSQL_PASSWORD=________________（步骤 2 设置的）
MYSQL_DATABASE=learning_platform
```

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 6：测试数据库连接（可选，⏱️ 2 分钟）

**如果你想在本地电脑先测试一下 RDS 是否能连上**：

#### 方法 A：使用 Navicat / DBeaver 等 GUI 工具（推荐）

1. 打开 Navicat 或 DBeaver
2. 新建 MySQL 连接
3. 填入步骤 5 的连接信息
4. 点击"测试连接"

**如果连接成功** → ✅ RDS 配置正确！

**如果失败**：

- ❌ "Can't connect" → 检查白名单（步骤 4）
- ❌ "Access denied" → 检查用户名密码（步骤 2）
- ❌ "Unknown database" → 检查数据库名（步骤 3）

#### 方法 B：在本地命令行测试（如果有 MySQL 客户端）

```bash
mysql -h <RDS地址> -P 3306 -u clearning_user -p
# 输入密码后如果能进入 MySQL 提示符 = 成功
```

**此步骤可选，可以跳过，直接进行第二部分**

**完成后在此打勾**：\[ ]

***

## 🟢 第二部分：Windows ECS 服务器配置（预计 20-25 分钟）

***

### ✅ 步骤 7：重置 ECS 登录密码（⏱️ 2 分钟）

**你需要设置一个密码才能通过远程桌面连接到 Windows ECS**

#### 操作路径：

```
ECS 控制台 → 实例列表 → 点击实例 iZx7xl1jm9j79Z
→ 点击"更多" → "密码/密钥" → "重置实例密码"
```

#### 设置新密码：

| 要求  | 说明                    |
| --- | --------------------- |
| 长度  | 8-30 个字符              |
| 复杂度 | 包含大写、小写、数字、特殊字符中的 3 种 |
| 示例  | `Ecs@Win2026!Secure`  |

**点击"提交"并确认重启实例**

**等待重启完成**（约 1-2 分钟）

**📝 务必记录密码**：

```
Windows 远程登录密码：________________（请妥善保存！）
```

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 8：远程桌面连接到 Windows ECS（⏱️ 3 分钟）

#### 方法 A：使用阿里云控制台的 VNC 连接（推荐首次使用）

```
ECS 控制台 → 实例详情 → 右侧"远程连接" → 点击"VNC连接"
→ 立即登录 → 输入步骤 7 的密码 → 点击"确定"
```

**优点**：无需额外软件，直接在浏览器操作

#### 方法 B：使用本地电脑的"远程桌面连接"（推荐日常使用）

1. **Windows 用户**：
   - 按 `Win + R` 键
   - 输入 `mstsc` 回车
   - 在弹出的窗口输入：`47.97.204.90`
   - 点击"连接"
   - 输入用户名：`Administrator`
   - 输入密码：（步骤 7 设置的密码）
   - 勾选"记住凭据"（方便以后连接）
   - 点击"确定"
2. **Mac 用户**：
   - 从 App Store 下载"Microsoft Remote Desktop"
   - 添加新的 PC，输入 `47.97.204.90`
   - 输入用户名和密码后连接

**预期结果**：

- ✅ 看到 Windows Server 2022 桌面
- ✅ 可以打开"服务器管理器"等系统工具

**🎉 恭喜！你已经成功进入你的云服务器了！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 9：安装 Python 3.11（⏱️ 5 分钟）

**在远程桌面的 Windows ECS 中执行以下操作：**

#### 方法 A：通过浏览器下载安装（推荐）

1. **打开 Edge 或 Chrome 浏览器**
2. **访问 Python 官网**：<https://www.python.org/downloads/>
3. **下载 Python 3.11.x**（最新稳定版）
   - 点击 "Download Python 3.11.x" 按钮
   - 会自动下载 Windows installer (64-bit)
4. **运行安装程序**：
   - 双击下载的 `.exe` 文件
   - **⚠️ 务必勾选底部的**：
     - ☑️ `Add python.exe to PATH` （非常重要！）
   - 点击 "Install Now" (默认安装)
   - 等待安装完成（约 2-3 分钟）
   - 点击 "Close"
5. **验证安装成功**：

   按 `Win + X` → 选择 "Windows PowerShell (管理员)" 或 "命令提示符"
   ```cmd
   python --version
   # 应该显示: Python 3.11.x

   pip --version
   # 应该显示: pip x.x.x from ...
   ```
   如果能看到版本号 = ✅ 安装成功！

#### 方法 B：使用 winget 命令行安装（快速）

```powershell
# 在 PowerShell 中执行
winget install Python.Python.3.11
```

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 10：安装 Git（⏱️ 2 分钟）

**Git 用于从 GitHub 克隆项目代码**

#### 方法 A：通过 winget 安装（推荐）

```powershell
# 在 PowerShell 中执行
winget install Git.Git
```

**关闭并重新打开 PowerShell** 使 git 生效。

#### 方法 B：手动下载安装

1. 访问 <https://git-scm.com/download/win>
2. 下载 Git for Windows 安装包
3. 运行安装程序，全部默认选项即可
4. 完成后重启 PowerShell

**验证安装**：

```cmd
git --version
# 应该显示: git version 2.x.x
```

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 11：克隆项目代码（⏱️ 2 分钟）

**在 PowerShell 中执行**：

```powershell
# 进入 D 盘（或 C 盘）
cd D:\

# 克隆项目代码
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git

# 进入项目目录
cd cpp-C-learning-platform

# 查看文件列表
dir
```

**预期输出**（应该看到这些文件夹）：

```
app/
deploy/
static/
Dockerfile
requirements.txt
gunicorn.conf.py
run.py
...
```

**✅ 如果能看到以上文件 = 克隆成功！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 12：创建虚拟环境并安装依赖（⏱️ 5-10 分钟）

**继续在 PowerShell 中执行**（确保在 `D:\cpp-C-learning-platform` 目录下）：

```powershell
# 1. 创建 Python 虚拟环境
python -m venv venv

# 2. 激活虚拟环境
.\venv\Scripts\activate

# 提示符前面出现 (venv) 表示激活成功
# (venv) PS D:\cpp-C-learning-platform>

# 3. 升级 pip 到最新版
python -m pip install --upgrade pip

# 4. 安装项目依赖（这步可能需要几分钟）
pip install -r requirements.txt

# 5. 安装 Gunicorn（用于生产环境部署）
pip install gunicorn waitress
```

**Waitress 是什么？**

- Waitress 是一个纯 Python 的 WSGI 服务器
- 适合在 Windows 上运行 Flask/Django 应用
- 比 Gunicorn 更适合 Windows（Gunicorn 主要为 Unix 设计）

**如果安装过程中遇到错误**：

- ❌ "Permission denied" → 以管理员身份运行 PowerShell
- ❌ "SSL certificate error" → 执行：`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt`
- ❌ 某个包安装失败 → 单独安装：`pip install <包名>`，然后重新执行上面的命令

**验证关键依赖安装成功**：

```powershell
python -c "import flask; print('Flask OK:', flask.__version__)"
python -c "import mysql.connector; print('MySQL OK')"
python -c "import openai; print('OpenAI SDK OK')"
```

**应全部显示 OK**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 13：配置 .env.production 环境变量（⏱️ 3 分钟）⭐⭐⭐ 最关键！

**这是整个部署中最重要的一步！所有连接信息都在这里配置！**

#### 13.1 创建配置文件

```powershell
# 复制模板文件
copy .env.production.example .env.production

# 用记事本打开编辑
notepad .env.production
```

#### 13.2 修改关键配置项（在记事本中）

**找到并修改以下内容**（使用 Ctrl+F 搜索关键字）：

##### ① 修改 SECRET\_KEY（第 14 行左右）

**原始值**：

```
SECRET_KEY=请替换为强随机密钥至少32位
```

**改为**（生成随机字符串）：

在 PowerShell 中执行这个命令来生成：

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

会输出类似：`a1b2c3d4e5f6...`（64位字符）

然后粘贴到配置文件：

```
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

##### ② 修改 MYSQL\_HOST（第 19 行左右）

**原始值**：

```
MYSQL_HOST=你的RDS内网地址或公网地址.rds.aliyuncs.com
```

**改为**（填入步骤 5 获得的地址）：

```
MYSQL_HOST=rm-bp1d721f394.mysql.rds.aliyuncs.com
```

##### ③ 修改 MYSQL\_USER（第 21 行左右）

**原始值**：

```
MYSQL_USER=你的RDS用户名
```

**改为**：

```
MYSQL_USER=clearning_user
```

##### ④ 修改 MYSQL\_PASSWORD（第 22 行左右）

**原始值**：

```
MYSQL_PASSWORD=你的RDS密码
```

**改为**（填入步骤 2 设置的密码）：

```
MYSQL_PASSWORD=Glm4H5q@2026!Secure
```

##### ⑤ 确认其他配置（通常不需要改）

```
MYSQL_PORT=3306                          # ✅ 保持不变
MYSQL_DATABASE=learning_platform         # ✅ 保持不变
AI_PROVIDER=qwen                         # ✅ 保持不变
QWEN_API_KEY=sk-4e93fc91489940afb7ea78f1839ef80f  # ✅ 已预配置
QWEN_MODEL=qwen-turbo                    # ✅ 保持不变
GUNICORN_WORKERS=2                       # ✅ 保持不变
GUNICORN_THREADS=4                       # ✅ 保持不变
```

##### ⑥ 修改 GUNICORN 配置（因为 Windows 不支持 Gunicorn 的 worker 模式）

**找到这部分**（大约在第 48-54 行），**注释掉或删除 GUNICORN 相关行**：

```
# 注释掉以下几行（在每行前面加 # 号）
# GUNICORN_WORKERS=2
# GUNICORN_THREADS=4
# GUNICORN_TIMEOUT=120
```

**或者直接保留也可以**，我们后面会用 Waitress 启动而不是 Gunicorn。

#### 13.3 保存配置文件

在记事本中：

1. 按 `Ctrl + S` 保存
2. 关闭记事本

#### 13.4 验证配置文件内容

```powershell
# 显示关键配置项
Select-String -Path .env.production -Pattern "^(SECRET_KEY|MYSQL_|AI_PROVIDER|QWEN_)"
```

**应显示类似**：

```
SECRET_KEY=a1b2c3...
DB_TYPE=mysql
MYSQL_HOST=rm-bp1d721f394.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=clearning_user
MYSQL_PASSWORD=Glm4H5q@2026!Secure
MYSQL_DATABASE=learning_platform
AI_PROVIDER=qwen
QWEN_API_KEY=sk-4e93fc91489940afb7ea78f1839ef80f
QWEN_MODEL=qwen-turbo
```

**✅ 如果以上都正确 = 配置完成！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 14：初始化数据库（⏱️ 2-3 分钟）

**这一步会自动创建所有数据表和默认用户账号**

#### 14.1 加载环境变量

```powershell
# 确保仍在虚拟环境中（提示符前有 (venv)）
# 如果没有，重新激活
.\venv\Scripts\activate

# 导出环境变量（PowerShell 版本）
Get-Content .env.production | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
```

#### 14.2 初始化数据库

```powershell
# 执行数据库初始化脚本
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ 数据库表创建成功！')
    
    from app.models.user import User
    from werkzeug.security import generate_password_hash
    
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@c-learning.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        teacher = User(
            username='teacher',
            email='teacher@c-learning.com',
            password_hash=generate_password_hash('teacher123'),
            role='teacher',
            is_active=True
        )
        student = User(
            username='student',
            email='student@c-learning.com',
            password_hash=generate_password_hash('student123'),
            role='student',
            is_active=True
        )
        db.session.add_all([admin, teacher, student])
        db.session.commit()
        print('✅ 默认用户创建成功！')
        print('   管理员: admin / admin123')
        print('   教师:   teacher / teacher123')
        print('   学生:   student / student123')
    else:
        print('ℹ️  默认用户已存在，跳过创建')
"
```

**预期输出**：

```
✅ 数据库表创建成功！
✅ 默认用户创建成功！
   管理员: admin / admin123
   教师:   teacher / teacher123
   学生:   student / student123
```

**如果看到错误**：

- ❌ "Can't connect to MySQL server" → 检查步骤 13 的 MYSQL\_HOST 是否正确
- ❌ "Access denied for user" → 检查 MYSQL\_USER 和 MYSQL\_PASSWORD
- ❌ "Unknown database 'learning\_platform'" → 检查 RDS 中是否创建了该数据库（步骤 3）

**✅ 如果显示成功 = 数据库初始化完成！**

**完成后在此打勾**：\[ ]

***

## 🔵 第三部分：启动服务与验证（预计 10-15 分钟）

***

### ✅ 步骤 15：启动 Flask 应用服务（⏱️ 2 分钟）

**现在启动 Web 应用，让它监听 8000 端口！**

#### 15.1 使用 Waitress 启动（推荐 Windows）

```powershell
# 确保在项目根目录且虚拟环境已激活
cd D:\cpp-C-learning-platform
.\venv\Scripts\activate

# 使用 Waitress 启动应用（后台运行）
Start-Process -NoNewWindow -FilePath "waitress-serve" -ArgumentList "--host=0.0.0.0","--port=8000","--threads=4","run:app"
```

**或者前台运行（方便看日志）**：

```powershell
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 run:app
```

**预期输出**：

```
INFO:waitress:Serving on http://0.0.0.0:8000
```

**✅ 看到"Serving on** **<http://0.0.0.0:8000>" = 启动成功！**

#### 15.2 验证本地访问

**打开一个新的 PowerShell 窗口**（不要关闭上面那个）：

```powershell
# 测试应用是否响应
curl http://localhost:8000

# 或者用 Invoke-WebRequest
Invoke-WebRequest -Uri http://localhost:8000 -UseBasicParsing
```

**应返回 HTML 内容（很长的一堆 HTML 代码）**

#### 15.3 配置 Windows 防火墙（允许外部访问 8000 端口）

```powershell
# 以管理员身份运行 PowerShell
# 添加防火墙规则允许 8000 端口
New-NetFirewallRule -DisplayName "C-Learning Platform" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 16：安装并配置 Nginx 反向代理（⏱️ 5 分钟，可选但推荐）

**Nginx 让你可以通过 80 端口（HTTP 默认端口）访问网站，而不需要带 :8000**

#### 16.1 下载并安装 Nginx for Windows

1. **访问 Nginx 官网**：<https://nginx.org/en/download.html>
2. **下载 Stable version**（稳定版）的 `nginx/Windows-x.x.x` 链接
3. **解压到**：`C:\nginx`（或 `D:\nginx`）
4. **目录结构应该是**：
   ```
   D:\nginx\
   ├── conf\
   │   └── nginx.conf
   ├── html\
   ├── logs\
   └── nginx.exe
   ```

#### 16.2 配置 Nginx

**编辑配置文件** `D:\nginx\conf\nginx.conf`（用记事本打开）：

**找到** **`server {`** **部分（大约在第 36 行左右），替换为以下内容**：

```nginx
server {
    listen       80;
    server_name  _;

    # 重定向到 Flask 应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 大文件上传支持
        client_max_body_size 100M;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # 错误页面
    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   html;
    }
}
```

**保存文件**（Ctrl+S）

#### 16.3 启动 Nginx

```powershell
# 进入 Nginx 目录
cd D:\nginx

# 测试配置语法
.\nginx.exe -t

# 应显示:
# nginx: configuration file D:\nginx\conf\nginx.conf test is successful

# 启动 Nginx
Start-Process nginx.exe

# 或者直接双击 nginx.exe
```

#### 16.4 添加防火墙规则（允许 80 端口）

```powershell
# 以管理员身份运行
New-NetFirewallRule -DisplayName "Nginx HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
```

#### 16.5 验证 Nginx 正常工作

```powershell
curl http://localhost:80
# 应该返回与 localhost:8000 相同的内容
```

**✅ 如果 80 端口也能访问 = Nginx 配置成功！**

**如果跳过此步骤**：可以直接通过 `http://47.97.204.90:8000` 访问（不带 Nginx 也完全可以！）

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 17：浏览器访问测试（⏱️ 2 分钟）🎉

**终于到了激动人心的时刻！在你本地电脑的浏览器中打开：**

#### 方式 A：通过 Nginx（80 端口，如果配置了步骤 16）

```
http://47.97.204.90
```

#### 方式 B：直接访问应用（8000 端口，如果没有配置 Nginx）

```
http://47.97.204.90:8000
```

**预期结果**：

- ✅ 看到 **C语言学习平台的登录页面**
- ✅ 页面完整加载（CSS 样式正常、图片显示正常）
- ✅ 有用户名和密码输入框
- ✅ 有"登录"按钮

**如果无法访问**：

| 问题现象            | 可能原因         | 解决方法                                  |
| --------------- | ------------ | ------------------------------------- |
| 浏览器转圈很久         | ECS 安全组未开放端口 | 去 ECS 控制台检查安全组规则                      |
| "无法访问此网站"       | 应用未启动或崩溃     | 回到步骤 15 查看日志                          |
| 页面样式混乱          | 静态资源未正确加载    | 检查 `static/dist` 目录是否存在               |
| 502 Bad Gateway | Nginx 配置问题   | 检查 Nginx 日志 `D:\nginx\logs\error.log` |

**📸 截图留念！这是历史性时刻！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 18：管理员登录测试（⏱️ 1 分钟）

**在登录页面输入**：

| 字段  | 输入内容       |
| --- | ---------- |
| 用户名 | `admin`    |
| 密码  | `admin123` |

**点击"登录"**

**预期结果**：

- ✅ 成功进入**管理后台仪表盘**
- ✅ 左侧显示菜单栏（课程管理、用户管理等）
- ✅ 顶部显示"欢迎, Admin"

**测试其他账号**（可选）：

| 角色 | 用户名       | 密码           |
| -- | --------- | ------------ |
| 教师 | `teacher` | `teacher123` |
| 学生 | `student` | `student123` |

**✅ 所有账号都能正常登录 = 用户认证系统正常！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 19：AI 助手功能测试（⏱️ 2 分钟）⭐ 重点！

**测试通义千问 AI 集成是否正常工作！**

#### 操作步骤：

1. 登录后，在左侧菜单找到 **"AI 助手"** 并点击
2. 在聊天框输入：**"你好，我是C语言初学者，请介绍一下指针"**
3. 点击 **"发送"**

**预期结果**：

- ✅ 几秒后收到回复消息
- ✅ 回复内容专业、详细讲解指针概念
- ✅ 可能包含代码示例并有语法高亮
- ✅ 回复以流式方式逐字显示（不是等很久才一次性出来）

**再测试几个问题**：

| 测试问题                | 预期回复方向        |
| ------------------- | ------------- |
| "帮我写一个 Hello World" | 提供 C 语言代码示例   |
| "数组和指针有什么区别？"       | 对比讲解两者异同      |
| "什么是内存泄漏？如何避免？"     | 解释原因 + 给出最佳实践 |

**如果 AI 无响应或报错**：

| 错误信息                  | 解决方法                                |
| --------------------- | ----------------------------------- |
| "API Key invalid"     | 检查 .env.production 的 QWEN\_API\_KEY |
| "Connection timeout"  | ECS 无法访问外网（阿里云网络限制）                 |
| "Rate limit exceeded" | API 调用太频繁，等 1 分钟再试                  |

**🎉 如果 AI 助手正常工作 = 核心功能验证通过！**

**完成后在此打勾**：\[ ]

***

### ✅ 步骤 20：🎉 部署完成！记录最终信息（⏱️ 1 分钟）

***

## 🎊 恭喜你完成了所有步骤！

### ✅ 最终验收清单

请在下面确认所有核心功能正常：

- [ ] **网站可访问**：通过 `http://47.97.204.90:8000` 或 `http://47.97.204.90` 能打开
- [ ] **管理员可登录**：`admin/admin123` 成功进入后台
- [ ] **AI 助手可用**：通义千问能正常专业回复
- [ ] **核心功能正常**：课程浏览、社区讨论等功能可用
- [ ] **数据持久化**：数据保存在阿里云 RDS MySQL 中

### 📋 部署成功信息汇总卡

```
═══════════════════════════════════════════════════════
🎉 C语言学习平台 - Windows ECS 部署成功！
═══════════════════════════════════════════════════════

【网站访问地址】
  直接访问：http://47.97.204.90:8000
  Nginx代理：http://47.97.204.90（如已配置）

【管理员账号】
  用户名：admin          密码：admin123

【其他测试账号】
  教师账号：teacher      密码：teacher123
  学生账号：student      密码：student123

【服务器信息】
  ECS 公网 IP：47.97.204.90
  系统：Windows Server 2022
  远程桌面：Administrator / <你设置的密码>

【数据库信息】
  RDS 地址：________________
  数据库名：learning_platform
  用户名：clearning_user

【AI 服务】
  通义千问：已集成 ✅
  免费额度：每月100万tokens

【应用服务】
  运行方式：Waitress (Python WSGI)
  监听端口：8000
  项目路径：D:\cpp-C-learning-platform

【常用运维命令】
  查看进程：tasklist | findstr python
  停止服务：taskkill /F /IM python.exe
  启动服务：见步骤 15
  查看日志：D:\cpp-C-learning-platform\logs\

【部署时间】
  日期：2026年____月____日
  总耗时：约 ____ 分钟
═══════════════════════════════════════════════════════
```

### 🚀 下一步优化建议（未来再做）

1. **将应用设置为 Windows 服务**（开机自启）
2. **绑定域名 + 配置 HTTPS**（Let's Encrypt 免费证书）
3. **配置定时任务备份数据库**
4. **设置监控告警**（CPU/内存/磁盘使用率）
5. **开启 CDN 加速静态资源**

### 📞 常见问题速查

| 问题       | 快速解决                                            |
| -------- | ----------------------------------------------- |
| 网站打不开    | 检查 Waitress 进程是否运行：`tasklist \| findstr python` |
| 数据库连不上   | 检查 .env.production 的 RDS 连接信息                   |
| AI 无响应   | 检查网络是否能访问 `dashscope.aliyuncs.com`              |
| 修改代码后不生效 | 重启 Waitress 服务                                  |
| 想更新代码    | `git pull` 然后重启服务                               |

***

## 💡 最后的建议

1. **收藏本文档**：以后维护时参考
2. **定期备份 .env.production**：包含敏感信息
3. **保持远程桌面会话活跃**：或配置为 Windows Service
4. **监控资源使用**：避免超出免费额度
5. **享受成果**：邀请朋友访问你的平台吧！🎉

***

**祝你部署顺利！如有问题随时查看故障排查指南或寻求帮助！** 💪

**最后更新**：2026年04月11日
