# GMSP 项目重组完成

## 新的项目结构

```
/home/GSMP/
├── GMSP/              # 训练端（云端服务器）
├── GMSPforBlender/    # Blender 插件（本地计算机）
├── GMSPforServer/     # 中转服务器（阿里云）⭐ 新增
└── ARCHITECTURE.md    # 架构总览文档
```

---

## GMSPforServer 项目

### 已创建的文件

```
GMSPforServer/
├── src/
│   └── relay_server.py          # WebSocket 中转服务器（150行）
├── config/
│   └── gmsp-relay.service       # systemd 服务配置
├── scripts/
│   ├── test_connection.py       # 连接测试
│   ├── test_trainer.py          # 训练端测试
│   └── test_blender.py          # Blender 端测试
├── docs/
│   └── deployment.md            # 详细部署文档
├── logs/                        # 日志目录
├── README.md                    # 项目说明
└── requirements.txt             # 依赖（websockets）
```

### 核心功能

1. **WebSocket 服务器**
   - 监听 0.0.0.0:8080
   - 支持训练端和 Blender 端连接
   - 自动消息转发
   - 心跳保活（20秒）
   - 大文件支持（100MB）

2. **客户端管理**
   - 自动注册识别
   - 连接状态跟踪
   - 死连接清理

3. **统计监控**
   - 每分钟打印统计
   - 连接数、消息数
   - 运行时间

---

## 快速部署

### 1. 阿里云部署（2分钟）

```bash
# 上传代码到阿里云
scp -r /home/GSMP/GMSPforServer root@阿里云IP:/root/

# SSH 登录
ssh root@阿里云IP

# 安装依赖
cd /root/GMSPforServer
pip3 install -r requirements.txt

# 启动服务器
python3 src/relay_server.py --host 0.0.0.0 --port 8080
```

### 2. 开放防火墙（1分钟）

**阿里云控制台：**
- 安全组 → TCP 8080 → 0.0.0.0/0

### 3. 测试连接（1分钟）

```bash
# 在本地测试
cd /home/GSMP/GMSPforServer
python3 scripts/test_connection.py ws://阿里云IP:8080
```

---

## 使用方式

### GMSP 训练端

编辑 `configs/local.json`：
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

使用 WebSocket 客户端：
```python
from gmsp.clients.websocket_client import GMSPWebSocketClient

client = GMSPWebSocketClient("ws://阿里云IP:8080")
await client.connect()
result = await client.send_material_request(...)
```

### Blender 端

在插件中填入：`ws://阿里云IP:8080`

---

## 优势总结

### ✅ 配置极简
- 只需要一个地址：`ws://阿里云IP:8080`
- 双方都连接这个地址
- 无需端口映射
- 无需 NAT 穿透

### ✅ 功能完整
- 双向通信
- 大文件支持（100MB）
- 自动重连
- 心跳保活
- 多客户端支持

### ✅ 部署简单
- 单个 Python 文件
- 一条命令启动
- systemd 服务支持
- 完整测试脚本

### ✅ 监控方便
- 实时日志
- 统计信息
- 连接状态
- 错误追踪

---

## 成本

**阿里云 ECS 最低配置：**
- 1核2G，5Mbps 带宽
- 约 ¥50-100/月
- 支持 10+ 并发连接

---

## 下一步

1. **部署到阿里云**
   ```bash
   cd /home/GSMP/GMSPforServer
   # 按照 docs/deployment.md 部署
   ```

2. **测试完整流程**
   ```bash
   # 终端 1：模拟 Blender
   python3 scripts/test_blender.py ws://阿里云IP:8080

   # 终端 2：模拟训练端
   python3 scripts/test_trainer.py ws://阿里云IP:8080
   ```

3. **集成到训练流程**
   - 修改 GMSP 使用 WebSocket 客户端
   - 修改 Blender 插件使用 WebSocket 客户端
   - 运行完整训练循环

---

## 文档索引

- **架构总览：** `/home/GSMP/ARCHITECTURE.md`
- **服务器 README：** `/home/GSMP/GMSPforServer/README.md`
- **部署指南：** `/home/GSMP/GMSPforServer/docs/deployment.md`
- **快速开始：** `/home/GSMP/GMSP/docs/aliyun_relay_quickstart.md`

---

## 项目职责划分

| 项目 | 职责 | 部署位置 |
|------|------|----------|
| GMSP | 模型训练、代码生成 | 云端服务器 |
| GMSPforBlender | 代码执行、渲染评分 | 本地计算机 |
| GMSPforServer | 消息中转、连接管理 | 阿里云 ECS |

---

## 总结

现在你有了一个清晰的三层架构：

1. **训练层（GMSP）** - 专注于模型训练
2. **执行层（GMSPforBlender）** - 专注于材质渲染
3. **通信层（GMSPforServer）** - 专注于消息转发

每个项目职责单一，独立部署，易于维护和扩展。

**启动顺序：**
1. 先启动 GMSPforServer（阿里云）
2. 再启动 GMSPforBlender（本地）
3. 最后启动 GMSP 训练（云端）

所有组件都连接到同一个地址：`ws://阿里云IP:8080`
