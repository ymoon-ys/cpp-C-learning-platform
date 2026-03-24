#!/bin/bash

# Oracle Cloud 服务器初始化部署脚本
# 用于快速部署 C-learning-platform

set -e

echo "========================================="
echo "C-learning-platform 部署脚本"
echo "========================================="

# 更新系统
echo "[1/10] 更新系统..."
sudo apt update && sudo apt upgrade -y

# 安装必要软件
echo "[2/10] 安装 Python、Git、MySQL、Nginx..."
sudo apt install -y python3 python3-pip python3-venv git curl mysql-server nginx

# 配置防火墙
echo "[3/10] 配置防火墙..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# 创建应用目录
echo "[4/10] 创建应用目录..."
sudo mkdir -p /var/www/cpp-C-learning-platform
sudo chown -R $USER:$USER /var/www/cpp-C-learning-platform
cd /var/www/cpp-C-learning-platform

# 克隆代码
echo "[5/10] 克隆代码..."
git clone https://github.com/ymoon-ys/cpp-C-learning-platform.git .

# 创建虚拟环境
echo "[6/10] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 创建环境变量文件
echo "[7/10] 创建环境变量配置..."
cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=learning
MYSQL_PASSWORD=CHANGE_THIS_PASSWORD
MYSQL_DATABASE=learning_platform
SECRET_KEY=CHANGE_THIS_SECRET_KEY
FLASK_ENV=production
FLASK_DEBUG=0
EOF

echo "⚠️  请编辑 .env 文件，修改密码和 SECRET_KEY"

# 配置 MySQL
echo "[8/10] 配置 MySQL 数据库..."
sudo systemctl start mysql
sudo systemctl enable mysql

# MySQL 安全配置
sudo mysql_secure_installation << EOF
n
Y
Y
Y
Y
EOF

# 创建数据库和用户
sudo mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'learning'@'localhost' IDENTIFIED BY 'learning_password_2024';
GRANT ALL PRIVILEGES ON learning_platform.* TO 'learning'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "✅ MySQL 数据库已创建"
echo "   数据库：learning_platform"
echo "   用户：learning"
echo "   密码：learning_password_2024"
echo "⚠️  请修改 .env 文件中的数据库密码"

# 初始化数据库表结构
echo "[9/10] 初始化数据库表..."
source venv/bin/activate
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/var/www/cpp-C-learning-platform')

from app.mysql_database import MySQLDatabase

db = MySQLDatabase(
    host='localhost',
    user='learning',
    password='learning_password_2024',
    database='learning_platform'
)

try:
    db.init_db()
    print("✅ 数据库表初始化成功")
except Exception as e:
    print(f"⚠️  数据库初始化可能已完成：{e}")
PYTHON_EOF

# 创建 systemd 服务
echo "[10/10] 创建 systemd 服务..."
sudo bash -c 'cat > /etc/systemd/system/learning-platform.service << EOF
[Unit]
Description=C-learning-platform Gunicorn instance
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/cpp-C-learning-platform
Environment="PATH=/var/www/cpp-C-learning-platform/venv/bin"
ExecStart=/var/www/cpp-C-learning-platform/venv/bin/gunicorn --config gunicorn.conf.py run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl start learning-platform
sudo systemctl enable learning-platform

# 配置 Nginx
echo "配置 Nginx 反向代理..."
sudo bash -c 'cat > /etc/nginx/sites-available/learning-platform << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/cpp-C-learning-platform/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/cpp-C-learning-platform/uploads;
        expires 30d;
    }
}
EOF'

sudo ln -sf /etc/nginx/sites-available/learning-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "========================================="
echo "✅ 部署完成！"
echo "========================================="
echo ""
echo "服务状态："
sudo systemctl status learning-platform --no-pager
echo ""
echo "访问地址：http://$(curl -s ifconfig.me)"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，修改密码和 SECRET_KEY"
echo "2. 更新 MySQL 密码后，同步修改 .env 文件"
echo "3. 重启服务：sudo systemctl restart learning-platform"
echo ""
