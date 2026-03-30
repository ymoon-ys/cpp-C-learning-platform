# Zeabur 部署完整指南

## 快速开始（5 分钟部署）

### 第一步：访问 Zeabur

1. 打开 https://zeabur.com
2. 点击右上角 **登录**
3. 选择 **使用 GitHub 登录**
4. 授权 Zeabur 访问你的 GitHub

---

### 第二步：创建项目

1. 登录后点击 **创建项目**
2. 填写项目名称：`c-learning-platform`
3. 选择区域：**新加坡 (Singapore)** 或 **东京 (Tokyo)**
4. 点击 **创建**

---

### 第三步：添加 MySQL 数据库

1. 在项目中点击 **添加服务**
2. 选择 **数据库** → **MySQL**
3. 等待 MySQL 启动（约 1-2 分钟）
4. 启动后，Zeabur 会自动注入数据库环境变量

---

### 第四步：添加 Flask 应用

1. 点击 **添加服务**
2. 选择 **Git** → **GitHub**
3. 选择 `cpp-C-learning-platform` 仓库
4. Zeabur 会自动检测 Dockerfile
5. 点击 **部署**

---

### 第五步：配置环境变量

1. 点击 Flask 服务
2. 进入 **环境变量** 标签
3. 添加以下变量：

| 变量名 | 值 |
|--------|-----|
| `SECRET_KEY` | 点击下方生成 |
| `FLASK_ENV` | production |

**生成 SECRET_KEY**：
```python
import secrets
print(secrets.token_hex(32))
```

输出示例：`a1b2c3d4e5f6...`（64位随机字符串）

---

### 第六步：连接数据库变量

Zeabur 会自动注入 MySQL 变量，确保你的应用使用：

- `MYSQL_HOST` - 数据库主机
- `MYSQL_PORT` - 端口（3306）
- `MYSQL_USER` - 用户名
- `MYSQL_PASSWORD` - 密码
- `MYSQL_DATABASE` - 数据库名

**重要**：检查你的代码是否使用这些变量名！

---

### 第七步：生成域名

1. 进入 Flask 服务
2. 点击 **网络** 或 **域名** 标签
3. 点击 **生成域名**
4. 获得免费域名：`xxx.zeabur.app`

---

### 第八步：初始化数据库

#### 方法 1：使用 Zeabur 终端

1. 点击 MySQL 服务
2. 进入 **终端** 标签
3. 执行数据库初始化 SQL

#### 方法 2：本地连接初始化

1. 在 Zeabur 获取数据库连接信息
2. 本地使用 MySQL 客户端连接
3. 执行初始化脚本

#### 方法 3：使用 Python 脚本

在 Zeabur 的 Flask 服务终端执行：

```bash
# 进入 Python
python3

# 执行初始化
from app.mysql_database import MySQLDatabase
import os

db = MySQLDatabase(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)
db.init_db()
exit()
```

---

### 第九步：测试访问

1. 浏览器打开你的域名：`https://xxx.zeabur.app`
2. 测试功能：
   - ✅ 访问首页
   - ✅ 用户注册
   - ✅ 用户登录
   - ✅ 课程浏览

---

## 常见问题

### Q: 部署失败，提示构建错误？
**A**: 检查以下几点：
1. Dockerfile 是否正确
2. requirements.txt 是否完整
3. 查看构建日志定位具体错误

### Q: 数据库连接失败？
**A**: 检查：
1. 环境变量名称是否正确
2. MySQL 服务是否已启动
3. Flask 服务是否在同一项目内

### Q: 页面无法访问？
**A**: 检查：
1. 服务是否正常运行
2. 域名是否已生成
3. 查看服务日志

### Q: 静态文件 404？
**A**: 确保：
1. Dockerfile 正确复制 static 目录
2. Nginx/Flask 静态文件路径配置正确

---

## 查看日志

1. 进入 Flask 服务
2. 点击 **日志** 标签
3. 实时查看运行日志

---

## 费用说明

| 项目 | 费用 |
|------|------|
| Web 服务 | **免费** |
| MySQL 数据库 | **免费** |
| 域名 | **免费** |
| SSL 证书 | **免费** |
| **总计** | **¥0/月** |

Zeabur 每月提供 $5 免费额度，足够小型应用使用！

---

## 自动部署

配置完成后，每次推送到 GitHub，Zeabur 会自动重新部署！

```bash
git add .
git commit -m "更新代码"
git push origin main
```

---

## 下一步

恭喜！你的 C-learning-platform 已经在 Zeabur 上运行了！

- 访问：`https://xxx.zeabur.app`
- 完全免费
- 不需要绑卡
- 中文界面
- 24 小时运行

有任何问题随时询问！
