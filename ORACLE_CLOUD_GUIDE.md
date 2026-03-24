# Oracle Cloud 部署完整指南

## 第一步：注册 Oracle Cloud 账号（5-10 分钟）

### 1.1 准备材料
- ✅ 邮箱地址
- ✅ 手机号码（支持中国 +86）
- ✅ 信用卡/借记卡（银联可，用于验证身份，**不扣费**）

### 1.2 注册步骤

1. **访问官网**
   - 打开 https://www.oracle.com/cloud/free/
   - 点击 **Start for free**

2. **填写账号信息**
   - Cloud Account Name：随便填（如 `my-account`）
   - First Name / Last Name：用拼音（如 `Xiao Ming`）
   - Email Address：常用邮箱
   - Password：强密码

3. **填写联系方式**
   - Country/Region：China
   - Phone Number：+86 手机号
   - 接收验证码并验证

4. **填写支付信息**
   - Card Number：卡号
   - Expiration：月/年
   - CVV：背面 3 位码
   - **说明**：只验证身份，不会扣费

5. **等待审核**
   - 通常几分钟到几小时
   - 审核通过后会收到邮件

### 1.3 常见问题

**Q: 注册失败怎么办？**
- 换浏览器（推荐 Chrome）
- 换时间段再试
- 确保信息真实

**Q: 信用卡被拒？**
- 确认卡支持国际支付
- 试试 Visa/MasterCard
- 有些银联卡也支持

---

## 第二步：创建云服务器（5 分钟）

### 2.1 登录控制台
1. 访问 https://cloud.oracle.com
2. 输入邮箱和密码登录

### 2.2 创建实例

1. **进入创建页面**
   - 点击左上角菜单 ☰
   - 选择 **Compute** → **Instances**
   - 点击 **Create instance**

2. **配置实例**
   ```
   Name: learning-platform
   Compartment: 选择你的 compartment
   
   Availability domain: 任选一个
   
   Image: 
   - 点击 Change Image
   - 选择 Canonical Ubuntu 22.04
   
   Shape:
   - 点击 Change Shape
   - 选择 VM.Standard.A1.Flex (ARM)
   - OCPUs: 4
   - Memory: 24 GB
   
   Networking:
   - 勾选 Assign a public IPv4 address
   
   Boot volume:
   - 默认 50GB（够用）
   ```

3. **添加 SSH 密钥**
   - 选择 **Generate a key pair for me**
   - 点击 **Download private key**
   - 保存为 `oracle_key.pem`
   - **重要**：保存好，丢失无法找回！

4. **创建实例**
   - 点击 **Create**
   - 等待 3-5 分钟
   - 记录 **Public IP address**

---

## 第三步：连接服务器（2 分钟）

### 3.1 准备 SSH 密钥

如果使用 Windows，需要转换密钥格式：

```bash
# 在 Git Bash 或 PowerShell 执行
ssh-keygen -p -m PEM -f ~/.ssh/id_rsa
```

### 3.2 连接服务器

**方法 1：使用 PowerShell**
```powershell
ssh -i <私钥路径> ubuntu@<公网 IP>
```

例如：
```powershell
ssh -i C:\Users\你的用户名\.ssh\oracle_key.pem ubuntu@129.123.123.123
```

**方法 2：使用 Putty**
1. 下载 Putty：https://www.putty.org/
2. 转换密钥：使用 PuTTYgen
3. 连接：输入 IP，选择私钥

**首次连接**会提示确认指纹，输入 `yes`

---

## 第四步：一键部署应用（10 分钟）

### 4.1 执行部署脚本

连接服务器后，执行：

