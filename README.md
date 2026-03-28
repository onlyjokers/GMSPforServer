# GMSPforServer

GMSP WebSocket 中转服务器 - 部署在阿里云，连接训练端和 Blender 端

## 项目定位

这是 GMSP 生态系统的三个组件之一：

- **GMSP** - 训练端（云端服务器）
- **GMSPforBlender** - Blender 插件（本地计算机）
- **GMSPforServer** - 中转服务器（阿里云）← 本项目

## 功能

- WebSocket 消息中转
- 支持多个训练端和 Blender 实例
- 自动心跳保活
- 大文件传输（最大 100MB）
- 连接统计和监控

## 快速部署

### 1. 安装依赖

```bash
pip3 install websockets
```

### 2. 启动服务器

```bash
python3 src/relay_server.py --host 0.0.0.0 --port 8080
```

### 3. 后台运行

```bash
nohup python3 src/relay_server.py --host 0.0.0.0 --port 8080 > logs/relay.log 2>&1 &
```

### 4. 使用 systemd（推荐）

```bash
# 复制服务文件
sudo cp config/gmsp-relay.service /etc/systemd/system/

# 修改路径
sudo nano /etc/systemd/system/gmsp-relay.service

# 启动服务
sudo systemctl enable gmsp-relay
sudo systemctl start gmsp-relay

# 查看状态
sudo systemctl status gmsp-relay
```

## 配置

### 防火墙

**阿里云控制台：**
- 安全组 → 添加规则
- 端口：8080
- 协议：TCP
- 授权对象：0.0.0.0/0

**服务器防火墙：**
```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

## 测试

```bash
# 测试连通性
python3 scripts/test_connection.py ws://你的IP:8080

# 模拟训练端
python3 scripts/test_trainer.py ws://你的IP:8080

# 模拟 Blender 端
python3 scripts/test_blender.py ws://你的IP:8080
```

## 监控

### 查看日志

```bash
# 实时日志
tail -f logs/relay.log

# systemd 日志
sudo journalctl -u gmsp-relay -f
```

### 统计信息

服务器每分钟自动打印统计：
- 运行时间
- 连接的训练端数量
- 连接的 Blender 数量
- 转发的消息总数

## 性能

- 单条消息最大：100MB
- 心跳间隔：20秒
- 并发连接：100+
- 延迟：~50ms（取决于网络）

## 目录结构

```
GMSPforServer/
├── src/
│   └── relay_server.py      # 主服务器代码
├── config/
│   ├── gmsp-relay.service   # systemd 服务文件
│   └── config.json          # 配置文件（可选）
├── scripts/
│   ├── test_connection.py   # 连接测试
│   ├── test_trainer.py      # 训练端测试
│   └── test_blender.py      # Blender 端测试
├── docs/
│   ├── deployment.md        # 部署文档
│   └── api.md               # API 文档
├── logs/                    # 日志目录
├── README.md
└── requirements.txt
```

## 客户端连接

### 训练端（GMSP）

**方式一：通过工厂函数自动选择（推荐）**

在 `configs/local.json` 中配置 `relay_server`：

```json
{
  "profiles": {
    "blenderllm_qwen3_5_4b": {
      "transport": {
        "relay_server": "ws://阿里云IP:8080"
      }
    }
  }
}
```

代码中使用：

```python
from gmsp.clients import create_transport_client
from gmsp.config import load_gmsp_config, get_default_profile_name, get_profile

config = load_gmsp_config()
profile = get_profile(config, get_default_profile_name(config))
client = create_transport_client(profile["transport"])
client.connect()
results = client.send_materials(materials_json)
client.close()
```

**方式二：直接使用 WebSocket 客户端**

```python
from gmsp.clients.websocket_client import WebSocketClientSender

client = WebSocketClientSender(relay_server="ws://阿里云IP:8080")
client.connect()
results = client.send_materials(materials_json)
client.close()
```

### Blender 端

1. 在 Blender 插件 GMSP 面板中，将通信模式切换为 "WebSocket"
2. 填入中转服务器地址：`ws://阿里云IP:8080`
3. 点击 "启动服务"

## 故障排查

### 连接失败

```bash
# 测试端口
telnet 阿里云IP 8080
nc -zv 阿里云IP 8080

# 检查进程
ps aux | grep relay_server

# 检查防火墙
sudo iptables -L -n | grep 8080
```

### 重启服务

```bash
# systemd
sudo systemctl restart gmsp-relay

# 手动
pkill -f relay_server
nohup python3 src/relay_server.py > logs/relay.log 2>&1 &
```

## 成本

**阿里云 ECS 最低配置：**
- 1核2G，5Mbps 带宽
- 约 ¥50-100/月

## 许可证

MIT License

## 相关项目

- [GMSP](../GMSP) - 训练端
- [GMSPforBlender](../GMSPforBlender) - Blender 插件
