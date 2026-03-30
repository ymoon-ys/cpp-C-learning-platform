@echo off
chcp 65001 >nul
echo ========================================
echo    MySQL 数据库配置向导
echo ========================================
echo.

echo 此脚本将帮助你：
echo 1. 检查MySQL安装状态
echo 2. 创建数据库
echo 3. 迁移SQLite数据到MySQL
echo 4. 配置应用使用MySQL
echo.

pause

echo.
echo [步骤 1/4] 检查MySQL安装状态...
echo.

mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到MySQL
    echo.
    echo 请先安装MySQL：
    echo   1. 访问 https://dev.mysql.com/downloads/installer/
    echo   2. 下载并安装 MySQL Community Server
    echo   3. 设置root密码（建议：123456）
    echo   4. 完成安装后重新运行此脚本
    echo.
    echo 或者运行 install_mysql.ps1 获取更多帮助
    pause
    exit /b 1
)

echo ✅ MySQL已安装
echo.

echo [步骤 2/4] 测试MySQL连接...
echo.

set /p MYSQL_PASSWORD=请输入MySQL root密码 (默认: 123456): 
if "%MYSQL_PASSWORD%"=="" set MYSQL_PASSWORD=123456

mysql -u root -p%MYSQL_PASSWORD% -e "SELECT 1" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ MySQL连接失败
    echo 请检查密码是否正确
    pause
    exit /b 1
)

echo ✅ MySQL连接成功
echo.

echo [步骤 3/4] 创建数据库...
echo.

mysql -u root -p%MYSQL_PASSWORD% -e "CREATE DATABASE IF NOT EXISTS learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if %errorlevel% neq 0 (
    echo ❌ 创建数据库失败
    pause
    exit /b 1
)

echo ✅ 数据库创建成功
echo.

echo [步骤 4/4] 配置应用...
echo.

(
echo # 数据库配置
echo DB_TYPE=mysql
echo.
echo # MySQL配置
echo MYSQL_HOST=localhost
echo MYSQL_USER=root
echo MYSQL_PASSWORD=%MYSQL_PASSWORD%
echo MYSQL_DATABASE=learning_platform
echo MYSQL_PORT=3306
) > .env

echo ✅ 配置文件已创建
echo.

echo ========================================
echo    配置完成！
echo ========================================
echo.
echo 下一步：
echo   1. 运行 migrate_to_mysql.py 迁移数据
echo   2. 运行 python run.py 启动应用
echo.

pause
