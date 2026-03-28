#!/usr/bin/env python3
"""模拟训练端客户端"""
import asyncio
import json
import sys
import websockets


async def test_trainer(server_url: str):
    print(f"[训练端] 连接到: {server_url}")

    async with websockets.connect(server_url) as ws:
        # 注册
        await ws.send(json.dumps({"type": "trainer", "id": "test_trainer"}))
        response = await ws.recv()
        print(f"[训练端] 注册响应: {json.loads(response)}")

        # 发送测试请求
        request = {
            "material_group": [{"id": 1, "name": "test", "code": "print('test')"}],
            "session_id": "test_001",
            "head": {"input": "测试", "taskid": "001"}
        }
        print("[训练端] 发送请求...")
        await ws.send(json.dumps(request))

        # 等待响应
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=30)
            print(f"[训练端] ✅ 收到响应: {json.loads(response)}")
        except asyncio.TimeoutError:
            print("[训练端] ⚠️  超时（可能没有 Blender 在线）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_trainer.py ws://IP:8080")
        sys.exit(1)

    asyncio.run(test_trainer(sys.argv[1]))
