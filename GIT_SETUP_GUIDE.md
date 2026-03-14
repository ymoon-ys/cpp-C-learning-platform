# Git安装和GitHub配置指南

## 第一步：安装Git

1. 访问Git官网下载：https://git-scm.com/download/win
2. 下载Windows版本的Git安装包
3. 运行安装程序，使用默认设置一路点击"Next"完成安装
4. 安装完成后，重启终端或电脑

## 第二步：验证Git安装

打开命令提示符（CMD）或PowerShell，运行：
```bash
git --version
```
如果显示Git版本号，说明安装成功。

## 第三步：配置Git用户信息

在项目根目录（C:\Users\18341\Desktop\C-learning-platform）打开Git Bash或命令提示符，运行：

```bash
git config user.name "你的GitHub用户名"
git config user.email "你的GitHub邮箱"
```

## 第四步：初始化Git仓库

在项目根目录运行以下命令：

```bash
git init
```

## 第五步：连接GitHub仓库

```bash
git remote add origin https://github.com/ymoon-ys/cpp-C-learning-platform.git
```

## 第六步：首次提交并推送到GitHub

```bash
git add .
git commit -m "初始提交：完整C++学习平台项目"
git push -u origin master
```

**注意**：首次推送时会要求输入GitHub的用户名和密码（或Personal Access Token）。

## 第七步：日常备份使用

每次修改文件后，双击运行 `auto_backup.bat` 即可自动备份到GitHub！

---

## 如何创建GitHub Personal Access Token（推荐）

1. 访问GitHub：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 点击 "Generate token"
5. 复制生成的token（只显示一次，务必保存好）
6. 推送时用这个token代替密码

---

## 查看备份历史

- 本地查看：`git log`
- GitHub查看：访问 https://github.com/ymoon-ys/cpp-C-learning-platform

## 快速参考

| 命令 | 说明 |
|------|------|
| `git status` | 查看当前状态 |
| `git add .` | 添加所有文件 |
| `git commit -m "描述"` | 提交修改 |
| `git push` | 推送到GitHub |
| `git pull` | 从GitHub拉取 |

---

**重要提示**：完成以上步骤后，以后每次修改文件只需要双击 `auto_backup.bat` 即可自动备份！
