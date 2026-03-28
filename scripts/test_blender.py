#!/usr/bin/env python3
"""模拟 Blender 客户端 — 返回与真实插件一致的字段映射格式"""
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

            # 从请求中提取材质名称，构造与真实插件一致的字段映射格式
            material_group = request.get("material_group", request.get("outputs", []))
            names = [m.get("name", f"M{i+1}") for i, m in enumerate(material_group)]

            # 字段映射格式：每个字段是 {材质名: 值} 的 dict
            response = {
                "session_id": request.get("session_id"),
                "taskid": request.get("head", {}).get("taskid"),
                "accuracy_rank": {name: rank for rank, name in enumerate(names, 1)},
                "meaning_rank": {name: rank for rank, name in enumerate(names, 1)},
                "status": {name: True for name in names},
                "error_msg": {name: "" for name in names},
                "id": {name: i + 1 for i, name in enumerate(names)},
                "name": {name: name for name in names},
            }
            await ws.send(json.dumps(response))
            print(f"[Blender] ✅ 已发送响应 ({len(names)} 个材质)")

        except asyncio.TimeoutError:
            print("[Blender] ⚠️  超时（可能没有训练端发送请求）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_blender.py ws://IP:8080")
        sys.exit(1)

    asyncio.run(test_blender(sys.argv[1]))
