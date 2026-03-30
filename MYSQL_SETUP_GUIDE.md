# MySQL 数据库配置完整指南

## 📋 概述

本指南将帮助你在Windows系统上安装和配置MySQL数据库，并将SQLite数据迁移到MySQL。

## 🔧 步骤1: 安装MySQL

### 方法A: 使用MySQL Installer（推荐）

1. **下载MySQL Installer**
   - 访问：https://dev.mysql.com/downloads/installer/
   - 选择 `mysql-installer-community-x.x.x.msi` 下载
   - 点击 "No thanks, just start my download" 跳过登录

2. **运行安装程序**
   - 双击下载的 `.msi` 文件
   - 选择安装类型：`Server only` 或 `Developer Default`
   - 点击 `Execute` 开始下载和安装

3. **配置MySQL Server**
   - **Type and Networking**: 保持默认设置
   - **Authentication Method**: 选择 `Use Strong Password Encryption`
   - **Accounts and Roles**: 设置root密码（建议：`123456`）
   - **Windows Service**: 勾选 `Configure MySQL Server as a Windows Service`
   - **Apply Configuration**: 点击 `Execute` 应用配置

4. **完成安装**
   - 点击 `Finish` 完成安装
   - MySQL会自动启动

### 方法B: 使用XAMPP（更简单）

1. 下载XAMPP：https://www.apachefriends.org/
2. 安装时勾选MySQL组件
3. 启动XAMPP Control Panel
4. 点击MySQL的"Start"按钮

### 方法C: 使用Docker

```powershell
# 拉取MySQL镜像
docker pull mysql:8.0

# 运行MySQL容器
docker run -d --name mysql-learning -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123456 mysql:8.0
```

## ✅ 步骤2: 验证安装

打开PowerShell或命令提示符，运行：

```powershell
# 检查MySQL版本
mysql --version

# 测试连接
mysql -u root -p
# 输入密码后应该进入MySQL命令行
```

## 🗄️ 步骤3: 创建数据库

### 方法A: 使用配置脚本（推荐）

双击运行 `setup_mysql.bat`，按照提示操作。

### 方法B: 手动创建

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 验证创建
SHOW DATABASES;

-- 退出
EXIT;
```

## 📦 步骤4: 安装Python依赖

```powershell
pip install mysql-connector-python
```

## 🔄 步骤5: 迁移数据

```powershell
# 运行迁移脚本
python migrate_to_mysql.py
```

## ⚙️ 步骤6: 配置应用

### 创建 .env 文件

在项目根目录创建 `.env` 文件：

```env
# 数据库配置
DB_TYPE=mysql

# MySQL配置
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=learning_platform
MYSQL_PORT=3306
```

### 或使用模板

```powershell
# 复制模板文件
copy .env.mysql .env

# 编辑密码（如果不同）
notepad .env
```

## 🚀 步骤7: 启动应用

```powershell
python run.py
```

## 🔍 故障排除

### 问题1: mysql命令未找到

**解决方案**：将MySQL添加到系统PATH

1. 右键"此电脑" → "属性" → "高级系统设置"
2. 点击"环境变量"
3. 在"系统变量"中找到"Path"，点击"编辑"
4. 添加MySQL bin目录路径，例如：
   - `C:\Program Files\MySQL\MySQL Server 8.0\bin`
   - `C:\xampp\mysql\bin`
5. 重启PowerShell

### 问题2: 无法连接MySQL

**检查清单**：
- [ ] MySQL服务是否启动？
  ```powershell
  net start | findstr MySQL
  # 如果未启动，运行：
  net start MySQL80
  ```
- [ ] 防火墙是否阻止3306端口？
- [ ] 密码是否正确？

### 问题3: 字符编码问题

**解决方案**：确保数据库使用utf8mb4

```sql
-- 检查数据库编码
SHOW CREATE DATABASE learning_platform;

-- 如果不是utf8mb4，修改：
ALTER DATABASE learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题4: 连接被拒绝

**解决方案**：检查用户权限

```sql
-- 登录MySQL
mysql -u root -p

-- 创建新用户（可选）
CREATE USER 'learning_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON learning_platform.* TO 'learning_user'@'localhost';
FLUSH PRIVILEGES;
```

## 📝 快速命令参考

```powershell
# 检查MySQL状态
python check_mysql_status.py

# 运行配置向导
setup_mysql.bat

# 迁移数据
python migrate_to_mysql.py

# 启动应用
python run.py

# 切换回SQLite（如果需要）
# 修改 .env 文件中的 DB_TYPE=sqlite
```

## 🆘 需要帮助？

如果遇到问题：

1. 运行诊断脚本：`python check_mysql_status.py`
2. 查看MySQL错误日志：
   - Windows: `C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.err`
   - XAMPP: `C:\xampp\mysql\data\*.err`
3. 检查应用日志：查看控制台输出

## 📚 相关文件

- `MYSQL_INSTALL_GUIDE.md` - 安装指南
- `setup_mysql.bat` - 自动配置脚本
- `migrate_to_mysql.py` - 数据迁移脚本
- `check_mysql_status.py` - 状态检查脚本
- `.env.mysql` - 配置文件模板
