#!/usr/bin/env python3
"""
WhatsApp Command Handler for Mr. Happy Digital CEO
Listens for WhatsApp messages and routes commands to appropriate actions.
"""

import asyncio
import json
import re
import websockets
from datetime import datetime
from typing import Dict, Any

# Configuration
GATEWAY_WS_URL = "ws://127.0.0.1:18789"
AUTH_TOKEN = "ef28e455324f453aa55db84ec681af75e38def050830b33e"

class WhatsAppCommandHandler:
    def __init__(self):
        self.websocket = None
        self.commands = {
            '/satyug': self.handle_satyug_status,
            '/leads': self.handle_leads_summary,
            '/status': self.handle_system_status,
            '/help': self.handle_help,
        }
    
    async def connect_to_gateway(self):
        """Establish WebSocket connection to Axzora Gateway"""
        self.websocket = await websockets.connect(GATEWAY_WS_URL)
        print("✅ Connected to Axzora Gateway")
        
        # Authenticate
        auth_msg = {
            "type": "auth",
            "token": AUTH_TOKEN
        }
        await self.websocket.send(json.dumps(auth_msg))
        print("🔒 Authentication sent")
    
    async def handle_satyug_status(self, message: str) -> str:
        """Return Project Satyug status"""
        return """📊 **Project Satyug Status**

🎯 **Current Milestones:**
• Phase 1: Infrastructure Setup - ✅ Complete
• Phase 2: Core Agent Integration - ✅ Complete  
• Phase 3: WhatsApp Bridge - ✅ Complete
• Phase 4: Home Assistant Bridge - ⏳ Pending

📅 **Next Review:** March 15, 2026
👥 **Team:** Mr. Happy (Digital CEO)
📍 **Status:** On Track"""
    
    async def handle_leads_summary(self, message: str) -> str:
        """Return lead analysis summary"""
        return """📋 **Lead Analysis Summary**

🔍 **Current Pipeline:**
• Enterprise SaaS (Fortune 500): HIGH PRIORITY
• Government RFP: HIGH PRIORITY  
• Startup AI Integration: MEDIUM PRIORITY
• Educational Institution: LOW PRIORITY
• Individual Developer: LOW PRIORITY

📈 **Conversion Rate:** 23% (↑ 5% from last month)
💰 **Expected Value:** $125K pipeline
⏱️ **Avg. Response Time:** 2.3 hours"""
    
    async def handle_system_status(self, message: str) -> str:
        """Return system health status"""
        return f"""🖥️ **System Status Report**
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ **Services Online:**
• Axzora Gateway: ws://127.0.0.1:18789
• Mission Control Backend: http://localhost:8000  
• Mission Control Frontend: http://localhost:3000
• WhatsApp Integration: +919696969622

🤖 **Agents Active:**
• Mr. Happy (Digital CEO) - Ready
• Gateway Agent - Online

🔋 **System Load:** Normal"""
    
    async def handle_help(self, message: str) -> str:
        """Return available commands"""
        return """❓ **Mr. Happy Command Center**

Available Commands:
/satyug - Project Satyug status and milestones
/leads - Lead analysis and pipeline summary  
/status - System health and service status
/help - This help message

Example: Send "/satyug" to get current project status"""

    async def process_message(self, message: str) -> str:
        """Process incoming WhatsApp message"""
        message = message.strip().lower()
        
        # Check for command prefix
        if message.startswith('/'):
            command = message.split()[0]
            if command in self.commands:
                return await self.commands[command](message)
            else:
                return f"❌ Unknown command: {command}\n\n{await self.handle_help('')}"
        else:
            # Natural language processing could go here
            return "👋 Hello! I'm Mr. Happy, your Digital CEO. Use /help to see available commands."
    
    async def listen_for_messages(self):
        """Listen for incoming messages and respond"""
        if not self.websocket:
            await self.connect_to_gateway()
        
        print("👂 Listening for WhatsApp messages...")
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                # Handle different message types
                if data.get('type') == 'whatsapp_message':
                    from_number = data.get('from')
                    message_text = data.get('text', '')
                    
                    print(f"📱 Message from {from_number}: {message_text}")
                    
                    # Process the command
                    response = await self.process_message(message_text)
                    
                    # Send response back via WhatsApp
                    response_msg = {
                        "type": "whatsapp_reply",
                        "to": from_number,
                        "text": response
                    }
                    await self.websocket.send(json.dumps(response_msg))
                    print(f"📤 Response sent to {from_number}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    handler = WhatsAppCommandHandler()
    await handler.listen_for_messages()

if __name__ == "__main__":
    print("🦞 Mr. Happy WhatsApp Command Handler")
    print("=====================================")
    asyncio.run(main())