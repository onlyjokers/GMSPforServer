# GMSPforServer 部署指南

## 部署环境

- 操作系统：Ubuntu 20.04+ / CentOS 7+
- Python：3.8+
- 网络：公网 IP，开放端口 8080

---

## 方式一：快速部署（开发测试）

### 1. 上传代码

```bash
# 在本地打包
cd /home/GSMP
tar -czf GMSPforServer.tar.gz GMSPforServer/

# 上传到阿里云
scp GMSPforServer.tar.gz root@阿里云IP:/root/

# 在阿里云解压
ssh root@阿里云IP
cd /root
tar -xzf GMSPforServer.tar.gz
```

### 2. 安装依赖

```bash
cd GMSPforServer
pip3 install -r requirements.txt
```

### 3. 启动服务器

```bash
# 前台运行（测试）
python3 src/relay_server.py --host 0.0.0.0 --port 8080

# 后台运行
nohup python3 src/relay_server.py --host 0.0.0.0 --port 8080 > logs/relay.log 2>&1 &

# 查看日志
tail -f logs/relay.log
```

---

## 方式二：生产部署（systemd）

### 1. 安装代码

```bash
cd /root
git clone <your-repo> GMSPforServer
# 或上传代码包

cd GMSPforServer
pip3 install -r requirements.txt
```

### 2. 配置 systemd 服务

```bash
# 复制服务文件
sudo cp config/gmsp-relay.service /etc/systemd/system/

# 编辑服务文件（如果路径不同）
sudo nano /etc/systemd/system/gmsp-relay.service

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable gmsp-relay

# 启动服务
sudo systemctl start gmsp-relay

# 查看状态
sudo systemctl status gmsp-relay
```

### 3. 管理服务

```bash
# 停止
sudo systemctl stop gmsp-relay

# 重启
sudo systemctl restart gmsp-relay

# 查看日志
sudo journalctl -u gmsp-relay -f

# 或查看文件日志
tail -f /root/GMSPforServer/logs/relay.log
```

---

## 防火墙配置

### 阿里云安全组

1. 登录阿里云控制台
2. ECS 实例 → 安全组
3. 配置规则 → 添加安全组规则
4. 设置：
   - 规则方向：入方向
   - 授权策略：允许
   - 协议类型：TCP
   - 端口范围：8080/8080
   - 授权对象：0.0.0.0/0

### 服务器防火墙

**Ubuntu/Debian (ufw):**
```bash
sudo ufw allow 8080/tcp
sudo ufw status
```

**CentOS/RHEL (firewalld):**
```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

**iptables:**
```bash
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

---

## 测试部署

### 1. 测试连通性

```bash
# 在本地测试
python3 scripts/test_connection.py ws://阿里云IP:8080

# 或使用 telnet
telnet 阿里云IP 8080

# 或使用 nc
nc -zv 阿里云IP 8080
```

### 2. 完整功能测试

**终端 1（模拟 Blender）：**
```bash
python3 scripts/test_blender.py ws://阿里云IP:8080
```

**终端 2（模拟训练端）：**
```bash
python3 scripts/test_trainer.py ws://阿里云IP:8080
```

应该看到消息成功转发。

---

## 监控和维护

### 查看运行状态

```bash
# systemd 状态
sudo systemctl status gmsp-relay

# 进程状态
ps aux | grep relay_server

# 端口监听
netstat -tlnp | grep 8080
# 或
ss -tlnp | grep 8080
```

### 查看日志

```bash
# 实时日志
tail -f logs/relay.log

# systemd 日志
sudo journalctl -u gmsp-relay -f

# 最近 100 行
sudo journalctl -u gmsp-relay -n 100
```

### 性能监控

服务器每分钟自动打印统计信息：
- 运行时间
- 连接数
- 转发消息数

---

## 故障排查

### 问题 1：连接超时

**检查：**
```bash
# 1. 服务是否运行
ps aux | grep relay_server

# 2. 端口是否监听
netstat -tlnp | grep 8080

# 3. 防火墙是否开放
sudo iptables -L -n | grep 8080

# 4. 阿里云安全组是否配置
```

### 问题 2：服务启动失败

**检查：**
```bash
# 查看详细错误
sudo journalctl -u gmsp-relay -xe

# 检查 Python 版本
python3 --version

# 检查依赖
pip3 list | grep websockets
```

### 问题 3：消息丢失

**检查：**
```bash
# 查看日志中的警告
grep "没有.*在线" logs/relay.log

# 确认双方都已连接
# 日志中应该有 "✅ 客户端已连接"
```

---

## 升级部署

```bash
# 停止服务
sudo systemctl stop gmsp-relay

# 备份旧版本
cp -r GMSPforServer GMSPforServer.backup

# 更新代码
cd GMSPforServer
git pull
# 或上传新代码

# 更新依赖
pip3 install -r requirements.txt

# 重启服务
sudo systemctl start gmsp-relay

# 检查状态
sudo systemctl status gmsp-relay
```

---

## 安全建议

1. **限制访问 IP**（可选）
   ```bash
   # 只允许特定 IP 访问
   # 在阿里云安全组中设置授权对象为你的 IP
   ```

2. **使用 TLS 加密**（推荐）
   - 申请 SSL 证书（Let's Encrypt 免费）
   - 使用 Nginx 反向代理
   - 客户端使用 `wss://` 连接

3. **添加认证**（可选）
   - 在注册时验证 token
   - 防止未授权访问

---

## 性能优化

### 增加并发连接数

编辑 `/etc/security/limits.conf`：
```
* soft nofile 65536
* hard nofile 65536
```

### 调整系统参数

编辑 `/etc/sysctl.conf`：
```
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
```

应用：
```bash
sudo sysctl -p
```

---

## 备份和恢复

### 备份

```bash
# 备份配置和日志
tar -czf gmsp-backup-$(date +%Y%m%d).tar.gz \
    GMSPforServer/config/ \
    GMSPforServer/logs/
```

### 恢复

```bash
# 解压备份
tar -xzf gmsp-backup-20260328.tar.gz

# 恢复配置
cp -r GMSPforServer/config/* /root/GMSPforServer/config/
```

---

## 卸载

```bash
# 停止并禁用服务
sudo systemctl stop gmsp-relay
sudo systemctl disable gmsp-relay

# 删除服务文件
sudo rm /etc/systemd/system/gmsp-relay.service
sudo systemctl daemon-reload

# 删除代码
rm -rf /root/GMSPforServer

# 关闭防火墙端口
sudo ufw delete allow 8080/tcp
```
