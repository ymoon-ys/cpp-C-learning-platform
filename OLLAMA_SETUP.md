# Ollama 本地模型安装指南

## 1. 下载安装 Ollama

访问 https://ollama.com/download 下载 Windows 版本安装包，或者使用命令行安装：

```powershell
# 使用 winget 安装（推荐）
winget install Ollama.Ollama

# 或者手动下载安装包后运行
```

## 2. 验证安装

安装完成后，打开新的 PowerShell 窗口：

```powershell
ollama --version
```

应该显示版本号，如：`ollama version 0.3.0`

## 3. 拉取模型

根据你的电脑配置选择合适的模型：

```powershell
# 轻量级模型（推荐，适合大多数电脑）
ollama pull qwen3:8b

# 更强的模型（需要更多内存）
ollama pull qwen3:14b

# 编程专用模型
ollama pull qwen3-coder:30b

# 查看已安装的模型
ollama list
```

## 4. 启动 Ollama 服务

```powershell
# 启动服务（保持窗口打开）
ollama serve

# 或者设置为系统服务自动启动（需要管理员权限）
```

## 5. 验证服务运行

```powershell
# 测试 API 是否可用
curl http://localhost:11434/api/tags
```

## 6. 配置 .env

```env
# 切换到 Ollama
AI_PROVIDER=ollama

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_TIMEOUT=180

# Minimax 作为备用
MINIMAX_API_KEY=sk-xxx
MINIMAX_BASE_URL=https://api.minimaxi.chat/v1
MINIMAX_MODEL=MiniMax-M2.7
MINIMAX_TIMEOUT=120

# 自动降级
AI_FALLBACK_ENABLED=true
AI_FALLBACK_ORDER=ollama,minimax,qwen
```

## 7. 重启应用

修改 .env 后重启 Flask 应用即可使用 Ollama 本地模型。

## 常见问题

### Q: Ollama 服务无法启动？
A: 检查端口 11434 是否被占用，或者尝试以管理员身份运行。

### Q: 模型下载很慢？
A: Ollama 会自动选择下载源，如果慢可以尝试使用代理。

### Q: 内存不足？
A: 使用更小的模型，如 `qwen3:8b` 需要约 8GB 内存，`qwen3:14b` 需要约 14GB。

### Q: 如何切换回 Minimax？
A: 在 .env 中将 `AI_PROVIDER=minimax`，或在前端设置面板中切换。
