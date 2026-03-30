# MySQL 本地启动脚本（使用用户目录）
# 无需管理员权限

Write-Host "=== MySQL 本地启动脚本 ===" -ForegroundColor Green
Write-Host ""

$mysqlDir = "C:\Program Files\MySQL\MySQL Server 8.0"
$binDir = "$mysqlDir\bin"
$dataDir = "$env:USERPROFILE\MySQLData"
$logDir = "$dataDir\logs"

Write-Host "MySQL目录: $mysqlDir" -ForegroundColor Cyan
Write-Host "数据目录: $dataDir" -ForegroundColor Cyan
Write-Host ""

# 创建数据目录
if (-not (Test-Path $dataDir)) {
    Write-Host "创建数据目录..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# 检查是否已初始化
if (-not (Test-Path "$dataDir\mysql")) {
    Write-Host "初始化MySQL数据目录..." -ForegroundColor Cyan
    Write-Host "这可能需要几分钟..." -ForegroundColor Yellow
    
    $initArgs = @(
        "--initialize-insecure",
        "--datadir=$dataDir",
        "--log-error=$logDir\error.log"
    )
    
    & "$binDir\mysqld.exe" @initArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ MySQL初始化失败" -ForegroundColor Red
        Write-Host "请检查日志: $logDir\error.log" -ForegroundColor Yellow
        pause
        exit 1
    }
    
    Write-Host "✅ MySQL初始化成功!" -ForegroundColor Green
} else {
    Write-Host "✅ 数据目录已存在，跳过初始化" -ForegroundColor Green
}

Write-Host ""
Write-Host "启动MySQL服务..." -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 启动MySQL
$startArgs = @(
    "--console",
    "--datadir=$dataDir",
    "--port=3306",
    "--log-error=$logDir\error.log"
)

& "$binDir\mysqld.exe" @startArgs