```bash
# 下载部署脚本
cd ~
curl -O https://raw.githubusercontent.com/ymoon-ys/cpp-C-learning-platform/main/deploy.sh

# 添加执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

### 4.2 等待部署完成

脚本会自动：
- ✅ 更新系统
- ✅ 安装 Python、MySQL、Nginx
- ✅ 配置防火墙
- ✅ 克隆代码
- ✅ 创建虚拟环境
- ✅ 安装依赖
- ✅ 配置数据库
- ✅ 初始化表结构
- ✅ 创建 systemd 服务
- ✅ 配置 Nginx 反向代理

### 4.3 修改配置

部署完成后，编辑环境变量：

```bash
nano /var/www/cpp-C-learning-platform/.env
```

修改以下内容：
```
MYSQL_PASSWORD=你的数据库密码
SECRET_KEY=你的随机密钥
```

**生成随机密钥**：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4.4 重启服务

```bash
sudo systemctl restart learning-platform
```

---

## 第五步：测试访问

### 5.1 访问网站

浏览器打开：
```
http://<你的 Oracle Cloud 公网 IP>
```

### 5.2 测试功能

- ✅ 访问首页
- ✅ 注册账号
- ✅ 登录
- ✅ 访问管理后台

---

## 第六步：配置防火墙（重要！）

### 6.1 Oracle Cloud 控制台配置

1. 登录 Oracle Cloud 控制台
2. 进入 **Compute** → **Instances**
3. 点击你的实例名称
4. 点击 **Primary VNIC**
5. 点击 **Subnet**
6. 点击 **Security Lists**
7. 点击 **Add Ingress Rules**
8. 添加规则：
   ```
   Source CIDR: 0.0.0.0/0
   Destination port range: 80
   Description: HTTP
   ```
9. 再添加一条：
   ```
   Source CIDR: 0.0.0.0/0
   Destination port range: 443
   Description: HTTPS
   ```

### 6.2 服务器内部防火墙

部署脚本已自动配置，检查：
```bash
sudo ufw status
```

应该看到：
```
22/tcp                     ALLOW
80/tcp                     ALLOW
443/tcp                    ALLOW
```

---

## 第七步：配置域名（可选）

### 7.1 使用免费域名

1. **Freenom 免费域名**
   - 访问 https://www.freenom.com
   - 注册账号
   - 选择免费域名（.tk, .ml, .ga 等）
   - 按提示完成注册

2. **配置 DNS**
   - 进入 Freenom 域名管理
   - 点击 **Manage Domain**
   - 选择 **Manage Freenom DNS**
   - 添加 A 记录：
     ```
     Name: @
     Type: A
     Value: <Oracle Cloud 公网 IP>
     TTL: 3600
     ```

### 7.2 绑定域名到 Oracle Cloud

在 Nginx 配置中修改：
```bash
sudo nano /etc/nginx/sites-available/learning-platform
```

修改 `server_name`：
```nginx
server_name yourdomain.com www.yourdomain.com;
```

重启 Nginx：
```bash
sudo systemctl restart nginx
```

---

## 第八步：安装 SSL 证书（可选）

### 8.1 安装 Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2 获取证书

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

按提示：
1. 输入邮箱
2. 同意条款
3. 选择是否重定向到 HTTPS（推荐 Yes）

### 8.3 自动续期

Certbot 会自动配置续期，检查：
```bash
sudo systemctl status certbot.timer
```

---

## 常用命令

### 查看服务状态
```bash
# 应用状态
sudo systemctl status learning-platform

# Nginx 状态
sudo systemctl status nginx

# MySQL 状态
sudo systemctl status mysql
```

### 查看日志
```bash
# 应用日志
sudo journalctl -u learning-platform -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 重启服务
```bash
sudo systemctl restart learning-platform
sudo systemctl restart nginx
sudo systemctl restart mysql
```

### 进入数据库
```bash
mysql -u learning -p learning_platform
```

---

## 费用说明

| 项目 | 费用 |
|------|------|
| 云服务器（4 核 24G） | **免费**（永久） |
| 存储（200GB） | **免费** |
| 流量（10TB/月） | **免费** |
| 域名（可选） | ¥0（Freenom 免费） |
| SSL 证书 | **免费** |
| **总计** | **¥0/月** |

---

## 故障排查

### 无法 SSH 连接
- 检查 Oracle Cloud 防火墙规则
- 确认私钥路径正确
- 检查安全组配置

### 网站无法访问
```bash
# 检查服务状态
sudo systemctl status learning-platform
sudo systemctl status nginx

# 检查端口
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000

# 检查防火墙
sudo ufw status
```

### 数据库连接失败
```bash
# 检查 MySQL 状态
sudo systemctl status mysql

# 检查数据库用户
mysql -u root -p
SELECT user, host FROM mysql.user;
```

### 资源不足
```bash
# 查看磁盘空间
df -h

# 查看内存使用
free -h

# 查看 CPU 使用
top
```

---

## 备份数据库

### 手动备份
```bash
mysqldump -u learning -p learning_platform > backup_$(date +%Y%m%d).sql
```

### 自动备份脚本
```bash
nano ~/backup_db.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR=~/db_backups
mkdir -p $BACKUP_DIR
mysqldump -u learning -p'密码' learning_platform > $BACKUP_DIR/backup_$(date +%Y%m%d).sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

添加定时任务：
```bash
crontab -e
```

添加：
```
0 2 * * * /bin/bash ~/backup_db.sh
```

---

## 下一步

恭喜！你的 C-learning-platform 已经在 Oracle Cloud 上运行了！

- 访问：`http://<你的公网 IP>`
- 完全免费，永久使用
- 24 小时稳定运行
- 无需担心费用

有任何问题随时询问！
