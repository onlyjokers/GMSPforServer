# GMSPforServer 阿里云部署指南

本指南详细说明如何在阿里云 ECS 上部署 GMSP WebSocket 中转服务器。

## 目录

1. [购买和配置阿里云 ECS](#1-购买和配置阿里云-ecs)
2. [连接到服务器](#2-连接到服务器)
3. [安装依赖](#3-安装依赖)
4. [部署服务器代码](#4-部署服务器代码)
5. [配置防火墙](#5-配置防火墙)
6. [使用 systemd 管理服务](#6-使用-systemd-管理服务)
7. [使用 screen 运行（简单方案）](#7-使用-screen-运行简单方案)
8. [监控和日志](#8-监控和日志)
9. [故障排查](#9-故障排查)

---

## 1. 购买和配置阿里云 ECS

### 1.1 选择实例规格

**推荐配置：**
- **实例类型**: 计算型 c7 或通用型 g7（按需选择）
- **CPU/内存**: 2核4GB（最低）或 4核8GB（推荐）
- **操作系统**: Ubuntu 22.04 LTS 或 Ubuntu 20.04 LTS
- **带宽**: 按流量计费，峰值带宽 5Mbps 起
- **地域**: 选择离你最近的地域（如华东、华北）

### 1.2 购买步骤

1. 登录阿里云控制台
2. 进入 **云服务器 ECS** → **实例与镜像** → **实例**
3. 点击 **创建实例**
4. 选择配置：
   - 付费模式：按量付费（测试）或包年包月（生产）
   - 地域：选择合适的地域
   - 实例规格：2核4GB 或更高
   - 镜像：Ubuntu 22.04 64位
   - 存储：系统盘 40GB（默认即可）
   - 网络：默认 VPC
   - 公网 IP：分配公网 IPv4 地址
   - 安全组：创建新安全组或使用现有
5. 设置实例密码（记住这个密码）
6. 确认订单并创建

### 1.3 记录重要信息

创建完成后，记录以下信息：
- **公网 IP**: 例如 `121.196.205.73`
- **用户名**: 默认为 `root`（Ubuntu）
- **密码**: 你设置的实例密码

---

## 2. 连接到服务器

### 2.1 使用 SSH 连接（推荐）

**Windows 用户：**
```bash
# 使用 PowerShell 或 Windows Terminal
ssh root@你的公网IP
```

**Mac/Linux 用户：**
```bash
ssh root@你的公网IP
```

首次连接会提示确认指纹，输入 `yes` 并回车，然后输入密码。

### 2.2 使用阿里云控制台连接

如果 SSH 连接失败，可以使用阿里云控制台的 VNC 连接：
1. 进入 ECS 控制台
2. 找到你的实例
3. 点击 **远程连接** → **VNC 连接**

---

## 3. 安装依赖

连接到服务器后，执行以下命令：

### 3.1 更新系统
```bash
apt update && apt upgrade -y
```

### 3.2 安装 Python 3.10+
```bash
# Ubuntu 22.04 默认已安装 Python 3.10
python3 --version

# 如果版本低于 3.10，安装最新版本
apt install python3.10 python3.10-venv python3-pip -y
```

### 3.3 安装 Git
```bash
apt install git -y
```

### 3.4 安装其他工具（可选）
```bash
# screen - 用于后台运行
apt install screen -y

# htop - 系统监控
apt install htop -y
```

---

## 4. 部署服务器代码

### 4.1 克隆代码仓库

```bash
# 创建工作目录
mkdir -p /opt/gmsp
cd /opt/gmsp

# 克隆 GMSPforServer 仓库
git clone https://github.com/onlyjokers/GMSPforServer.git
cd GMSPforServer
```

### 4.2 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4.3 安装 Python 依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.4 测试运行
```bash
# 测试服务器是否能正常启动
python3 src/relay_server.py --host 0.0.0.0 --port 8080
```

看到以下输出表示成功：
```
🚀 GMSP 中转服务器启动
📍 0.0.0.0:8080
```

按 `Ctrl+C` 停止测试。

---

## 5. 配置防火墙

### 5.1 配置阿里云安全组

1. 进入 ECS 控制台
2. 点击实例 ID 进入详情页
3. 点击 **安全组** 标签
4. 点击安全组 ID 进入安全组规则
5. 点击 **手动添加** 或 **快速添加**

**添加入方向规则：**
- 协议类型：自定义 TCP
- 端口范围：8080/8080
- 授权对象：0.0.0.0/0（允许所有 IP）
- 描述：GMSP WebSocket 服务

### 5.2 配置服务器防火墙（可选）

Ubuntu 默认使用 ufw：
```bash
# 允许 8080 端口
ufw allow 8080/tcp

# 允许 SSH（重要！）
ufw allow 22/tcp

# 启用防火墙
ufw enable

# 查看状态
ufw status
```

---

## 6. 使用 systemd 管理服务（推荐）

### 6.1 创建 systemd 服务文件

```bash
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
```

### 6.2 启动服务

```bash
# 重新加载 systemd 配置
systemctl daemon-reload

# 启动服务
systemctl start gmsp-relay

# 设置开机自启
systemctl enable gmsp-relay

# 查看服务状态
systemctl status gmsp-relay
```

### 6.3 管理服务

```bash
# 停止服务
systemctl stop gmsp-relay

# 重启服务
systemctl restart gmsp-relay

# 查看日志
journalctl -u gmsp-relay -f

# 查看最近 100 行日志
journalctl -u gmsp-relay -n 100
```

---

## 7. 使用 screen 运行（简单方案）

如果不想配置 systemd，可以使用 screen 在后台运行：

### 7.1 启动 screen 会话

```bash
cd /opt/gmsp/GMSPforServer
source venv/bin/activate

# 创建名为 gmsp 的 screen 会话
screen -S gmsp

# 在 screen 中运行服务器
python3 src/relay_server.py --host 0.0.0.0 --port 8080
```

### 7.2 分离和重新连接

- **分离会话**: 按 `Ctrl+A` 然后按 `D`
- **重新连接**: `screen -r gmsp`
- **查看所有会话**: `screen -ls`
- **终止会话**: 在 screen 中按 `Ctrl+C` 然后输入 `exit`

---

## 8. 监控和日志

### 8.1 查看实时日志

**使用 systemd：**
```bash
journalctl -u gmsp-relay -f
```

**使用 screen：**
```bash
screen -r gmsp
```

### 8.2 监控系统资源

```bash
# 查看 CPU、内存使用
htop

# 查看网络连接
netstat -tulnp | grep 8080

# 查看进程
ps aux | grep relay_server
```

### 8.3 日志文件位置

如果配置了日志文件（可选）：
```bash
# 创建日志目录
mkdir -p /var/log/gmsp

# 修改服务器代码，添加文件日志
# 或使用 systemd 的 journal
```

---

## 9. 故障排查

### 9.1 服务无法启动

**检查端口占用：**
```bash
netstat -tulnp | grep 8080
# 或
lsof -i :8080
```

**检查 Python 环境：**
```bash
source /opt/gmsp/GMSPforServer/venv/bin/activate
python3 -c "import websockets; print('OK')"
```

**查看详细错误：**
```bash
journalctl -u gmsp-relay -n 50 --no-pager
```

### 9.2 客户端无法连接

**检查防火墙：**
```bash
# 阿里云安全组是否开放 8080 端口
# 服务器防火墙是否允许
ufw status
```

**测试端口连通性（从本地）：**
```bash
# 使用 telnet
telnet 你的公网IP 8080

# 使用 nc
nc -zv 你的公网IP 8080

# 使用 Python 测试 WebSocket
python3 -c "
import asyncio
import websockets

async def test():
    uri = 'ws://你的公网IP:8080'
    async with websockets.connect(uri) as ws:
        print('连接成功')

asyncio.run(test())
"
```

### 9.3 服务运行但无响应

**检查服务状态：**
```bash
systemctl status gmsp-relay
```

**查看连接数：**
```bash
netstat -an | grep 8080 | grep ESTABLISHED | wc -l
```

**重启服务：**
```bash
systemctl restart gmsp-relay
```

### 9.4 内存或 CPU 占用过高

**查看资源使用：**
```bash
htop
# 或
top
```

**增加实例规格：**
如果资源不足，考虑升级 ECS 实例配置。

---

## 10. 测试连接

### 10.1 从本地测试

在本地机器上运行（需要安装 websockets）：

```bash
cd /home/GSMP/GMSPforServer
python3 scripts/test_connection.py ws://你的公网IP:8080
```

### 10.2 更新客户端配置

**GMSP 训练端（configs/default.json）：**
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

**GMSPforBlender（Blender 插件 UI）：**
- 打开 Blender
- 进入 GMSP 面板
- 服务器地址填写：`ws://你的公网IP:8080`
- 点击启动服务

---

## 11. 安全建议

### 11.1 使用 SSL/TLS（推荐生产环境）

安装 Nginx 作为反向代理，配置 HTTPS：

```bash
apt install nginx certbot python3-certbot-nginx -y

# 配置域名（需要先将域名解析到服务器 IP）
certbot --nginx -d your-domain.com
```

Nginx 配置示例：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 11.2 限制访问 IP（可选）

如果只有固定 IP 访问，修改安全组规则，只允许特定 IP。

### 11.3 定期更新

```bash
# 定期更新系统
apt update && apt upgrade -y

# 更新代码
cd /opt/gmsp/GMSPforServer
git pull
systemctl restart gmsp-relay
```

---

## 12. 快速部署脚本

将以下内容保存为 `deploy.sh`，一键部署：

```bash
#!/bin/bash
set -e

echo "🚀 开始部署 GMSP 中转服务器..."

# 更新系统
apt update && apt upgrade -y

# 安装依赖
apt install -y python3 python3-venv python3-pip git screen

# 创建目录
mkdir -p /opt/gmsp
cd /opt/gmsp

# 克隆代码
if [ ! -d "GMSPforServer" ]; then
    git clone https://github.com/onlyjokers/GMSPforServer.git
fi
cd GMSPforServer

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 创建 systemd 服务
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
systemctl daemon-reload
systemctl enable gmsp-relay
systemctl start gmsp-relay

echo "✅ 部署完成！"
echo "📍 服务器运行在 0.0.0.0:8080"
echo "🔍 查看状态: systemctl status gmsp-relay"
echo "📋 查看日志: journalctl -u gmsp-relay -f"
echo ""
echo "⚠️  别忘了在阿里云安全组开放 8080 端口！"
```

使用方法：
```bash
# 上传到服务器
scp deploy.sh root@你的公网IP:/root/

# SSH 连接到服务器
ssh root@你的公网IP

# 执行部署
chmod +x deploy.sh
./deploy.sh
```

---

## 常见问题

**Q: 服务器重启后服务会自动启动吗？**
A: 如果使用 systemd 并执行了 `systemctl enable gmsp-relay`，会自动启动。

**Q: 如何更改端口？**
A: 修改 systemd 服务文件中的 `--port 8080`，然后 `systemctl daemon-reload && systemctl restart gmsp-relay`。

**Q: 支持多少并发连接？**
A: 取决于服务器配置，2核4GB 可支持数百个连接，4核8GB 可支持数千个。

**Q: 流量费用如何计算？**
A: 按实际使用流量计费，WebSocket 消息较小，一般每月几 GB 到几十 GB。

**Q: 需要备案吗？**
A: 如果使用域名访问需要备案，直接使用 IP 不需要。

---

## 联系支持

如有问题，请查看：
- GitHub Issues: https://github.com/onlyjokers/GMSPforServer/issues
- 阿里云文档: https://help.aliyun.com/
