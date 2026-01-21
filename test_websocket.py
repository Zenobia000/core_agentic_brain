#!/usr/bin/env python3
"""Test WebSocket connection and step event streaming"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        print(f"[{datetime.now()}] Connected to WebSocket")

        # Send init message
        init_msg = {
            "type": "init",
            "data": {}
        }
        await websocket.send(json.dumps(init_msg))
        print(f"[{datetime.now()}] Sent init message")

        # Send a chat message
        chat_msg = {
            "type": "chat",
            "data": {
                "message": "Hello, can you help me understand what tools you have available?"
            }
        }
        await websocket.send(json.dumps(chat_msg))
        print(f"[{datetime.now()}] Sent chat message")

        # Listen for responses
        print(f"[{datetime.now()}] Listening for events...")
        print("-" * 60)

        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)

                # Check if it's a step_event
                if data.get("type") == "step_event":
                    event = data.get("data", {})
                    print(f"[STEP EVENT] Phase: {event.get('phase')}, Step: {event.get('step_index')}")
                    if event.get('message'):
                        print(f"  Message: {event.get('message')[:100]}...")
                    if event.get('tool'):
                        print(f"  Tool: {event['tool'].get('name')} - Status: {event['tool'].get('status')}")
                else:
                    print(f"[{data.get('type', 'unknown').upper()}] {str(data)[:200]}...")

        except asyncio.TimeoutError:
            print(f"\n[{datetime.now()}] No more messages (timeout)")
        except Exception as e:
            print(f"\n[{datetime.now()}] Error: {e}")

if __name__ == "__main__":
    print("Testing WebSocket connection and step events...")
    print("=" * 60)
    asyncio.run(test_websocket())
    print("=" * 60)
    print("Test complete!")