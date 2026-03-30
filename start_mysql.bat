@echo off
chcp 65001 >nul
echo ========================================
echo    MySQL 本地启动脚本
echo ========================================
echo.

set MYSQL_BIN="C:\Program Files\MySQL\MySQL Server 8.0\bin"
set DATA_DIR=%USERPROFILE%\MySQLData

if not exist %DATA_DIR% mkdir %DATA_DIR%

echo MySQL目录: %MYSQL_BIN%
echo 数据目录: %DATA_DIR%
echo.

if not exist "%DATA_DIR%\mysql" (
    echo 正在初始化MySQL数据目录...
    echo 这可能需要几分钟...
    echo.
    
    %MYSQL_BIN%\mysqld.exe --initialize-insecure --datadir="%DATA_DIR%"
    
    if errorlevel 1 (
        echo 初始化失败，请检查权限
        pause
        exit /b 1
    )
    
    echo 初始化成功!
    echo.
)

echo 启动MySQL服务...
echo 按 Ctrl+C 停止服务
echo.
echo MySQL连接信息:
echo   主机: localhost
echo   端口: 3306
echo   用户: root
echo   密码: (空)
echo.

%MYSQL_BIN%\mysqld.exe --console --datadir="%DATA_DIR%" --port=3306

pause
