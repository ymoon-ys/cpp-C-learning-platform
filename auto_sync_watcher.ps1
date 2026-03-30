$projectPath = "C:\Users\18341\Desktop\C-learning-platform"
$gitPath = "C:\Program Files\Git\bin\git.exe"
$lastSyncTime = [DateTime]::MinValue
$syncInterval = 30

function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $message"
}

function Sync-ToGitHub {
    Set-Location $projectPath
    
    $hasChanges = & $gitPath status --porcelain 2>$null
    if ($hasChanges) {
        Write-Log "检测到文件修改，正在同步..."
        
        & $gitPath add -A 2>$null
        
        $commitMessage = "自动同步 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        & $gitPath commit -m $commitMessage 2>$null
        
        $pushResult = & $gitPath push origin main 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ 同步成功！已推送到 GitHub"
        } else {
            Write-Log "❌ 推送失败: $pushResult"
        }
    }
}

Write-Host "========================================================"
Write-Host "  C++学习平台 - 自动同步监控服务"
Write-Host "  监控目录: $projectPath"
Write-Host "  按 Ctrl+C 停止监控"
Write-Host "========================================================"
Write-Host ""

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $projectPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$ignorePatterns = @('.git', '__pycache__', '*.pyc', '.idea', 'venv', 'instance')

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $shouldIgnore = $false
    
    foreach ($pattern in $ignorePatterns) {
        if ($path -like "*$pattern*") {
            $shouldIgnore = $true
            break
        }
    }
    
    if (-not $shouldIgnore) {
        $global:fileChanged = $true
    }
}

$watcher.Add_Changed($action)
$watcher.Add_Created($action)
$watcher.Add_Deleted($action)
$watcher.Add_Renamed($action)

$global:fileChanged = $false

while ($true) {
    Start-Sleep -Seconds $syncInterval
    
    if ($global:fileChanged) {
        $global:fileChanged = $false
        Sync-ToGitHub
    }
}
