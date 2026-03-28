#!/usr/bin/env python3
"""
GMSP WebSocket 中转服务器
部署在阿里云，连接训练端和 Blender 端
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class RelayServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.trainer_clients: Dict[str, WebSocketServerProtocol] = {}
        self.blender_clients: Dict[str, WebSocketServerProtocol] = {}
        self.stats = {
            "total_connections": 0,
            "messages_relayed": 0,
            "start_time": datetime.now()
        }

    async def register_client(self, websocket: WebSocketServerProtocol):
        """客户端注册"""
        try:
            identity_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            identity = json.loads(identity_msg)
            client_type = identity.get("type")
            client_id = identity.get("id", f"{client_type}_{id(websocket)}")

            if client_type == "trainer":
                self.trainer_clients[client_id] = websocket
                logger.info(f"✅ 训练客户端已连接: {client_id}")
            elif client_type == "blender":
                self.blender_clients[client_id] = websocket
                logger.info(f"✅ Blender 客户端已连接: {client_id}")
            else:
                await websocket.close(1008, "未知客户端类型")
                return None

            self.stats["total_connections"] += 1
            await websocket.send(json.dumps({
                "type": "registered",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
            return client_type, client_id
        except Exception as e:
            logger.error(f"❌ 注册失败: {e}")
            return None

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """处理客户端连接"""
        client_info = await self.register_client(websocket)
        if not client_info:
            return

        client_type, client_id = client_info
        try:
            async for message in websocket:
                if client_type == "trainer":
                    await self.broadcast_to_blender(message, client_id)
                elif client_type == "blender":
                    await self.broadcast_to_trainer(message, client_id)
                self.stats["messages_relayed"] += 1
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 客户端断开: {client_id}")
        finally:
            if client_type == "trainer":
                self.trainer_clients.pop(client_id, None)
            elif client_type == "blender":
                self.blender_clients.pop(client_id, None)

    async def broadcast_to_blender(self, message, sender_id: str):
        """转发到 Blender"""
        if not self.blender_clients:
            logger.warning("⚠️  没有 Blender 在线")
            return
        try:
            data = json.loads(message)
            data["_sender"] = sender_id
            message = json.dumps(data)
        except:
            pass
        for client_id, ws in list(self.blender_clients.items()):
            try:
                await ws.send(message)
            except Exception as e:
                logger.error(f"❌ 转发失败: {e}")
                self.blender_clients.pop(client_id, None)

    async def broadcast_to_trainer(self, message, sender_id: str):
        """转发到训练端"""
        if not self.trainer_clients:
            logger.warning("⚠️  没有训练端在线")
            return
        try:
            data = json.loads(message)
            data["_sender"] = sender_id
            message = json.dumps(data)
        except:
            pass
        for client_id, ws in list(self.trainer_clients.items()):
            try:
                await ws.send(message)
            except Exception as e:
                logger.error(f"❌ 转发失败: {e}")
                self.trainer_clients.pop(client_id, None)

    async def print_stats(self):
        """定期打印统计"""
        while True:
            await asyncio.sleep(60)
            uptime = datetime.now() - self.stats["start_time"]
            logger.info(
                f"📊 运行 {uptime} | 训练端: {len(self.trainer_clients)} | "
                f"Blender: {len(self.blender_clients)} | 转发: {self.stats['messages_relayed']}"
            )

    async def start(self):
        """启动服务器"""
        logger.info("🚀 GMSP 中转服务器启动")
        logger.info(f"📍 {self.host}:{self.port}")
        asyncio.create_task(self.print_stats())
        async with websockets.serve(
            self.handle_client, self.host, self.port,
            max_size=100 * 1024 * 1024, ping_interval=20, ping_timeout=10
        ):
            await asyncio.Future()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    
    server = RelayServer(host=args.host, port=args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("👋 服务器已停止")
