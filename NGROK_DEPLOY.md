# ngrok 快速部署指南

## 什么是 ngrok

ngrok 可以将本地服务暴露到公网，获得一个临时的公网域名。

**优点**：
- ✅ 完全免费
- ✅ 不需要绑卡
- ✅ 1 分钟搞定
- ✅ 适合测试和演示

**缺点**：
- ⚠️ 域名每次启动都会变
- ⚠️ 需要保持电脑开机
- ⚠️ 有流量限制（但够用）

---

## 快速开始

### 步骤 1：下载 ngrok

访问 https://ngrok.com/download
- 点击 **Download ngrok**
- 下载 Windows 版本

### 步骤 2：注册获取 Token

1. 访问 https://ngrok.com/signup
2. 用邮箱注册（免费）
3. 登录后复制你的 **Authtoken**

### 步骤 3：配置 ngrok

解压下载的 ngrok，然后：

```bash
# 配置你的 token（替换成你的）
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### 步骤 4：启动 Flask 应用

```bash
# 在项目目录启动
python run.py
```

应用会运行在 `http://localhost:5001`

### 步骤 5：启动 ngrok

打开**新的终端**，运行：

```bash
ngrok http 5001
```

### 步骤 6：获取公网域名

ngrok 会显示类似这样的信息：

```
Forwarding: https://abc123.ngrok.io -> http://localhost:5001
```

这个 `https://abc123.ngrok.io` 就是你的公网域名！

分享给别人即可访问。

---

## 每次使用

1. 启动 Flask：`python run.py`
2. 启动 ngrok：`ngrok http 5001`
3. 使用显示的域名

**注意**：每次重启 ngrok 域名会变，可以在 ngrok 后台配置固定域名（需要付费）。

---

## 进阶：配置固定域名（可选）

如果不想每次域名都变：

1. 登录 ngrok 后台
2. 进入 **Domains**
3. 添加一个免费域名
4. 启动时用：`ngrok http --domain=your-domain.ngrok.io 5001`

---

## 故障排查

### 端口不对
确保 ngrok 指向 5001 端口（Flask 默认端口）

### 连接超时
检查防火墙是否允许 5001 端口

### 速度慢
ngrok 免费服务器在国外，速度可能较慢
