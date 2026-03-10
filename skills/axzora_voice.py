#!/usr/bin/env python3
"""
Axzora Voice System - STT + TTS + LLM Integration
Adds full voice capabilities to Mr Happy
"""

import asyncio
import json
import os
import sys
import subprocess
import websockets
import requests
from datetime import datetime
from typing import Optional
import threading
import base64
import io

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

OLLAMA_URL = "http://localhost:11434"
MISSION_CONTROL_URL = "http://localhost:8000"
DEFAULT_MODEL = "llama3.2:3b"
WEBSOCKET_PORT = 8765


class SpeechToText:
    """Speech to Text using Whisper (local) or cloud APIs"""

    def __init__(self, model: str = "base"):
        self.model_name = model
        self.whisper_model = None

        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model(model)
                print(f"[Whisper model '{model}' loaded]")
            except Exception as e:
                print(f"[Whisper load failed: {e}]")

    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text"""
        if self.whisper_model:
            try:
                import numpy as np
                import wave

                with io.BytesIO(audio_data) as audio_buffer:
                    with wave.open(audio_buffer, "rb") as wf:
                        frames = wf.readframes(wf.getnframes())
                        audio_np = np.frombuffer(frames, dtype=np.int16)
                        audio_np = audio_np.astype(np.float32) / 32768.0

                result = self.whisper_model.transcribe(audio_np)
                return result["text"].strip()
            except Exception as e:
                return f"STT Error: {e}"

        return "STT not available - install whisper: pip install openai-whisper"

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe audio file"""
        if not WHISPER_AVAILABLE:
            return "Whisper not installed"

        try:
            result = self.whisper_model.transcribe(file_path)
            return result["text"].strip()
        except Exception as e:
            return f"Error: {e}"


class TextToSpeech:
    """Text to Speech using pyttsx3 (local) or gTTS (cloud)"""

    def __init__(self, engine: str = "pyttsx3"):
        self.engine = engine
        self.tts_engine = None

        if engine == "pyttsx3" and TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)
                self.tts_engine.setProperty("volume", 0.9)
                print("[TTS engine initialized]")
            except Exception as e:
                print(f"[TTS init failed: {e}]")

    def speak(self, text: str) -> bytes:
        """Convert text to speech and return audio bytes"""
        if self.tts_engine:
            try:
                with io.BytesIO() as audio_buffer:
                    self.tts_engine.save_to_file(text, audio_buffer)
                    self.tts_engine.runAndWait()
                    return audio_buffer.getvalue()
            except Exception as e:
                return f"TTS Error: {e}".encode()

        return b"TTS not available"

    def speak_to_file(self, text: str, file_path: str) -> bool:
        """Save TTS output to file"""
        if not self.tts_engine:
            return False

        try:
            self.tts_engine.save_to_file(text, file_path)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"TTS Error: {e}")
            return False


class AxzoraVoice:
    """Complete voice system for Mr Happy"""

    def __init__(self, llm_model: str = DEFAULT_MODEL):
        self.ollama_url = OLLAMA_URL
        self.model = llm_model
        self.stt = SpeechToText("base")
        self.tts = TextToSpeech("pyttsx3")
        self.conversation_history = []
        self.is_listening = False

        print("[Axzora Voice System Initialized]")
        print(f"   STT: {'Whisper' if WHISPER_AVAILABLE else 'Not installed'}")
        print(f"   TTS: {'pyttsx3' if TTS_AVAILABLE else 'Not installed'}")
        print(f"   LLM: {llm_model}")

    def check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False

    def query_llm(self, prompt: str) -> str:
        """Query Ollama for response"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "context": self.conversation_history[-5:],
        }

        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate", json=payload, timeout=60
            )
            if r.status_code == 200:
                response = r.json().get("response", "")
                self.conversation_history.append(prompt)
                return response
            return f"LLM Error: {r.status_code}"
        except Exception as e:
            return f"Connection error: {e}"

    def process_voice(self, audio_data: bytes) -> dict:
        """Complete voice pipeline: STT -> LLM -> TTS"""
        text = self.stt.transcribe_audio(audio_data)

        if not text or text.startswith("STT"):
            return {"error": text, "audio": None}

        response = self.query_llm(text)

        return {
            "transcribed": text,
            "response": response,
            "audio": self.tts.speak(response),
        }

    def process_text(self, text: str) -> str:
        """Process text input and return LLM response"""
        response = self.query_llm(text)

        if self.tts.tts_engine:
            threading.Thread(target=self.tts.speak, args=(response,)).start()

        return response


class VoiceWebSocketServer:
    """WebSocket server for real-time voice"""

    def __init__(self, voice_system: AxzoraVoice, port: int = WEBSOCKET_PORT):
        self.voice = voice_system
        self.port = port
        self.clients = set()

    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        print(f"[Voice client connected]")

        try:
            async for message in websocket:
                data = json.loads(message)

                if data.get("type") == "audio":
                    audio_bytes = base64.b64decode(data.get("data", ""))
                    result = self.voice.process_voice(audio_bytes)
                    await websocket.send(json.dumps(result))

                elif data.get("type") == "text":
                    response = self.voice.process_text(data.get("text", ""))
                    await websocket.send(json.dumps({"response": response}))

                elif data.get("type") == "ping":
                    await websocket.send(json.dumps({"status": "pong"}))

        except Exception as e:
            print(f"❌ Voice error: {e}")
        finally:
            self.clients.discard(websocket)

    def start(self):
        """Start WebSocket server"""
        print(f"[Starting voice server on port {self.port}...]")
        start_server = websockets.serve(self.handle_client, "0.0.0.0", self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Axzora Voice System")
    parser.add_argument("--ws", action="store_true", help="Start WebSocket server")
    parser.add_argument("--text", type=str, help="Process text command")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="LLM model")
    parser.add_argument(
        "--install-deps", action="store_true", help="Install dependencies"
    )

    args = parser.parse_args()

    if args.install_deps:
        print("Installing voice dependencies...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "openai-whisper",
                "pyttsx3",
                "websockets",
            ]
        )
        print("[Dependencies installed. Restart the voice system.]")
        return

    voice = AxzoraVoice(args.model)

    if args.ws:
        server = VoiceWebSocketServer(voice)
        server.start()

    elif args.text:
        print(f"\nYou: {args.text}")
        response = voice.process_text(args.text)
        print(f"Mr Happy: {response}")

    else:
        print("\n[Axzora Voice System - Interactive Mode]")
        print("Type 'quit' to exit\n")

        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() == "quit":
                    break

                response = voice.process_text(user_input)
                print(f"Mr Happy: {response}\n")
            except KeyboardInterrupt:
                break

        print("Goodbye!")


if __name__ == "__main__":
    main()
