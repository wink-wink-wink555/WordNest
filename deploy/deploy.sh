#!/bin/bash
set -e

PROJECT_DIR="/root/project1/WordNest"
cd "$PROJECT_DIR"

echo "=== WordNest 部署脚本 ==="

# 1. 创建虚拟环境
echo "[1/6] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
echo "[2/6] 安装 Python 依赖..."
pip install -r requirements.txt
pip install gunicorn

# 3. 创建日志目录
echo "[3/6] 创建日志目录..."
mkdir -p /var/log/wordnest

# 4. 配置 systemd 服务
echo "[4/6] 配置 systemd 服务..."
cp deploy/wordnest.service /etc/systemd/system/wordnest.service
systemctl daemon-reload
systemctl enable wordnest
systemctl restart wordnest

# 5. 配置 Nginx
echo "[5/6] 配置 Nginx..."
cp deploy/nginx_wordnest.conf /etc/nginx/conf.d/wordnest.conf
nginx -t && systemctl reload nginx

# 6. 检查状态
echo "[6/6] 检查服务状态..."
systemctl status wordnest --no-pager

echo ""
echo "=== 部署完成 ==="
echo "网站地址: http://www.manbaout.com"
echo ""
echo "后续步骤:"
echo "  1. 修改 /etc/systemd/system/wordnest.service 中的 SECRET_KEY"
echo "  2. 确保域名 www.manbaout.com 的 DNS A 记录指向本服务器 IP"
echo "  3. (可选) 配置 HTTPS: certbot --nginx -d www.manbaout.com -d manbaout.com"
