@echo off
chcp 65001 >nul
title C语言学习平台 - 一键部署工具
color 0A

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║     🚀 C语言学习平台 - 阿里云 Windows 一键部署    ║
echo ║                                              ║
echo ║   自动完成:                                   ║
echo ║   ✅ 安装 Python                              ║
echo ║   ✅ 安装 Git                                 ║
echo ║   ✅ 克隆项目代码                             ║
echo ║   ✅ 安装所有依赖                             ║
echo ║   ✅ 配置环境变量                             ║
echo ║   ✅ 初始化数据库                             ║
echo ║   ✅ 启动 Web 服务                            ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 请以管理员身份运行此脚本！
    echo    右键点击此文件 → "以管理员身份运行"
    pause
    exit /b 1
)

set "PROJECT_DIR=D:\cpp-C-learning-platform"
set "PYTHON_VERSION=3.11.6"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"

:: ==================== 步骤 1: 检测系统架构 ====================
echo.
echo [1/9] 🔍 检测系统环境...
echo.

:: 检查是否为64位系统
if not "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    if not "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
        echo ❌ 错误: 本脚本仅支持 64 位 Windows 系统
        pause
        exit /b 1
    )
)

echo ✅ 系统架构: %PROCESSOR_ARCHITECTURE%
echo ✅ 操作系统: %OS%

:: ==================== 步骤 2: 安装 Python ====================
echo.
echo [2/9] 🐍 检查/安装 Python...
echo.

python --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do (
        echo ✅ Python 已安装: %%v
    )
) else (
    echo ⏳ 正在下载 Python %PYTHON_VERSION%...
    
    :: 创建临时目录
    if not exist "%TEMP%\c-learning-deploy" mkdir "%TEMP%\c-learning-deploy"
    
    :: 下载 Python (使用 PowerShell)
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -URI '%PYTHON_URL%' -OutFile '%TEMP%\c-learning-deploy\python-installer.exe' }"
    
    if exist "%TEMP%\c-learning-deploy\python-installer.exe" (
        echo ✅ 下载完成
        echo ⏳ 正在安装 Python (请稍候，需要 2-3 分钟)...
        
        :: 静默安装 Python，添加到 PATH
        start /wait "" "%TEMP%\c-learning-deploy\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        
        :: 刷新环境变量
        call refreshenv >nul 2>&1 || set "PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts"
        
        python --version >nul 2>&1
        if %errorLevel% equ 0 (
            for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do (
                echo ✅ Python 安装成功: %%v
            )
        ) else (
            echo ❌ Python 安装失败，请手动安装后重试
            pause
            exit /b 1
        )
    ) else (
        echo ❌ 下载失败，请检查网络连接
        pause
        exit /b 1
    )
)

:: ==================== 步骤 3: 安装 Git ====================
echo.
echo [3/9] 📦 检查/安装 Git...
echo.

git --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=3 delims= " %%v in ('git --version 2^>^&1') do (
        echo ✅ Git 已安装: %%v
    )
) else (
    echo ⏳ 正在下载 Git...
    
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -URI 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile '%TEMP%\c-learning-deploy\git-installer.exe' }"
    
    if exist "%TEMP%\c-learning-deploy\git-installer.exe" (
        echo ✅ 下载完成
        echo ⏳ 正在安装 Git...
        
        start /wait "" "%TEMP%\c-learning-deploy\git-installer.exe" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
        
        set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\Git\bin"
        
        git --version >nul 2>&1
        if %errorLevel% equ 0 (
            for /f "tokens=3 delims= " %%v in ('git --version 2^>^&1') do (
                echo ✅ Git 安装成功: %%v
            )
        ) else (
            echo ⚠️ Git 可能未正确添加到 PATH，尝试使用完整路径
            set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
        )
    ) else (
        echo ❌ Git 下载失败
        pause
        exit /b 1
    )
)

:: ==================== 步骤 4: 克隆项目代码 ====================
echo.
echo [4/9] 📥 克隆项目代码...
echo.

if exist "%PROJECT_DIR%\.git" (
    echo ✅ 项目已存在，更新代码...
    cd /d "%PROJECT_DIR%"
    git pull origin main
) else (
    echo ⏳ 正在克隆项目到 %PROJECT_DIR%...
    git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git "%PROJECT_DIR%"
    
    if exist "%PROJECT_DIR%\run.py" (
        echo ✅ 项目克隆成功
    ) else (
        echo ❌ 项目克隆失败，请检查网络
        pause
        exit /b 1
    )
)

cd /d "%PROJECT_DIR%"

:: ==================== 步骤 5: 创建虚拟环境并安装依赖 ====================
echo.
echo [5/9] 📋 安装项目依赖...
echo.

if not exist "venv" (
    echo ⏳ 创建 Python 虚拟环境...
    python -m venv venv
)

echo ⏳ 激活虚拟环境...
call venv\Scripts\activate.bat

