@echo off
title C++学习平台 - 自动同步监控
cd /d "%~dp0"
echo ========================================================
echo   启动自动同步监控服务...
echo ========================================================
echo.
PowerShell -ExecutionPolicy Bypass -File "%~dp0auto_sync_watcher.ps1"
pause
