@echo off
chcp 65001 >nul
title GitHub 一键同步工具

echo.
echo ╔══════════════════════════════════════╗
echo     🚀 GitHub Auto Sync Tool v1.0
echo     C++ Learning Platform - Quick Sync
echo ╚══════════════════════════════════════╝
echo.

:: 设置 Git PATH
set "PATH=%PATH%;C:\Program Files\Git\cmd"

:: 检查 Git 是否可用
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found! Please install Git first.
    pause
    exit /b 1
)

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 显示当前状态
echo [INFO] Checking repository status...
echo.

:: 添加所有文件
echo [1/4] Adding files to staging area...
git add -A

:: 检查是否有变更需要提交
git status --porcelain | findstr /r "." >nul 2>&1
if %errorlevel% neq 0 (
    for /f %%a in ('time /t') do set timestamp=%%a
    
    :: 提交变更
    echo [2/4] Committing changes...
    git commit -m "Update: Auto-sync %date% %timestamp%"
    
    if %errorlevel% equ 0 (
        echo [OK] Commit successful!
    ) else (
        echo [WARN] Nothing to commit or commit failed
    )
) else (
    echo [INFO] No changes to commit. Repository is up to date.
    goto :skip_push
)

:: 推送到 GitHub
echo.
echo [3/4] Pushing to GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ╔══════════════════════════════════════╗
    echo     ✅ SUCCESS! Code pushed to GitHub!
    echo     Koyeb will auto-deploy in ~3 minutes
    echo ╚══════════════════════════════════════╝
) else (
    echo.
    echo [ERROR] Push failed! Trying to fix SSL settings...
    
    :: 尝试修复 SSL 问题
    git config --global http.sslBackend openssl
    git config --global http.postBuffer 524288000
    
    echo [RETRY] Retrying push...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ Push successful after fixing SSL!
    ) else (
        echo.
        echo ❌ Push still failed. Please check your network connection.
        echo     Try: Check VPN/proxy settings or retry later.
    )
)

:skip_push
echo.
echo [4/4] Sync completed at %time% on %date%
echo.

:: 等待用户按键
pause
