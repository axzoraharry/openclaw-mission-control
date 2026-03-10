#!/usr/bin/env python3
"""
Mr Happy Voice Integration
Connects AxzoraVoice (STT/TTS) with MrHappyBrain (LLM/Agents)
Full pipeline: Microphone → Whisper STT → Brain → Ollama LLM → pyttsx3 TTS → Speaker
"""

import asyncio
import json
import sys
import os
import threading
import base64
import io
from datetime import datetime
from typing import Optional

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'skills'))

import requests

# Voice deps
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[whisper not installed — run: pip install openai-whisper]")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[pyttsx3 not installed — run: pip install pyttsx3]")

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

# Settings
OLLAMA_URL = "http://localhost:11434"
MISSION_CONTROL_URL = "http://localhost:8000"
MR_HAPPY_AGENT_URL = "http://localhost:8001"
DEFAULT_MODEL = "llama3.2:3b"
VOICE_WS_PORT = 8765


# ─────────────────────────────────────────────
# STT
# ─────────────────────────────────────────────
class SpeechToText:
    """Whisper-based speech recognition"""

    def __init__(self, model: str = "base"):
        self.model_name = model
        self.model = None
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model(model)
                print(f"  [Whisper '{model}' loaded]")
            except Exception as e:
                print(f"  [Whisper load failed: {e}]")

    def transcribe_bytes(self, audio_data: bytes) -> str:
        if not self.model:
            return ""
        try:
            import numpy as np, wave
            buf = io.BytesIO(audio_data)
            with wave.open(buf, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            result = self.model.transcribe(audio_np)
            return result["text"].strip()
        except Exception as e:
            return f"[STT error: {e}]"

    def transcribe_file(self, path: str) -> str:
        if not self.model:
            return ""
        try:
            result = self.model.transcribe(path)
            return result["text"].strip()
        except Exception as e:
            return f"[STT error: {e}]"


# ─────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────
class TextToSpeech:
    """pyttsx3-based text-to-speech"""

    def __init__(self):
        self.engine = None
        self._lock = threading.Lock()
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 160)
                self.engine.setProperty("volume", 0.95)
                # Use a natural-sounding voice if available
                voices = self.engine.getProperty("voices")
                if voices:
                    # Prefer second voice (usually female/different accent)
                    self.engine.setProperty("voice", voices[min(1, len(voices)-1)].id)
                print("  [pyttsx3 TTS ready]")
            except Exception as e:
                print(f"  [TTS init failed: {e}]")

    def speak(self, text: str):
        """Speak text aloud (blocking)"""
        if not self.engine:
            print(f"  [TTS unavailable] {text}")
            return
        with self._lock:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"  [TTS speak error: {e}]")

    def speak_async(self, text: str):
        """Speak in background thread"""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def save_to_file(self, text: str, path: str) -> bool:
        if not self.engine:
            return False
        with self._lock:
            try:
                self.engine.save_to_file(text, path)
                self.engine.runAndWait()
                return True
            except:
                return False


