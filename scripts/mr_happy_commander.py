#!/usr/bin/env python3
"""
Mr. Happy Command Interface
Sends commands directly to the Axzora Gateway agent
"""

import asyncio
import websockets
import json
import uuid
from datetime import datetime

class MrHappyCommander:
    def __init__(self):
        self.websocket = None
        self.session_id = str(uuid.uuid4())
        
    async def connect(self):
        """Connect to Axzora Gateway"""
        uri = "ws://127.0.0.1:18789"
        self.websocket = await websockets.connect(uri)
        print("✅ Connected to Axzora Gateway")
        return True
    
    async def send_command(self, command: str) -> str:
        """Send a command to Mr. Happy and get response"""
        if not self.websocket:
            await self.connect()
            
        # Create message for the agent
        message = {
            "type": "chat",
            "text": command,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📤 Sending command: {command}")
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            response_data = json.loads(response)
            
            # Extract the actual response text
            if response_data.get('type') == 'chat':
                return response_data.get('text', 'No response text found')
            elif response_data.get('type') == 'agent_response':
                return response_data.get('content', str(response_data))
            else:
                return f"Response: {response}"
                
        except asyncio.TimeoutError:
            return "⏰ Command timed out after 30 seconds"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()

async def main():
    commander = MrHappyCommander()
    
    print("🦞 Mr. Happy Command Interface")
    print("==============================")
    print("Connected to your Digital CEO system")
    print("Type 'quit' to exit\n")
    
    try:
        while True:
            command = input("🤖 Mr. Happy >> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
                
            if not command:
                continue
                
            response = await commander.send_command(command)
            print(f"🦞 Mr. Happy: {response}\n")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        await commander.close()

if __name__ == "__main__":
    asyncio.run(main())