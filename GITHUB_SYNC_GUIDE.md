# GitHub 自动同步指南

> 📝 **使用说明**：每次修改代码后，按照本文档操作即可同步到 GitHub

---

## 🚀 **一键同步脚本**

### **Windows PowerShell 脚本** (`sync_github.ps1`)

```powershell
# =====================================================
# GitHub 一键同步脚本
# 使用方法：右键 → 使用 PowerShell 运行
# 或：powershell -ExecutionPolicy Bypass -File sync_github.ps1
# =====================================================

Write-Host "🔄 开始同步到 GitHub..." -ForegroundColor Cyan

# 1. 确保 Git 在 PATH 中
$env:Path += ";C:\Program Files\Git\cmd"

# 2. 检查 Git 是否可用
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git 未找到！请先安装 Git" -ForegroundColor Red
    exit 1
}

# 3. 添加所有文件
Write-Host "📁 添加文件..." -ForegroundColor Yellow
git add -A

# 4. 检查是否有变更
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✅ 没有需要提交的变更" -ForegroundColor Green
    exit 0
}

# 5. 提交变更
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$commitMsg = "Update: Auto-sync $timestamp"
Write-Host "💾 提交变更: $commitMsg" -ForegroundColor Yellow
git commit -m $commitMsg

# 6. 推送到 GitHub
Write-Host "⬆️ 推送到 GitHub..." -ForegroundColor Yellow
try {
    git push origin main
    Write-Host "✅ 成功推送到 GitHub！" -ForegroundColor Green
} catch {
    Write-Host "❌ 推送失败！尝试重新配置 SSL..." -ForegroundColor Red
    
    # 尝试修复 SSL 问题
    git config --global http.sslBackend openssl
    
    Write-Host "🔧 已配置 SSL，正在重试..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 重试成功！" -ForegroundColor Green
    } else {
        Write-Host "❌ 仍然失败，请检查网络连接" -ForegroundColor Red
        exit 1
    }
}
```

### **Windows 批处理脚本** (`sync_github.bat`)

```batch
@echo off
chcp 65001 >nul
title GitHub 同步工具

echo ============================================
echo   GitHub 一键同步工具
echo ============================================
echo.

:: 设置 Git PATH
set "PATH=%PATH%;C:\Program Files\Git\cmd"

:: 检查 Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Git 未找到！请先安装 Git
    pause
    exit /b 1
)

:: 添加文件
echo [1/4] 添加文件...
git add -A

:: 检查是否有变更
git status --porcelain | findstr /r "." >nul
if %errorlevel% neq 0 (
    echo [完成] 没有需要提交的变更
    pause
    exit /b 0
)

:: 生成提交信息
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set date=%%a-%%b-%%c
for /f "tokens=1,2 delims=: " %%a in ('time /t') do set time=%%a:%%b

echo [2/4] 提交变更...
git commit -m "Update: Auto-sync %date% %time%"

:: 推送
echo [3/4] 推送到 GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo [✓ 完成] 成功推送到 GitHub！
) else (
    echo.
    echo [!] 推送失败，尝试修复 SSL...
    git config --global http.sslBackend openssl
    echo [重试] 正在重新推送...
    git push origin main
)

echo.
echo [4/4] 同步完成！
pause
```

---

## 📋 **手动同步步骤（详细版）**

### **步骤 1：打开终端**

#### **方法 A：VS Code 集成终端**
1. 打开 VS Code
2. 按 `` Ctrl + ` `` (反引号)
3. 或菜单：`终端` → `新建终端`

#### **方法 B：PowerShell**
1. 按 `Win + R`
2. 输入 `powershell`
3. 回车

#### **方法 C：Git Bash**
1. 右键点击项目文件夹
2. 选择 `Git Bash Here`

---

### **步骤 2：配置 Git 环境（如果需要）**

```powershell
# 如果提示找不到 git，执行此命令：
$env:Path += ";C:\Program Files\Git\cmd"

# 验证 Git 是否可用：
git --version
# 应该显示: git version 2.x.x
```

---

### **步骤 3：查看当前状态**

```bash
git status
```

**输出示例**：
```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
        modified:   app/routes/student.py
        modified:   app/templates/student/lesson_detail.html

no changes added to commit
```

---

### **步骤 4：添加所有变更**

```bash
git add -A
```

**参数说明**：
- `-A` = 所有文件（包括新增、修改、删除）
- `.` = 当前目录下的所有变更

---

### **步骤 5：提交变更**

```bash
git commit -m "你的提交信息"
```

**提交信息规范**：

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `Feature:` | `Feature: Add video support` |
| 修复 | `Fix:` | `Fix: Resolve login issue` |
| 更新 | `Update:` | `Update: Improve UI styling` |
| 重构 | `Refactor:` | `Refactor: Simplify code structure` |
| 文档 | `Docs:` | `Docs: Update README` |

**示例**：
```bash
git commit -m "Fix: Repair delete button functionality"
git commit -m "Feature: Add Base64 file persistence"
git commit -m "Update: Clean up documentation files"
```

---

### **步骤 6：推送到 GitHub**

```bash
git push origin main
```

**参数说明**：
- `push` = 推送
- `origin` = 远程仓库名称（默认）
- `main` = 分支名称

**成功输出**：
```
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
...
To https://github.com/ymoon-ys/cpp-C-learning-platform.git
   37b9f01..23c307b  main -> main
