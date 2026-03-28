#!/bin/bash
set -e

echo "🚀 开始部署 GMSP 中转服务器..."

# 更新系统
echo "📦 更新系统..."
apt update && apt upgrade -y

# 安装依赖
echo "📦 安装依赖..."
apt install -y python3 python3-venv python3-pip git screen htop

# 创建目录
echo "📁 创建工作目录..."
mkdir -p /opt/gmsp
cd /opt/gmsp

# 克隆代码
echo "📥 克隆代码仓库..."
if [ ! -d "GMSPforServer" ]; then
    git clone https://github.com/onlyjokers/GMSPforServer.git
else
    echo "⚠️  代码目录已存在，跳过克隆"
fi
cd GMSPforServer

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建 systemd 服务
echo "⚙️  配置 systemd 服务..."
cat > /etc/systemd/system/gmsp-relay.service << 'EOF'
[Unit]
Description=GMSP WebSocket Relay Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gmsp/GMSPforServer
Environment="PATH=/opt/gmsp/GMSPforServer/venv/bin"
ExecStart=/opt/gmsp/GMSPforServer/venv/bin/python3 src/relay_server.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable gmsp-relay
systemctl start gmsp-relay

# 等待服务启动
sleep 2

# 检查服务状态
if systemctl is-active --quiet gmsp-relay; then
    echo ""
    echo "✅ 部署完成！服务已成功启动"
    echo ""
    echo "📍 服务器运行在 0.0.0.0:8080"
    echo "🔍 查看状态: systemctl status gmsp-relay"
    echo "📋 查看日志: journalctl -u gmsp-relay -f"
    echo ""
    echo "⚠️  重要提醒："
    echo "   1. 请在阿里云安全组开放 8080 端口"
    echo "   2. 如果使用防火墙，执行: ufw allow 8080/tcp"
    echo ""
    echo "🧪 测试连接:"
    echo "   python3 scripts/test_connection.py ws://$(curl -s ifconfig.me):8080"
else
    echo ""
    echo "❌ 服务启动失败，请查看日志："
    echo "   journalctl -u gmsp-relay -n 50"
    exit 1
fi
