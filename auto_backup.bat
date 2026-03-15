@echo off
cd /d "%~dp0"
echo ========================================================================
echo   C++学习平台 - GitHub自动备份脚本
echo ========================================================================
echo [%date% %time%] 开始自动备份...
echo.

:: 设置Git路径
set GIT_PATH="C:\Program Files\Git\bin\git.exe"

:: 检查是否已初始化Git仓库
if not exist ".git\" (
    echo [错误] Git仓库未初始化！
    echo.
    pause
    exit /b 1
)

:: 添加所有修改的文件
%GIT_PATH% add -A

:: 检查是否有修改
%GIT_PATH% diff --cached --quiet
if %errorlevel% neq 0 (
    echo [1/3] 检测到文件修改，正在添加...
    echo.
    
    echo [2/3] 正在提交到本地仓库...
    %GIT_PATH% commit -m "自动备份 %date% %time%"
    if %errorlevel% neq 0 (
        echo [错误] 提交失败！
        pause
        exit /b 1
    )
    echo.
    
    echo [3/3] 正在推送到GitHub...
    %GIT_PATH% push origin main
    if %errorlevel% neq 0 (
        echo [错误] 推送失败！请检查网络连接和GitHub凭证。
        pause
        exit /b 1
    )
    echo.
    
    echo ========================================================================
    echo   ✅ 备份成功！已同步到GitHub！
    echo   仓库地址: https://github.com/ymoon-ys/cpp-C-learning-platform
    echo ========================================================================
) else (
    echo ========================================================================
    echo   ℹ️  没有文件修改，跳过备份
    echo ========================================================================
)
echo.
pause