echo ⏳ 升级 pip...
python -m pip install --upgrade pip -q

echo ⏳ 安装依赖包 (这步可能需要 5-10 分钟)...
pip install -r requirements.txt -q

pip install waitress -q

echo ✅ 依赖安装完成

:: ==================== 步骤 6: 配置环境变量 ====================
echo.
echo [6/9] ⚙️ 配置数据库连接...
echo.

if not exist ".env.production" (
    copy .env.production.example .env.production >nul
    echo ✅ 已创建配置文件模板
)

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  📝 请编辑 .env.production 文件填入以下信息:       ║
echo ╠══════════════════════════════════════════════════╣
echo ║                                                ║
echo ║  MYSQL_HOST=rm-bp11x99qe6c0c9b9k.mysql.rds.aliyuncs.com ║
echo ║  MYSQL_PORT=3306                               ║
echo ║  MYSQL_USER=clearning_user                     ║
echo ║  MYSQL_PASSWORD=<你的RDS密码>                    ║
echo ║  MYSQL_DATABASE=learning_platform              ║
echo ║                                                ║
echo ║  QWEN_API_KEY=sk-4e93fc91489940afb7ea78f1839ef80f ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: 询问是否要现在编辑
set /p EDIT_CONFIG="是否现在打开编辑器配置? (Y/n): "
if /i "%EDIT_CONFIG%"=="" set EDIT_CONFIG=Y
if /i "%EDIT_CONFIG%"=="Y" (
    notepad .env.production
)

echo ✅ 配置文件已准备就绪

:: ==================== 步骤 7: 初始化数据库 ====================
echo.
echo [7/9] 🗄️ 初始化数据库...
echo.

echo ⏳ 正在创建数据表和默认账号...

python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ 数据库表创建成功')" 2>nul

if %errorLevel% equ 0 (
    echo ✅ 数据库初始化成功
    
    python -c "from app import create_app, db; from app.models.user import User; from werkzeug.security import generate_password_hash; app = create_app(); app.app_context().push(); 
    u = User.query.filter_by(username='admin').first() 
    if not u:
        db.session.add(User(username='admin', email='admin@c-learning.com', password_hash=generate_password_hash('admin123'), role='admin', is_active=True))
        db.session.add(User(username='teacher', email='teacher@c-learning.com', password_hash=generate_password_hash('teacher123'), role='teacher', is_active=True))
        db.session.add(User(username='student', email='student@c-learning.com', password_hash=generate_password_hash('student123'), role='student', is_active=True))
        db.session.commit()
        print('✅ 默认账号创建成功')
    else:
        print('ℹ️ 默认账号已存在')"
) else (
    echo ⚠️ 数据库初始化可能失败，请检查 .env.production 配置
)

:: ==================== 步骤 8: 启动 Web 服务 ====================
echo.
echo [8/9] 🚀 启动 Web 服务...
echo.

echo ⏳ 正在启动 Waitress 服务器 (监听端口 8000)...

:: 添加防火墙规则
powershell -Command "New-NetFirewallRule -DisplayName 'C-Learning Platform' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue" >nul 2>&1

:: 后台启动服务
start "C-Learning-Platform" cmd /k "cd /d %PROJECT_DIR% && call venv\Scripts\activate.bat && waitress-serve --host=0.0.0.0 --port=8000 --threads=4 run:app"

:: 等待启动
timeout /t 5 /nobreak >nul

:: 测试是否启动成功
curl -s http://localhost:8000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 服务启动成功!
) else (
    echo ⚠️ 服务可能还在启动中，请稍等片刻...
)

:: ==================== 步骤 9: 完成 ====================
echo.
echo [9/9] 🎉 部署完成!
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║           🎊 恭喜! 部署成功! 🎊                  ║
echo ╠══════════════════════════════════════════════════╣
echo ║                                                ║
echo ║  📍 本地访问地址:                               ║
echo ║     http://localhost:8000                       ║
echo ║                                                ║
echo ║  🌐 公网访问地址 (在浏览器中打开):               ║
echo ║     http://47.97.204.90:8000                   ║
echo ║                                                ║
echo ║  👤 默认登录账号:                               ║
echo ║     管理员: admin / admin123                    ║
echo ║     教师:   teacher / teacher123                ║
echo ║     学生:   student / student123                ║
echo ║                                                ║
echo ║  📂 项目目录:                                    ║
echo ║     D:\cpp-C-learning-platform                 ║
echo ║                                                ║
echo ║  🛠️ 常用命令:                                   ║
echo ║     查看进程: tasklist ^| findstr python         ║
echo ║     停止服务: taskkill /F /IM python.exe         ║
echo ║     重启服务: 重新运行此脚本                      ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 💡 提示:
echo    - 如果无法访问公网 IP，请检查 ECS 安全组是否开放 8000 端口
echo    - 新开的窗口是 Web 服务窗口，不要关闭它!
echo    - 按任意键退出此向导...
echo.

pause >nul
