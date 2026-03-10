#!/usr/bin/env python3
"""
Simple Axzora Gateway Test Script
Tests direct communication with the gateway
"""

import asyncio
import websockets
import json

async def test_gateway_connection():
    uri = "ws://127.0.0.1:18789"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Axzora Gateway")
            
            # Test message
            test_message = {
                "type": "chat",
                "text": "Hello Mr. Happy, this is a test message from your Digital CEO system."
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📥 Response received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 10 seconds")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🦞 Testing Axzora Gateway Connection")
    print("====================================")
    asyncio.run(test_gateway_connection())