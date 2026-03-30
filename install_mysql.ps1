# MySQL 自动安装和配置脚本
# 需要以管理员权限运行

Write-Host "=== MySQL 安装配置脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查是否以管理员权限运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "错误: 请以管理员权限运行此脚本!" -ForegroundColor Red
    Write-Host "右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

# 检查MySQL是否已安装
Write-Host "检查MySQL安装状态..." -ForegroundColor Cyan
$mysqlService = Get-Service -Name "MySQL*" -ErrorAction SilentlyContinue
if ($mysqlService) {
    Write-Host "MySQL已安装，服务状态: $($mysqlService.Status)" -ForegroundColor Green
    
    # 检查MySQL命令是否可用
    $mysqlPath = Get-Command mysql -ErrorAction SilentlyContinue
    if ($mysqlPath) {
        Write-Host "MySQL命令路径: $($mysqlPath.Source)" -ForegroundColor Green
    }
    exit 0
}

Write-Host "MySQL未安装，开始安装流程..." -ForegroundColor Yellow
Write-Host ""

# 方法1: 尝试使用winget安装
Write-Host "方法1: 尝试使用winget安装MySQL..." -ForegroundColor Cyan
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    Write-Host "找到winget，尝试安装MySQL Community Server..." -ForegroundColor Green
    
    # 搜索MySQL包
    Write-Host "搜索MySQL包..." -ForegroundColor Yellow
    winget search "MySQL Community Server"
    
    Write-Host ""
    Write-Host "请手动运行以下命令安装MySQL:" -ForegroundColor Yellow
    Write-Host "  winget install Oracle.MySQL" -ForegroundColor White
    Write-Host ""
    Write-Host "或者下载MySQL Installer:" -ForegroundColor Yellow
    Write-Host "  https://dev.mysql.com/downloads/installer/" -ForegroundColor White
} else {
    Write-Host "未找到winget" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 手动安装指南 ===" -ForegroundColor Green
Write-Host "1. 访问: https://dev.mysql.com/downloads/installer/" -ForegroundColor White
Write-Host "2. 下载 mysql-installer-community" -ForegroundColor White
Write-Host "3. 运行安装程序，选择 'Server only' 或 'Developer Default'" -ForegroundColor White
Write-Host "4. 设置root密码（建议: 123456）" -ForegroundColor White
Write-Host "5. 完成安装后，重新运行此脚本" -ForegroundColor White
Write-Host ""

# 检查常见MySQL安装路径
$commonPaths = @(
    "C:\Program Files\MySQL\MySQL Server 8.0\bin",
    "C:\Program Files\MySQL\MySQL Server 5.7\bin",
    "C:\xampp\mysql\bin",
    "C:\wamp64\bin\mysql\mysql8.0.*\bin"
)

Write-Host "检查常见MySQL安装路径..." -ForegroundColor Cyan
$foundPath = $null
foreach ($path in $commonPaths) {
    if ($path -like "*\*") {
        $expanded = Get-Item $path -ErrorAction SilentlyContinue
        if ($expanded) {
            $foundPath = $expanded.FullName
            break
        }
    } elseif (Test-Path $path) {
        $foundPath = $path
        break
    }
}

if ($foundPath) {
    Write-Host "找到MySQL安装路径: $foundPath" -ForegroundColor Green
    Write-Host "请将此路径添加到系统PATH环境变量" -ForegroundColor Yellow
} else {
    Write-Host "未找到MySQL安装路径" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "安装完成后，请运行 init_mysql_database.ps1 来初始化数据库" -ForegroundColor Green
pause
