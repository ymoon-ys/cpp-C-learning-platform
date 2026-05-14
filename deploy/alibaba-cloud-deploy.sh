#!/bin/bash
# ============================================
# C语言学习平台 - 阿里云 ECS 一键部署脚本
# ============================================

set -e

echo "🚀 开始部署 C语言学习平台到阿里云 ECS..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 root 用户运行此脚本"
    exit 1
fi

# 步骤 1: 更新系统包
echo ""
echo "===== 步骤 1/6: 更新系统包 ====="
apt update && apt upgrade -y
print_success "系统包更新完成"

# 步骤 2: 安装必要工具
echo ""
echo "===== 步骤 2/6: 安装 Docker 和工具 ====="
apt install -y \
    git \
    curl \
    wget \
    nginx \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose-v2 \
    certbot \
    python3-certbot-nginx

# 启动 Docker
systemctl enable docker
systemctl start docker
print_success "Docker 和工具安装完成"

# 步骤 3: 配置防火墙
echo ""
echo "===== 步骤 3/6: 配置防火墙 ====="
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8000/tcp comment 'Application'

# 启用 UFW（交互式确认）
if ! ufw status | grep -q "active"; then
    print_warning "请手动启用防火墙: ufw enable"
else
    print_success "防火墙已配置"
fi

# 步骤 4: 克隆项目代码
echo ""
echo "===== 步骤 4/6: 克隆项目代码 ====="
cd /opt || cd /home

if [ ! -d "cpp-C-learning-platform" ]; then
    git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git
fi

cd cpp-C-learning-platform
git pull origin main
print_success "项目代码准备完成"

# 步骤 5: 检查环境配置
echo ""
echo "===== 步骤 5/6: 检查环境配置 ====="

if [ ! -f ".env.production" ]; then
    if [ -f ".env.example" ] || [ -f ".env.production.example" ]; then
        print_warning ".env.production 不存在，正在从模板创建..."
        cp .env.production.example .env.production
        print_error "请编辑 .env.production 文件填入实际的数据库连接信息和 API 密钥！"
        print_error "然后重新运行此脚本继续部署。"
        exit 1
    else
        print_error ".env.production 或 .env.example 都不存在！"
        exit 1
    fi
fi

print_success "环境配置文件存在"

# 步骤 6: 构建并启动应用
echo ""
echo "===== 步骤 6/6: 构建并启动应用 ====="

# 使用生产环境 compose 文件
if [ -f "docker-compose.production.yml" ]; then
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
else
    docker-compose --env-file .env.production up -d --build
fi

# 等待容器启动
sleep 10

# 显示状态
echo ""
echo "========================================="
docker ps --filter name=c-learning-web
echo "========================================="

# 配置 Nginx
echo ""
echo "===== 配置 Nginx 反向代理 ====="
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

if [ -f "deploy/nginx/c-learning.conf" ]; then
    cp deploy/nginx/c-learning.conf /etc/nginx/sites-available/c-learning
else
    # 如果没有配置文件，创建基本配置
    cat > /etc/nginx/sites-available/c-learning << 'EOF'
server {
    listen 80 default_server;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 100M;
    }
}
EOF
fi

ln -sf /etc/nginx/sites-available/c-learning /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
print_success "Nginx 配置完成"

# 完成
echo ""
echo "========================================="
print_success "🎉 部署完成！"
echo "========================================="
echo ""
echo "访问方式:"
echo "  直接访问: http://<你的ECS公网IP>:8000"
echo "  通过Nginx: http://<你的ECS公网IP>"
echo ""
echo "默认账号:"
echo "  管理员: admin / admin123"
echo "  教师:   teacher / teacher123"
echo "  学生:   student / student123"
echo ""
echo "查看日志: docker logs -f c-learning-web"
echo "重启服务: docker-compose restart"