```

---

## 🔧 **常见问题解决**

### **问题 1：Git 未找到**

**错误信息**：
```
git : 无法将"git"项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

**解决方案**：
```powershell
# 临时解决（仅当前会话）：
$env:Path += ";C:\Program Files\Git\cmd"

# 永久解决（添加到系统环境变量）：
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Git\cmd", "Machine")
```

---

### **问题 2：SSL 错误**

**错误信息**：
```
fatal: unable to access 'https://github.com/...': 
OpenSSL SSL_read: error:0A000126:SSL routines::unexpected eof while reading
```

**解决方案**：
```bash
# 方法 1：配置 SSL 后端
git config --global http.sslBackend openssl

# 方法 2：增加缓冲区大小
git config --global http.postBuffer 524288000

# 方法 3：重试推送
git push origin main
```

---

### **问题 3：网络连接失败**

**错误信息**：
```
fatal: unable to access 'https://github.com/...': Connection was reset
```

**解决方案**：

1. **检查 VPN/代理**：
   ```bash
   # 如果使用代理，配置 Git 代理
   git config --global http.proxy http://127.0.0.1:7890
   git config --global https.proxy http://127.0.0.1:7890
   ```

2. **切换到 SSH**（可选）：
   ```bash
   git remote set-url origin git@github.com:ymoon-ys/cpp-C-learning-platform.git
   ```

3. **等待网络恢复后重试**

---

### **问题 4：权限被拒绝**

**错误信息**：
```
error: failed to push some refs to 'https://github.com/...'
! [rejected] main -> main (non-fast-forward)
```

**解决方案**：
```bash
# 先拉取远程更新，再推送
git pull origin main --rebase
git push origin main
```

---

## ⚡ **高级技巧**

### **1️⃣ 查看提交历史**

```bash
# 最近 5 次提交
git log --oneline -5

# 详细历史
git log --oneline --all --graph
```

### **2️⃣ 撤销未提交的更改**

```bash
# 撤销某个文件的修改
git restore <file_path>

# 撤销所有修改
git restore .

# 撤销暂存的更改
git reset HEAD
```

### **3️⃣ 创建新分支**

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 推送新分支
git push origin feature/new-feature
```

### **4️⃣ 查看远程仓库信息**

```bash
# 查看远程仓库
git remote -v

# 查看详细信息
git remote show origin
```

---

## 🎯 **推荐工作流程**

### **日常开发流程**：

```
1. 编写/修改代码
   ↓
2. 本地测试通过
   ↓
3. 运行同步脚本或手动执行：
   ├── git add -A          （添加所有文件）
   ├── git commit -m "..."  （提交）
   └── git push origin main （推送）
   ↓
4. 等待 Koyeb 自动部署（~3分钟）
   ↓
5. 测试线上功能
```

### **完整同步命令（一行搞定）**：

```bash
$env:Path += ";C:\Program Files\Git\cmd"; git add -A; git commit -m "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"; git push origin main
```

---

## 📌 **快捷方式设置**

### **在 Windows 资源管理器中添加右键菜单**：

1. 创建文件 `GitHub Sync.bat`（内容见上方）
2. 复制到：`C:\Users\你的用户名\AppData\Roaming\Microsoft\Windows\SendTo\`
3. 现在**右键任何文件夹** → **发送到** → **GitHub Sync**

---

## ✅ **验证清单**

推送前确认：

- [ ] 代码已本地测试通过
- [ ] 没有包含敏感信息（密码、API Key 等）
- [ ] 提交信息清晰明了
- [ ] 网络连接正常

推送后确认：

- [ ] GitHub 仓库已更新（刷新页面查看）
- [ ] Koyeb 开始自动部署（查看 Deployments 标签）
- [ ] 线上功能正常（等待部署完成后测试）

---

## 📞 **获取帮助**

### **常用 Git 命令速查**：

| 操作 | 命令 |
|------|------|
| 查看状态 | `git status` |
| 查看差异 | `git diff` |
| 添加文件 | `git add <file>` |
| 提交 | `git commit -m "msg"` |
| 推送 | `git push` |
| 拉取 | `git pull` |
| 查看日志 | `git log` |
| 撤销修改 | `git restore <file>` |

### **相关资源**：

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 快速入门](https://docs.github.com/en/get-started)
- [Koyeb 部署文档](https://www.koyeb.com/docs)

---

**🎉 最后更新时间：2026-04-05**
