#!/usr/bin/env python3
"""WhatsApp Bridge Service for Axzora Mission Control."""

import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class WhatsAppMessage(BaseModel):
    """WhatsApp message structure."""
    from_number: str
    to_number: str
    body: str
    message_id: Optional[str] = None
    timestamp: Optional[str] = None


class WhatsAppBridge:
    """WhatsApp Bridge service."""
    
    def __init__(self, port: int = 8005):
        self.port = port
        self.app = FastAPI(
            title="WhatsApp Bridge",
            description="Bridge between WhatsApp and Axzora Mission Control",
            version="0.1.0"
        )
        self.verify_token = "axzora_whatsapp_verify_token_2026"
        self.messages = []
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "WhatsApp Bridge",
                "version": "0.1.0",
                "status": "online"
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "whatsapp-bridge",
                "messages_received": len(self.messages),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/webhook")
        async def verify_webhook(
            hub_mode: str = None,
            hub_verify_token: str = None,
            hub_challenge: str = None
        ):
            """Verify webhook for WhatsApp API."""
            if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
                return int(hub_challenge) if hub_challenge else "OK"
            raise HTTPException(status_code=403, detail="Verification failed")
        
        @self.app.post("/webhook")
        async def receive_message(request: Request):
            """Receive WhatsApp webhook messages."""
            try:
                data = await request.json()
                
                # Process message
                message = self._process_whatsapp_data(data)
                if message:
                    self.messages.append(message)
                    
                    # Forward to Mission Control
                    await self._forward_to_mission_control(message)
                    
                    return {"status": "received", "message_id": message.message_id}
                
                return {"status": "ignored"}
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/send")
        async def send_message(message: dict):
            """Send a WhatsApp message."""
            # This would integrate with WhatsApp Business API
            return {
                "status": "sent",
                "to": message.get("to"),
                "body": message.get("body"),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/messages")
        async def list_messages(limit: int = 10):
            """List recent messages."""
            return {
                "messages": self.messages[-limit:],
                "total": len(self.messages)
            }
    
    def _process_whatsapp_data(self, data: dict) -> Optional[WhatsAppMessage]:
        """Process WhatsApp webhook data."""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if messages:
                msg = messages[0]
                return WhatsAppMessage(
                    from_number=msg.get("from"),
                    to_number=value.get("metadata", {}).get("phone_number_id"),
                    body=msg.get("text", {}).get("body", ""),
                    message_id=msg.get("id"),
                    timestamp=msg.get("timestamp")
                )
            
            return None
        except Exception:
            return None
    
    async def _forward_to_mission_control(self, message: WhatsAppMessage):
        """Forward message to Mission Control."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8000/api/v1/webhooks/whatsapp",
                    json={
                        "from": message.from_number,
                        "body": message.body,
                        "timestamp": message.timestamp
                    },
                    timeout=5.0
                )
        except Exception as e:
            print(f"Failed to forward to Mission Control: {e}")
    
    def run(self):
        """Run the WhatsApp bridge service."""
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")


def main():
    """Main entry point."""
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8005
    bridge = WhatsAppBridge(port=port)
    bridge.run()


if __name__ == "__main__":
    main()
