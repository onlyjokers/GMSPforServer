#!/usr/bin/env python3
"""模拟 Blender 客户端"""
import asyncio
import json
import sys
import websockets


async def test_blender(server_url: str):
    print(f"[Blender] 连接到: {server_url}")

    async with websockets.connect(server_url) as ws:
        # 注册
        await ws.send(json.dumps({"type": "blender", "id": "test_blender"}))
        response = await ws.recv()
        print(f"[Blender] 注册响应: {json.loads(response)}")

        print("[Blender] 等待请求...")

        # 监听请求
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=60)
            request = json.loads(message)
            print(f"[Blender] ✅ 收到请求: {request.get('session_id')}")

            # 返回模拟结果
            response = {
                "material_results": [{
                    "id": 1,
                    "name": "test",
                    "status": True,
                    "accuracy_rank": 5,
                    "meaning_rank": 4
                }],
                "session_id": request.get("session_id"),
                "taskid": request.get("head", {}).get("taskid")
            }
            await ws.send(json.dumps(response))
            print("[Blender] ✅ 已发送响应")

        except asyncio.TimeoutError:
            print("[Blender] ⚠️  超时（可能没有训练端发送请求）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_blender.py ws://IP:8080")
        sys.exit(1)

    asyncio.run(test_blender(sys.argv[1]))
