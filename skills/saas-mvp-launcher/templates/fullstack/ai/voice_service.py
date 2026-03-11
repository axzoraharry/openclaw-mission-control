#!/usr/bin/env python3
"""Mr Happy Voice Service - WebSocket server for voice AI"""

import os
import sys
import json
import asyncio
import argparse
import base64
import io
from datetime import datetime
from typing import Optional

import httpx
import websockets
from fastapi import FastAPI
from pydantic import BaseModel

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = os.getenv("MODEL", "llama3.2:3b")
VOICE_WS_PORT = int(os.getenv("VOICE_WS_PORT", "8765"))

# Try to import voice libraries
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[Warning] Whisper not installed - STT disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[Warning] pyttsx3 not installed - TTS disabled")


class VoiceBrain:
    """Simple LLM brain for voice responses"""
    
    def __init__(self):
        self.history = []
    
    async def ask(self, text: str) -> str:
        """Query the LLM"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": MODEL,
                        "prompt": f"You are Mr Happy, a helpful voice assistant. Keep responses brief (1-2 sentences). User: {text}\nMr Happy:",
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                return "I'm having trouble connecting to my brain right now."
        except Exception as e:
            return f"Error: {str(e)[:50]}"


class VoiceWebSocketServer:
    """WebSocket server for real-time voice interaction"""
    
    def __init__(self, brain: VoiceBrain, port: int = VOICE_WS_PORT):
        self.brain = brain
        self.port = port
        self.clients = set()
        self.whisper_model = None
        
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                print(f"[Whisper model loaded]")
            except Exception as e:
                print(f"[Whisper load failed: {e}]")
    
    async def handle_client(self, websocket):
        self.clients.add(websocket)
        print(f"[Voice client connected - {len(self.clients)} total]")
        
        # Send welcome
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Mr Happy Voice Server ready",
            "port": self.port
        }))
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "text")
                    
                    if msg_type == "text":
                        text = data.get("text", "").strip()
                        if text:
                            response = await self.brain.ask(text)
                            await websocket.send(json.dumps({
                                "type": "response",
                                "transcribed": text,
                                "response": response,
                                "timestamp": datetime.now().isoformat()
                            }))
                    
                    elif msg_type == "audio":
                        if self.whisper_model:
                            audio_b64 = data.get("data", "")
                            audio_bytes = base64.b64decode(audio_b64)
                            # Transcribe and respond
                            text = await self._transcribe(audio_bytes)
                            if text:
                                response = await self.brain.ask(text)
                                await websocket.send(json.dumps({
                                    "type": "response",
                                    "transcribed": text,
                                    "response": response,
                                    "timestamp": datetime.now().isoformat()
                                }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "STT not available"
                            }))
                    
                    elif msg_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                    
                    elif msg_type == "status":
                        await websocket.send(json.dumps({
                            "type": "status",
                            "ollama": "connected",
                            "whisper": "loaded" if self.whisper_model else "unavailable",
                            "clients": len(self.clients)
                        }))
                
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
        
        except Exception as e:
            print(f"[Voice client error: {e}]")
        finally:
            self.clients.discard(websocket)
            print(f"[Voice client disconnected - {len(self.clients)} remaining]")
    
    async def _transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe audio bytes using Whisper"""
        if not self.whisper_model:
            return None
        try:
            import numpy as np
            import wave
            
            with io.BytesIO(audio_bytes) as buf:
                with wave.open(buf, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            result = self.whisper_model.transcribe(audio_np)
            return result["text"].strip()
        except Exception as e:
            print(f"[Transcription error: {e}]")
            return None
    
    async def start(self):
        print(f"\n[Voice WebSocket Server on ws://0.0.0.0:{self.port}]")
        async with websockets.serve(self.handle_client, "0.0.0.0", self.port):
            print("  Listening for voice clients...")
            await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(description="Mr Happy Voice Service")
    parser.add_argument("--ws", action="store_true", help="Start WebSocket server")
    parser.add_argument("--text", type=str, help="One-shot text query")
    args = parser.parse_args()
    
    brain = VoiceBrain()
    
    if args.text:
        response = asyncio.run(brain.ask(args.text))
        print(f"\nMr Happy: {response}")
    elif args.ws:
        server = VoiceWebSocketServer(brain)
        asyncio.run(server.start())
    else:
        print("\n[Mr Happy Voice Service]")
        print("  --ws     Start WebSocket server")
        print("  --text   One-shot text query")
        print("\nStarting WebSocket server by default...")
        server = VoiceWebSocketServer(brain)
        asyncio.run(server.start())


if __name__ == "__main__":
    main()
