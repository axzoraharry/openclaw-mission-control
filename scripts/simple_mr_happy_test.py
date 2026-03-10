#!/usr/bin/env python3
"""
Simple Mr. Happy Test - Direct Gateway Communication
"""

import asyncio
import websockets
import json

async def test_mr_happy():
    uri = "ws://127.0.0.1:18789"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to Axzora Gateway")
        
        # Wait for initial challenge
        challenge = await websocket.recv()
        print(f"📥 Challenge received: {challenge}")
        
        # Send a simple chat message
        message = {
            "type": "chat.message",
            "content": {
                "text": "Hello Mr. Happy! This is Harish. Please provide a status update on Axzora operations."
            }
        }
        
        print("📤 Sending message to Mr. Happy...")
        await websocket.send(json.dumps(message))
        
        # Wait for responses
        for i in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                print(f"📥 Response {i+1}: {response}")
            except asyncio.TimeoutError:
                print("⏰ No more responses")
                break

if __name__ == "__main__":
    print("🦞 Testing Mr. Happy Communication")
    print("=================================")
    asyncio.run(test_mr_happy())