# ─────────────────────────────────────────────
# BRAIN (LLM + Agents)
# ─────────────────────────────────────────────
class MrHappyVoiceBrain:
    """Mr Happy's intelligence layer — routes to Ollama or Agent endpoint"""

    AGENT_SKILLS = {
        "code": ["code", "program", "debug", "git", "script", "function"],
        "research": ["search", "research", "find", "analyze", "latest", "news"],
        "automation": ["run", "execute", "schedule", "automate", "backup", "monitor"],
        "security": ["security", "scan", "protect", "encrypt", "audit"],
    }

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.history = []
        self.session_start = datetime.now()

    def _route(self, text: str) -> str:
        t = text.lower()
        for skill, keywords in self.AGENT_SKILLS.items():
            if any(k in t for k in keywords):
                return skill
        return "chat"

    def _system_prompt(self, skill: str) -> str:
        prompts = {
            "chat": "You are Mr Happy, the Digital CEO of Axzora — friendly, smart, concise. Keep voice replies under 3 sentences.",
            "code": "You are Mr Happy's Code Agent. Write clean, working code. Keep explanations brief.",
            "research": "You are Mr Happy's Research Agent. Give concise summaries, 2-3 sentences max.",
            "automation": "You are Mr Happy's Automation Agent. Describe the automation approach in 2 sentences.",
            "security": "You are Mr Happy's Security Agent. Give a clear, actionable security assessment.",
        }
        return prompts.get(skill, prompts["chat"])

    def ask(self, user_text: str) -> str:
        """Synchronous LLM query"""
        skill = self._route(user_text)
        system = self._system_prompt(skill)

        # Build conversation context (last 4 turns)
        context_parts = []
        for turn in self.history[-4:]:
            context_parts.append(f"User: {turn['user']}\nMr Happy: {turn['assistant']}")
        context_str = "\n".join(context_parts)

        full_prompt = f"{system}\n\n{context_str}\n\nUser: {user_text}\nMr Happy:"

        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": self.model, "prompt": full_prompt, "stream": False},
                timeout=45
            )
            if r.status_code == 200:
                response = r.json().get("response", "").strip()
                self.history.append({"user": user_text, "assistant": response})
                return response
            return f"LLM error {r.status_code}"
        except Exception as e:
            return f"Connection error: {e}"

    def status(self) -> dict:
        try:
            r = requests.get(f"{MR_HAPPY_AGENT_URL}/health", timeout=3)
            agent_ok = r.status_code == 200
        except:
            agent_ok = False
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            ollama_ok = r.status_code == 200
        except:
            ollama_ok = False
        return {
            "agent_service": "online" if agent_ok else "offline",
            "ollama": "online" if ollama_ok else "offline",
            "model": self.model,
            "session_turns": len(self.history),
        }


# ─────────────────────────────────────────────
# INTEGRATED VOICE SYSTEM
# ─────────────────────────────────────────────
class MrHappyVoice:
    """
    Full voice loop:
    mic → STT → Brain (LLM) → TTS → speaker
    Also supports text-in / text-out for WebSocket clients
    """

    def __init__(self):
        print("\n╔══════════════════════════════════════╗")
        print("║   Mr Happy Voice System Booting...   ║")
        print("╚══════════════════════════════════════╝\n")

        self.stt = SpeechToText("base")
        self.tts = TextToSpeech()
        self.brain = MrHappyVoiceBrain()
        self.running = False

        print(f"  STT  : {'Whisper ready' if WHISPER_AVAILABLE else 'Not installed'}")
        print(f"  TTS  : {'pyttsx3 ready' if TTS_AVAILABLE else 'Not installed'}")
        print(f"  LLM  : {DEFAULT_MODEL} via Ollama")
        print()

    def process_text(self, text: str, speak: bool = True) -> str:
        """Text in → Brain → (optional TTS) → text out"""
        print(f"  You  : {text}")
        response = self.brain.ask(text)
        print(f"  Mr H : {response}")
        if speak:
            self.tts.speak_async(response)
        return response

    def process_audio_bytes(self, audio_data: bytes) -> dict:
        """Audio bytes → STT → Brain → TTS → result dict"""
        transcribed = self.stt.transcribe_bytes(audio_data)
        if not transcribed or transcribed.startswith("[STT"):
            return {"error": transcribed or "Could not transcribe", "response": None}

        response = self.brain.ask(transcribed)
        self.tts.speak_async(response)
        return {"transcribed": transcribed, "response": response}

    def interactive(self):
        """Keyboard-based interactive loop"""
        print("╔══════════════════════════════════════════╗")
        print("║  Mr Happy Voice — Text Mode              ║")
        print("║  Commands: /status /clear /quit          ║")
        print("╚══════════════════════════════════════════╝\n")

        self.tts.speak_async("Hello! I'm Mr Happy, your AI assistant. How can I help you today?")

        self.running = True
        while self.running:
            try:
                user = input("You: ").strip()
                if not user:
                    continue
                if user.lower() in ("/quit", "quit", "exit"):
                    self.tts.speak("Goodbye! Have a great day!")
                    break
                elif user.lower() == "/status":
                    s = self.brain.status()
                    print(f"  Status: {json.dumps(s, indent=2)}")
                elif user.lower() == "/clear":
                    self.brain.history.clear()
                    print("  [Conversation cleared]")
                else:
                    self.process_text(user)
            except KeyboardInterrupt:
                print("\n[Ctrl+C — goodbye!]")
                break

        print("\nMr Happy offline. Goodbye!")


