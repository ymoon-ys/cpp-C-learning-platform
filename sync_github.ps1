# =====================================================
# GitHub Auto Sync Script for C++ Learning Platform
# Version: 1.0
# Author: Auto-generated
# Description: One-click Git commit and push to GitHub
# Usage: Right-click → Run with PowerShell
#        Or: powershell -ExecutionPolicy Bypass -File sync_github.ps1
# =====================================================

# 设置控制台颜色
$Host.UI.RawUI.WindowTitle = "GitHub Sync Tool - C++ Learning Platform"
Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "     🚀 GitHub Auto Sync Tool v1.0       " -ForegroundColor Cyan
Write-Host "     C++ Learning Platform              " -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. 确保 Git 在 PATH 中
$gitPath = "C:\Program Files\Git\cmd"
if ($env:Path -notlike "*$gitPath*") {
    $env:Path += ";$gitPath"
}

# 2. 检查 Git 是否可用
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git not found! Please install Git first." -ForegroundColor Red
    Write-Host "Download: https://git-scm.com/downloads" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Git version: $(git --version)" -ForegroundColor Green

# 3. 切换到脚本所在目录
Set-Location -Path $PSScriptRoot
Write-Host "[INFO] Working directory: $(Get-Location)" -ForegroundColor Gray

# 4. 显示当前状态
Write-Host ""
Write-Host "[1/5] Checking repository status..." -ForegroundColor Yellow
$status = git status --porcelain

if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "[INFO] No changes detected. Repository is up to date." -ForegroundColor Green
    
    # 检查是否有未推送的提交
    $unpushed = git log origin/main..main --oneline 2>$null
    if ($unpushed) {
        Write-Host ""
        Write-Host "[WARN] Found unpushed commits:" -ForegroundColor Yellow
        Write-Host $unpushed -ForegroundColor Gray
        
        $push = Read-Host "Do you want to push these commits? (Y/n)"
        if ($push -eq 'Y' -or $push -eq 'y') {
            Push-ToGitHub
        }
    } else {
        Write-Host ""
        Write-Host "✅ Everything is up to date!" -ForegroundColor Green
    }
    
    Read-Host "`nPress Enter to exit"
    exit 0
}

# 5. 统计变更
$changedFiles = ($status | Measure-Object).Count
$added = ($status | Where-Object { $_ -match '^\?\?A' }).Count
$modified = ($status | Where-Object { $_ -match '^[MARC]' }).Count
$deleted = ($status | Where-Object { $_ -match '^[ D]' }).Count

Write-Host "Found changes:" -ForegroundColor White
Write-Host "  • Modified: $modified files" -ForegroundColor Yellow
Write-Host "  • Added:   $added files" -ForegroundColor Green
if ($deleted -gt 0) { Write-Host "  • Deleted: $deleted files" -ForegroundColor Red }

# 6. 添加文件到暂存区
Write-Host ""
Write-Host "[2/5] Adding files to staging area..." -ForegroundColor Yellow
git add -A | Out-Null
Write-Host "[OK] All changes staged successfully" -ForegroundColor Green

# 7. 生成智能提交信息
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$dayOfWeek = (Get-Date).ToString("dddd", [System.Globalization.CultureInfo]::new("zh-CN"))

# 分析变更类型并生成合适的提交信息
$commitMsg = ""
if ($added -gt 0 -and $modified -eq 0 -and $deleted -eq 0) {
    $commitMsg = "Add: New files ($added items)"
} elseif ($deleted -gt 0 -and $added -eq 0 -and $modified -eq 0) {
    $commitMsg = "Remove: Clean up files ($deleted items)"
} elseif ($modified -gt 0 -and $added -eq 0 -and $deleted -eq 0) {
    $commitMsg = "Update: Modify $modified files"
} else {
    $commitMsg = "Update: Auto-sync $timestamp ($dayOfWeek)"
}

Write-Host ""
Write-Host "[3/5] Committing changes..." -ForegroundColor Yellow
Write-Host "Message: $commitMsg" -ForegroundColor Gray

$commitResult = git commit -m $commitMsg 2>&1

if ($LASTEXITCODE -eq 0) {
    # 提取 commit hash
    $commitHash = ($commitResult | Select-String -Pattern '[a-f0-9]{7}' | Select-Object -First 1).Matches[0].Value
    Write-Host "[OK] Committed: $commitHash" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Commit failed!" -ForegroundColor Red
    Write-Host $commitResult -ForegroundColor Red
    Read-Host "`nPress Enter to exit"
    exit 1
}

# 8. 推送到 GitHub
Push-ToGitHub

function Push-ToGitHub {
    Write-Host ""
    Write-Host "[4/5] Pushing to GitHub..." -ForegroundColor Yellow
    
    $pushOutput = git push origin main 2>&1
    $pushSuccess = $LASTEXITCODE
    
    if ($pushSuccess -eq 0) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "     ✅ SUCCESS! Code pushed to GitHub!         " -ForegroundColor Green
        Write-Host "                                             " -ForegroundColor Green
        Write-Host "     Next steps:                              " -ForegroundColor Cyan
        Write-Host "     1. Koyeb will auto-deploy in ~3 minutes   " -ForegroundColor White
        Write-Host "     2. Check: https://app.koyeb.com          " -ForegroundColor White
        Write-Host "     3. Test your live site                     " -ForegroundColor White
        Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Green
        
        # 显示推送统计
        if ($pushOutput -match '(\d+) file.*changed.*(\d+) insertion.*(\d+) deletion') {
            Write-Host "" 
            Write-Host "Stats: $($Matches[1]) files changed, $($Matches[2]) insertions(+), $($Matches[3]) deletions(-)" -ForegroundColor Gray
        }
        
        Show-Summary
    } else {
        Write-Host ""
        Write-Host "[ERROR] Push failed!" -ForegroundColor Red
        Write-Host "Attempting to fix SSL settings..." -ForegroundColor Yellow
        
        # 尝试修复常见问题
        git config --global http.sslBackend openssl 2>$null | Out-Null
        git config --global http.postBuffer 524288000 2>$null | Out-Null
        
        Write-Host "[RETRY] Retrying push..." -ForegroundColor Yellow
        $retryOutput = git push origin main 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Push successful after fixing SSL!" -ForegroundColor Green
            Show-Summary
        } else {
            Write-Host ""
            Write-Host "❌ Push still failed!" -ForegroundColor Red
            Write-Host "" 
            Write-Host "Possible solutions:" -ForegroundColor Yellow
            Write-Host "  1. Check your internet connection" -ForegroundColor White
            Write-Host "  2. If using VPN, try turning it off" -ForegroundColor White
            Write-Host "  3. Check GitHub authentication" -ForegroundColor White
            Write-Host "  4. Try again later" -ForegroundColor White
            Write-Host ""
            Write-Host "Error details:" -ForegroundColor Red
            Write-Host $retryOutput -ForegroundColor DarkRed
            
            Show-Summary
        }
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "[5/5] Sync completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    
    # 显示仓库信息
    $remoteUrl = git remote get-url origin 2>$null
    if ($remoteUrl) {
        Write-Host "Repository: $remoteUrl" -ForegroundColor Gray
    }
    
    $branch = git branch --show-current 2>$null
    if ($branch) {
        Write-Host "Branch: $branch" -ForegroundColor Gray
    }
    
    Write-Host ""
    Read-Host "Press Enter to exit"
}

# 结束
