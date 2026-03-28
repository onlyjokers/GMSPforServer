# GMSPforServer 阿里云快速部署

## 最简部署流程（5 分钟）

### 1. 购买阿里云 ECS

- 配置：2核4GB，Ubuntu 22.04
- 记录公网 IP（例如：`121.196.205.73`）

### 2. 开放端口

进入 ECS 控制台 → 安全组 → 添加规则：
- 端口：8080
- 授权对象：0.0.0.0/0

### 3. 连接服务器

```bash
ssh root@你的公网IP
```

### 4. 一键部署

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/onlyjokers/GMSPforServer/master/deploy.sh

# 或者手动创建
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git
mkdir -p /opt/gmsp && cd /opt/gmsp
git clone https://github.com/onlyjokers/GMSPforServer.git
cd GMSPforServer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cat > /etc/systemd/system/gmsp-relay.service << 'EOFS'
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
EOFS
systemctl daemon-reload
systemctl enable gmsp-relay
systemctl start gmsp-relay
echo "✅ 部署完成！"
systemctl status gmsp-relay
EOF

# 执行部署
chmod +x deploy.sh
./deploy.sh
```

### 5. 验证部署

```bash
# 查看服务状态
systemctl status gmsp-relay

# 查看日志
journalctl -u gmsp-relay -f
```

看到 `🚀 GMSP 中转服务器启动` 表示成功。

### 6. 配置客户端

**GMSP 训练端** (`configs/default.json`)：
```json
{
  "profiles": {
    "blenderllm_qwen3_5_4b": {
      "transport": {
        "relay_server": "ws://你的公网IP:8080"
      }
    }
  }
}
```

**GMSPforBlender** (Blender 插件)：
- 服务器地址：`ws://你的公网IP:8080`
- 点击启动服务

---

## 常用命令

```bash
# 查看状态
systemctl status gmsp-relay

# 查看日志
journalctl -u gmsp-relay -f

# 重启服务
systemctl restart gmsp-relay

# 停止服务
systemctl stop gmsp-relay

# 查看连接数
netstat -an | grep 8080 | grep ESTABLISHED | wc -l
```

---

## 故障排查

### 无法连接？

1. **检查安全组**：确保 8080 端口已开放
2. **检查服务**：`systemctl status gmsp-relay`
3. **查看日志**：`journalctl -u gmsp-relay -n 50`
4. **测试端口**：`telnet 你的公网IP 8080`

### 服务无法启动？

```bash
# 查看详细错误
journalctl -u gmsp-relay -n 50 --no-pager

# 手动运行测试
cd /opt/gmsp/GMSPforServer
source venv/bin/activate
python3 src/relay_server.py
```

---

## 完整文档

详细部署指南请查看：[docs/aliyun_deployment.md](docs/aliyun_deployment.md)

包含：
- SSL/TLS 配置
- Nginx 反向代理
- 安全加固
- 性能优化
- 监控告警