# ─────────────────────────────────────────────
# WEBSOCKET SERVER (port 8765)
# ─────────────────────────────────────────────
class VoiceWebSocketServer:
    """
    WebSocket server so browser / other apps can talk to Mr Happy:
      { "type": "text",  "text": "hello" }
      { "type": "audio", "data": "<base64 wav>" }
      { "type": "ping" }
    """

    def __init__(self, voice: MrHappyVoice, port: int = VOICE_WS_PORT):
        self.voice = voice
        self.port = port
        self.clients: set = set()

    async def handle(self, websocket):
        self.clients.add(websocket)
        print(f"  [Voice WS] client connected ({len(self.clients)} total)")

        # Send welcome
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Mr Happy Voice Server ready",
            "port": self.port
        }))

        try:
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                    msg_type = data.get("type", "text")

                    if msg_type == "text":
                        text = data.get("text", "").strip()
                        if text:
                            response = self.voice.process_text(text, speak=True)
                            await websocket.send(json.dumps({
                                "type": "response",
                                "transcribed": text,
                                "response": response,
                                "timestamp": datetime.now().isoformat()
                            }))

                    elif msg_type == "audio":
                        audio_b64 = data.get("data", "")
                        audio_bytes = base64.b64decode(audio_b64)
                        result = self.voice.process_audio_bytes(audio_bytes)
                        result["type"] = "response"
                        result["timestamp"] = datetime.now().isoformat()
                        await websocket.send(json.dumps(result))

                    elif msg_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))

                    elif msg_type == "status":
                        s = self.voice.brain.status()
                        s["type"] = "status"
                        await websocket.send(json.dumps(s))

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))

        except Exception as e:
            print(f"  [Voice WS] client error: {e}")
        finally:
            self.clients.discard(websocket)
            print(f"  [Voice WS] client disconnected ({len(self.clients)} remaining)")

    async def start(self):
        if not WS_AVAILABLE:
            print("[websockets not installed — run: pip install websockets]")
            return
        print(f"\n[Voice WebSocket Server on ws://localhost:{self.port}]")
        async with websockets.serve(self.handle, "0.0.0.0", self.port):
            print(f"  Listening for voice clients...")
            await asyncio.Future()  # run forever


# ─────────────────────────────────────────────
# ENTRY POINTS
# ─────────────────────────────────────────────
def run_interactive():
    voice = MrHappyVoice()
    voice.interactive()


def run_ws_server():
    voice = MrHappyVoice()
    server = VoiceWebSocketServer(voice)
    asyncio.run(server.start())


def main():
    import argparse
    p = argparse.ArgumentParser(description="Mr Happy Voice System")
    p.add_argument("--ws", action="store_true", help="Start WebSocket voice server (port 8765)")
    p.add_argument("--text", type=str, help="One-shot text query")
    p.add_argument("--status", action="store_true", help="Show system status and exit")
    args = p.parse_args()

    if args.status:
        voice = MrHappyVoice()
        print(json.dumps(voice.brain.status(), indent=2))
        return

    if args.text:
        voice = MrHappyVoice()
        response = voice.process_text(args.text, speak=True)
        print(f"\nMr Happy: {response}")
        return

    if args.ws:
        run_ws_server()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
