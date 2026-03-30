# MySQL 初始化脚本
# 需要以管理员权限运行

Write-Host "=== MySQL 初始化脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查是否以管理员权限运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "错误: 请以管理员权限运行此脚本!" -ForegroundColor Red
    Write-Host "右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

$mysqlDir = "C:\Program Files\MySQL\MySQL Server 8.0"
$binDir = "$mysqlDir\bin"
$dataDir = "$mysqlDir\data"

Write-Host "MySQL目录: $mysqlDir" -ForegroundColor Cyan

# 检查数据目录
if (Test-Path $dataDir) {
    Write-Host "数据目录已存在: $dataDir" -ForegroundColor Yellow
    Write-Host "正在清理数据目录..." -ForegroundColor Cyan
    Remove-Item "$dataDir\*" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "正在初始化MySQL数据目录..." -ForegroundColor Cyan

# 运行初始化命令
$initCommand = "$binDir\mysqld.exe" --initialize-insecure
& $initCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MySQL初始化成功!" -ForegroundColor Green
    
    # 启动MySQL服务
    Write-Host "正在启动MySQL服务..." -ForegroundColor Cyan
    $startCommand = "$binDir\mysqld.exe"
    Start-Process -FilePath $startCommand -WindowStyle Hidden -ArgumentList "--console"
    
    Start-Sleep -Seconds 3
    
    # 测试连接
    Write-Host "正在测试MySQL连接..." -ForegroundColor Cyan
    $testCommand = "$binDir\mysql.exe" -u root -e "SELECT VERSION();"
    $result = & $testCommand 2>&1
    
    if ($result -match "8\.0\.") {
        Write-Host "✅ MySQL连接成功!" -ForegroundColor Green
        Write-Host ""n        Write-Host "MySQL版本: $result" -ForegroundColor Green
        Write-Host ""n        Write-Host "下一步: 运行 setup_mysql.bat 配置数据库" -ForegroundColor Yellow
    } else {
        Write-Host "❌ MySQL连接失败" -ForegroundColor Red
        Write-Host "错误: $result" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ MySQL初始化失败" -ForegroundColor Red
    Write-Host "请检查权限和目录结构" -ForegroundColor Yellow
}

Write-Host ""nWrite-Host "按任意键退出..." -ForegroundColor Cyan
Read-Host
