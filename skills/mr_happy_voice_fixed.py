#!/usr/bin/env python3
"""
Mr. Happy Voice Integration- Fixed Version
For use on Samsung Z Fold7 / Termux / Ubuntu Proot
Integrates with Ollama (llama3.2:3b) and Axzora Mesh Node
"""

import asyncio
import json
import os
import sys
import websocket
from datetime import datetime
from typing import Optional
import requests

# ============ GLOBAL CONFIGURATION ============
# IMPORTANT: Global variables must be declared at module levelMODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434"
MESH_NODE_URL = "http://localhost:8888"
MISSION_CONTROL_URL = "http://localhost:8000"
WEBSOCKET_PORT = 8765

# Axzora Agent Configuration
AGENTS = {
    "mr_happy": {"port": 8001, "role": "Primary AI CEO"},
    "lucy": {"port": 8002, "role": "Research Agent"},
    "tansi": {"port": 8003, "role": "Operations & Happy Paisa"},
    "kyra": {"port": 8004, "role": "Analytics & Vision"},
}

# Happy Paisa Configuration
HAPPY_PAISA_RATE = 1000# 1 HP =₹1000 INR

# ============ CORE CLASSES ============

class MrHappyVoice:
    """Voice interface for Mr. Happy AI"""
    
    def __init__(self):
        self.model = MODEL
        self.ollama_url = OLLAMA_URL
        self.mesh_url = MESH_NODE_URL
        self.conversation_history = []
        
    def check_ollama_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def query_ollama(self, prompt: str, stream: bool = False) -> str:
        """Send query to Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "context": self.conversation_history[-5:] if self.conversation_history else []
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                self.conversation_history.append(prompt)
                return result.get("response", "")
            return f"Error: Ollama returned {response.status_code}"
        except Exception as e:
            return f"Error querying Ollama: {e}"
    
    def convert_happy_paisa(self, amount: float, from_currency: str, to_currency: str) -> dict:
        """Convert between Happy Paisa and INR"""
        if from_currency.upper() == "HP" and to_currency.upper() == "INR":
            inr_value = amount * HAPPY_PAISA_RATE
            return {
                "amount": inr_value,
                "currency": "INR",
                "rate": HAPPY_PAISA_RATE,
                "original": amount
            }
        elif from_currency.upper() == "INR" and to_currency.upper() == "HP":
            hp_value = amount / HAPPY_PAISA_RATE
            return {
                "amount": hp_value,
                "currency": "HP",
                "rate": HAPPY_PAISA_RATE,
                "original": amount
            }
        return {"error": "Invalid conversion pair"}
    
    def process_voice_command(self, text: str) -> str:
        """Process voice command and route to appropriate handler"""
        text_lower = text.lower()
        
        # Happy Paisa conversion
        if "happy paisa" in text_lower or "hp" in text_lower:
            return self._handle_happy_paisa_query(text_lower)
        
        # Health check
        elif "health" in text_lower or "status" in text_lower:
            return self._handle_health_check()
        
        # Agent status
        elif "agent" in text_lower or "lucy" in text_lower or "tansi" in text_lower or "kyra" in text_lower:
            return self._handle_agent_query(text_lower)
        
        # Default: Send to Ollama
        else:
            return self.query_ollama(f"You are Mr. Happy, the Digital CEO of Axzora. Respond concisely: {text}")
    
    def _handle_happy_paisa_query(self, text: str) -> str:
        """Handle Happy Paisa related queries"""
        import re
        
        # Extract numbers from text
        numbers = re.findall(r'\d+\.?\d*', text)
        
        if numbers:
            amount = float(numbers[0])
            if "inr" in text or "rupee" in text:
                result = self.convert_happy_paisa(amount, "INR", "HP")
                return f"₹{amount:,.2f} = {result['amount']:,.4f} Happy Paisa"
            else:
                result = self.convert_happy_paisa(amount, "HP", "INR")
                return f"{amount} Happy Paisa = ₹{result['amount']:,.2f}"
        
        return f"Current Happy Paisa rate: 1 HP =₹{HAPPY_PAISA_RATE:,}"
    
    def _handle_health_check(self) -> str:
        """Check health of all services"""
        status = []
        
        # Check Ollama
        if self.check_ollama_health():
            status.append("✅ Ollama: Running")
        else:
            status.append("❌ Ollama: Down")
        
        # Check Mesh Node
        try:
            response = requests.get(f"{self.mesh_url}/health", timeout=5)
            status.append("✅ Mesh Node: Running")
        except:
            status.append("❌ Mesh Node: Down")
        
        return "\n".join(status)
    
    def _handle_agent_query(self, text: str) -> str:
        """Handle agent-related queries"""
        agent_status = []
        for name, config in AGENTS.items():
            try:
                response = requests.get(f"http://localhost:{config['port']}/health", timeout=2)
                agent_status.append(f"✅ {name.title()}: {config['role']}")
            except:
                agent_status.append(f"❌ {name.title()}: Offline")
        
        return "\n".join(agent_status)


class WebSocketServer:
    """WebSocket server for voice bridge"""
    
    def __init__(self, voice_handler: MrHappyVoice, port: int = WEBSOCKET_PORT):
        self.voice = voice_handler
        self.port = port
        self.clients = set()
    
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                response = self.voice.process_voice_command(data.get("text", ""))
                await websocket.send(json.dumps({"response": response}))
        finally:
            self.clients.discard(websocket)
    
    def start(self):
        """Start WebSocket server"""
        import websockets
        
        print(f"Starting WebSocket server on port {self.port}...")
        start_server = websockets.serve(self.handle_client, "0.0.0.0", self.port)
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


# ============ CLI INTERFACE ============

def main():
    """Main entry point"""
    global MODEL, OLLAMA_URL
    
    import argparse
    parser = argparse.ArgumentParser(description="Mr. Happy Voice Integration")
    parser.add_argument("--text", type=str, help="Process text command")
    parser.add_argument("--ws", action="store_true", help="Start WebSocket server")
    parser.add_argument("--health", action="store_true", help="Check service health")
    parser.add_argument("--model", type=str, default=MODEL, help="Ollama model to use")
    parser.add_argument("--ollama-url", type=str, default=OLLAMA_URL, help="Ollama URL")
    
    args = parser.parse_args()
    
    # Update global config from args
    MODEL = args.model
    OLLAMA_URL = args.ollama_url
    
    voice = MrHappyVoice()
    
    if args.health:
        print(voice._handle_health_check())
        return
    
    if args.ws:
        print("Starting WebSocket mode...")
        server = WebSocketServer(voice)
        server.start()
        return
    
    if args.text:
        print(voice.process_voice_command(args.text))
        return
    
    # Interactive mode
    print("Mr. Happy Voice Interface")
    print("Type 'exit' to quit, 'health' for status check")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "health":
                print(voice._handle_health_check())
                continue
            
            response = voice.process_voice_command(user_input)
            print(f"Mr. Happy: {response}")
        except KeyboardInterrupt:
            break
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
