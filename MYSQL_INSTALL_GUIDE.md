# MySQL 安装和配置指南

## 方法一：下载MySQL Installer（推荐）

### 1. 下载MySQL
- 访问：https://dev.mysql.com/downloads/installer/
- 选择 "mysql-installer-community" 下载
- 运行安装程序

### 2. 安装步骤
1. 选择 "Developer Default" 或 "Server only"
2. 点击 "Execute" 开始安装
3. 配置MySQL Server：
   - 设置root密码（建议：123456 或自定义）
   - 端口保持默认：3306
   - 字符集选择：utf8mb4

### 3. 验证安装
```powershell
# 打开命令提示符或PowerShell
mysql -u root -p
# 输入密码后进入MySQL命令行
```

## 方法二：使用PowerShell脚本自动安装

运行项目中的 `install_mysql.ps1` 脚本（需要管理员权限）

## 安装后配置

### 创建数据库
```sql
CREATE DATABASE learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 创建用户（可选）
```sql
CREATE USER 'learning_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON learning_platform.* TO 'learning_user'@'localhost';
FLUSH PRIVILEGES;
```

## 常见问题

### 1. 无法连接MySQL
- 检查MySQL服务是否启动：`net start MySQL`
- 检查防火墙设置
- 确认端口3306未被占用

### 2. 忘记root密码
```powershell
# 停止MySQL服务
net stop MySQL

# 以安全模式启动
mysqld --skip-grant-tables

# 重置密码
mysql -u root
USE mysql;
UPDATE user SET authentication_string=PASSWORD('新密码') WHERE User='root';
FLUSH PRIVILEGES;
```

### 3. 字符编码问题
确保my.ini配置文件包含：
```ini
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

[client]
default-character-set=utf8mb4
```
