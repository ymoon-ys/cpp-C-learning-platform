# ============================================
# Git 推送脚本 - 推送修复到 GitHub
# ============================================
#
# 使用方法：
#   1. 在 PowerShell 中运行此脚本
#   2. 或右键 → "使用 PowerShell 运行"
#
# 此脚本会自动：
#   - 检查 .gitignore 保护敏感文件
#   - 添加所有修改的文件
#   - 创建有意义的 commit
#   - 推送到 GitHub

Write-Host ""
Write-Host "🚀" * 20
Write-Host "       Git 推送工具"
Write-Host "       C-Learning Platform"
Write-Host "🚀" * 20
Write-Host ""

$ErrorActionPreference = "Stop"

# 检查是否在 Git 仓库中
if (-not (Test-Path ".git")) {
    Write-Host "❌ 错误：当前目录不是 Git 仓库！" -ForegroundColor Red
    Write-Host "请先执行: git init" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ 当前目录是 Git 仓库" -ForegroundColor Green
Write-Host ""

# 显示将要提交的文件
Write-Host "📋 准备提交的文件：" -ForegroundColor Cyan
Write-Host ""

$files = @(
    # 核心修复文件
    "app/config.py",
    "app/__init__.py", 
    "app/routes/ai_assistant.py",
    
    # Docker 和部署配置
    "Dockerfile",
    "gunicorn.conf.py",
    
    # 文档和工具（新增）
    "KOYEB_DEPLOYMENT_GUIDE.md",
    "FIXES_SUMMARY.md",
    "check_deployment.py",
    "test_db_connection.py",
    ".env.production.example",
    
    # 配置文件更新
    ".gitignore"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (不存在)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🔒 安全检查：以下文件将被忽略（不会提交）：" -ForegroundColor Yellow
Write-Host "  🚫 .env (本地开发配置)"
Write-Host "  🚫 .env.production (生产环境配置)"  
Write-Host "  🚫 deployment_check_report.json"
Write-Host ""

# 确认继续
$confirm = Read-Host "❓ 是否继续？(Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host ""
    Write-Host "❌ 已取消操作" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "⏳ 正在执行 Git 操作..." -ForegroundColor Yellow
Write-Host ""

try {
    # 步骤 1: 添加文件
    Write-Host "[1/4] 📦 添加文件到暂存区..." -ForegroundColor Cyan
    
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
    
    Write-Host "  ✓ 文件添加成功" -ForegroundColor Green
    
    # 步骤 2: 创建 commit
    Write-Host ""
    Write-Host "[2/4] 🔖 创建 Commit..." -ForegroundColor Cyan
    
    $commitMessage = @"
fix: 修复公网部署问题并优化本地开发配置

主要修复内容：
1. 移除硬编码的不安全默认值（config.py）
2. 添加环境变量验证机制（__init__.py, config.py）
3. 改进数据库连接错误处理和提示
4. 动态设置 HSTS 安全头（支持 HTTP/HTTPS 自动检测）
5. Dockerfile 添加 g++ 编译器支持 Linux/Docker
6. 改进编译器检测逻辑支持跨平台

新增功能：
- Koyeb 部署完整指南 (KOYEB_DEPLOYMENT_GUIDE.md)
- 部署前自动化检查工具 (check_deployment.py)
- 数据库连接测试脚本 (test_db_connection.py)
- 生产环境变量模板 (.env.production.example)
- 修复总结文档 (FIXES_SUMMARY.md)

安全改进：
- 强制要求 SECRET_KEY 环境变量
- 生产环境缺少必需配置时阻止启动
- 完善 .gitignore 保护敏感文件

配置恢复：
- 恢复原始数据库名称 learning_platform
- 更新本地开发环境配置
"@
    
    git commit -m $commitMessage
    
    Write-Host "  ✓ Commit 创建成功" -ForegroundColor Green
    
    # 步骤 3: 查看状态
    Write-Host ""
    Write-Host "[3/4] 📊 查看 Git 状态..." -ForegroundColor Cyan
    
    git status --short
    
    Write-Host ""
    
    # 步骤 4: 推送到远程仓库
    Write-Host "[4/4] 🚀 推送到 GitHub..." -ForegroundColor Cyan
    
    # 尝试推送
    $pushResult = git push origin main 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 推送成功！" -ForegroundColor Green
        Write-Host ""
        
        # 获取远程 URL
        $remoteUrl = git remote get-url origin
        Write-Host "🌐 远程仓库：$remoteUrl" -ForegroundColor Cyan
        
        # 获取最新 commit 信息
        $lastCommit = git log -1 --pretty=format:"%h - %s (%cr)"
        Write-Host "📝 最新提交：$lastCommit" -ForegroundColor Cyan
        
    } else {
        Write-Host ""
        Write-Host "⚠️  推送遇到问题，尝试其他分支名..." -ForegroundColor Yellow
        
        # 尝试 master 分支
        git push origin master 2>&1
        
        if ($LASTEXITCODE -neq 0) {
            Write-Host ""
            Write-Host "❌ 推送失败！可能的原因：" -ForegroundColor Red
            Write-Host "  1. 远程仓库不存在或无权限" -ForegroundColor Yellow
            Write-Host "  2. 需要先拉取远程更改 (git pull)" -ForegroundColor Yellow
            Write-Host "  3. 分支名称不匹配" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "💡 请手动执行以下命令：" -ForegroundColor Cyan
            Write-Host "  git remote -v          # 检查远程仓库" -ForegroundColor White
            Write-Host "  git branch -a          # 查看所有分支" -ForegroundColor White
            Write-Host "  git pull origin main   # 先拉取再推送" -ForegroundColor White
        }
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ 发生错误: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 提示：" -ForegroundColor Yellow
    Write-Host "  如果是首次推送，需要先添加远程仓库：" -ForegroundColor White
    Write-Host "  git remote add origin <你的GitHub仓库URL>" -ForegroundColor White
    Write-Host "  git push -u origin main" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "="*60
Write-Host "✨ 操作完成！" -ForegroundColor Green
Write-Host "="*60
Write-Host ""
Write-Host "📖 下一步：" -ForegroundColor Cyan
Write-Host "  1. 访问 GitHub 查看推送的代码" -ForegroundColor White
Write-Host "  2. 如需部署到 Koyeb，参考 KOYEB_DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "  3. 运行 test_db_connection.py 测试数据库连接" -ForegroundColor White
Write-Host ""
