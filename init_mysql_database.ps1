# MySQL 数据库初始化脚本
# 在MySQL安装完成后运行此脚本

param(
    [string]$MySQLHost = "localhost",
    [string]$MySQLUser = "root",
    [string]$MySQLPassword = "123456",
    [string]$Database = "learning_platform",
    [int]$Port = 3306
)

Write-Host "=== MySQL 数据库初始化 ===" -ForegroundColor Green
Write-Host ""

# 检查MySQL命令
$mysqlCmd = Get-Command mysql -ErrorAction SilentlyContinue
if (-not $mysqlCmd) {
    Write-Host "错误: 未找到mysql命令，请确保MySQL已安装并添加到PATH" -ForegroundColor Red
    Write-Host "常见路径:" -ForegroundColor Yellow
    Write-Host "  C:\Program Files\MySQL\MySQL Server 8.0\bin" -ForegroundColor White
    Write-Host "  C:\xampp\mysql\bin" -ForegroundColor White
    pause
    exit 1
}

Write-Host "MySQL命令: $($mysqlCmd.Source)" -ForegroundColor Green
Write-Host ""

# 测试MySQL连接
Write-Host "测试MySQL连接..." -ForegroundColor Cyan
$testConnection = & mysql -h $MySQLHost -u $MySQLUser -p$MySQLPassword -e "SELECT 1" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法连接到MySQL服务器" -ForegroundColor Red
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. MySQL服务是否启动: net start MySQL" -ForegroundColor White
    Write-Host "  2. 用户名和密码是否正确" -ForegroundColor White
    Write-Host "  3. 端口是否正确 (默认3306)" -ForegroundColor White
    Write-Host ""
    Write-Host "连接信息:" -ForegroundColor Yellow
    Write-Host "  主机: $MySQLHost" -ForegroundColor White
    Write-Host "  用户: $MySQLUser" -ForegroundColor White
    Write-Host "  端口: $Port" -ForegroundColor White
    pause
    exit 1
}

Write-Host "MySQL连接成功!" -ForegroundColor Green
Write-Host ""

# 创建数据库
Write-Host "创建数据库: $Database" -ForegroundColor Cyan
$createDbSql = "CREATE DATABASE IF NOT EXISTS $Database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
& mysql -h $MySQLHost -u $MySQLUser -p$MySQLPassword -e $createDbSql

if ($LASTEXITCODE -eq 0) {
    Write-Host "数据库创建成功!" -ForegroundColor Green
} else {
    Write-Host "数据库创建失败或已存在" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 数据库初始化完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "数据库信息:" -ForegroundColor Cyan
Write-Host "  数据库名: $Database" -ForegroundColor White
Write-Host "  字符集: utf8mb4" -ForegroundColor White
Write-Host ""
Write-Host "下一步: 运行 migrate_to_mysql.py 迁移数据" -ForegroundColor Yellow
pause
