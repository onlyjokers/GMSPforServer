#!/usr/bin/env python3
"""测试中转服务器连通性"""
import asyncio
import sys
import websockets


async def test_connection(server_url: str):
    print(f"🔍 测试连接: {server_url}")
    try:
        async with websockets.connect(server_url, open_timeout=5) as ws:
            print("✅ 连接成功")
            await ws.close()
            return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_connection.py ws://IP:8080")
        sys.exit(1)

    success = asyncio.run(test_connection(sys.argv[1]))
    sys.exit(0 if success else 1)
