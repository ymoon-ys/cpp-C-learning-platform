@echo off
chcp 65001 >nul 2>&1
title Git Push to GitHub - C-Learning Platform

echo.
echo ============================================
echo    🚀 C-Learning Platform - GitHub 推送工具
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] 🔍 检查 Git 仓库状态...
if not exist ".git" (
    echo ❌ 错误：当前目录不是 Git 仓库
    pause
    exit /b 1
)
echo ✅ Git 仓库检查通过
echo.

echo [2/4] 📦 添加修改的文件到暂存区...
git add app/config.py
git add app/__init__.py
git add app/routes/ai_assistant.py
git add Dockerfile
git add gunicorn.conf.py
git add KOYEB_DEPLOYMENT_GUIDE.md
git add FIXES_SUMMARY.md
git add check_deployment.py
git add test_db_connection.py
git add .env.production.example
git add .gitignore
git add push_to_github.ps1
git add push_to_github.bat
echo ✅ 文件添加完成
echo.

echo [3/4] 🔖 创建 Commit...
git commit -m "fix: 修复公网部署问题并优化本地开发配置

主要修复：
- 移除硬编码的不安全默认值（config.py）
- 添加环境变量验证机制（生产环境强制要求）
- 改进数据库连接错误处理和提示信息
- 动态设置 HSTS 安全头（支持 HTTP/HTTPS 自动检测）
- Dockerfile 添加 g++ 编译器支持 Linux/Docker 环境
- 改进编译器检测逻辑，完整支持跨平台

新增功能：
- Koyeb 部署完整指南 (KOYEB_DEPLOYMENT_GUIDE.md)
- 部署前自动化检查工具 (check_deployment.py)
- 数据库连接测试脚本 (test_db_connection.py)
- 生产环境变量模板 (.env.production.example)
- 修复总结文档 (FIXES_SUMMARY.md)
- 一键推送脚本 (push_to_github.ps1/bat)

安全改进：
- 强制要求 SECRET_KEY 环境变量（生产环境）
- 生产环境缺少必需配置时阻止启动
- 完善 .gitignore 保护敏感文件和临时文件

配置恢复：
- 恢复原始数据库名称 learning_platform
- 更新本地开发环境 .env 配置"
if %errorlevel% neq 0 (
    echo ⚠️ 没有新的更改需要提交，或提交失败
) else (
    echo ✅ Commit 创建成功
)
echo.

echo [4/4] 🚀 推送到 GitHub...
echo 正在推送到 origin/main...
echo.

git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo    ✅ 推送成功！代码已上传到 GitHub
    echo ============================================
    echo.
    
    for /f "tokens=*" %%i in ('git remote get-url origin') do set REMOTE_URL=%%i
    echo 🌐 远程仓库: %REMOTE_URL%
    echo.
    
    for /f "tokens=*" %%i in ('git log -1 --pretty^=format:"%%h - %%s"') do set LAST_COMMIT=%%i
    echo 📝 最新提交: %LAST_COMMIT%
    echo.
    echo 📖 下一步操作：
    echo    1. 访问 GitHub 查看推送的代码
    echo    2. 如需部署到 Koyeb，参考 KOYEB_DEPLOYMENT_GUIDE.md
    echo    3. 运行 test_db_connection.py 测试数据库连接
    echo    4. 运行 python run.py 启动本地应用
    echo.
) else (
    echo.
    echo ❌ 推送失败！可能的原因：
    echo    1. 网络连接问题
    echo    2. 认证失败（需要重新登录 GitHub）
    echo    3. 远程仓库有新的提交需要先拉取
    echo.
    echo 💡 尝试以下命令：
    echo    git pull origin main --rebase
    echo    git push origin main
    echo.
)

pause
