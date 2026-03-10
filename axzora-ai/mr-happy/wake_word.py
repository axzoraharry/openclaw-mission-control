#!/usr/bin/env python3
"""
Mr Happy Wake Word Listener
Listens for "Hey Mr Happy" and activates voice mode.

Dependencies:
  pip install SpeechRecognition pyttsx3 pyaudio
  (pyaudio on Windows: pip install pipwin; pipwin install pyaudio)
"""

import sys
import os
import time
import threading
import json

# Add project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

WAKE_WORDS = ["hey mr happy", "mr happy", "hey happy", "ok happy"]
STOP_WORDS = ["goodbye mr happy", "stop listening", "sleep mr happy"]

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("[SpeechRecognition not installed — run: pip install SpeechRecognition]")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# ─────────────────────────────────────────────
# TTS helper
# ─────────────────────────────────────────────
_tts_lock = threading.Lock()
_tts = None

def _init_tts():
    global _tts
    if TTS_AVAILABLE and _tts is None:
        try:
            _tts = pyttsx3.init()
            _tts.setProperty("rate", 160)
            _tts.setProperty("volume", 0.95)
        except Exception:
            pass

def speak(text: str):
    _init_tts()
    if _tts is None:
        print(f"  [Mr Happy]: {text}")
        return
    with _tts_lock:
        try:
            _tts.say(text)
            _tts.runAndWait()
        except Exception:
            print(f"  [Mr Happy]: {text}")

def speak_async(text: str):
    threading.Thread(target=speak, args=(text,), daemon=True).start()


# ─────────────────────────────────────────────
# LLM (via Ollama directly)
# ─────────────────────────────────────────────
def ask_mr_happy(text: str) -> str:
    try:
        import requests
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": (
                    "You are Mr Happy, the Digital CEO of Axzora. "
                    "Respond in 1-2 short sentences suitable for voice. "
                    f"User said: {text}"
                ),
                "stream": False
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception as e:
        return f"Sorry, I had a connection issue: {e}"
    return "I didn't catch that."


# ─────────────────────────────────────────────
# WAKE WORD LISTENER
# ─────────────────────────────────────────────
class WakeWordListener:
    """
    Continuously listens via microphone.
    On detecting a wake word → activates and listens for a command.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self.microphone = sr.Microphone() if SR_AVAILABLE else None
        self.active = False       # True when in command-listening mode
        self.running = False
        self.session_count = 0

        if not SR_AVAILABLE:
            raise RuntimeError("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")

        # Calibrate noise level
        print("[Calibrating microphone noise level...]")
        with self.microphone as src:
            self.recognizer.adjust_for_ambient_noise(src, duration=1.5)
        print("[Calibration done]")

    def _listen_once(self, timeout: int = 5, phrase_limit: int = 8) -> str:
        """Listen for one phrase and return transcribed text (lowercase)"""
        try:
            with self.microphone as src:
                audio = self.recognizer.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            text = self.recognizer.recognize_google(audio).lower().strip()
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            return ""

    def _contains_wake_word(self, text: str) -> bool:
        return any(w in text for w in WAKE_WORDS)

    def _contains_stop_word(self, text: str) -> bool:
        return any(w in text for w in STOP_WORDS)

    def _handle_command(self, command: str):
        """Process a voice command from the user"""
        print(f"\n  [Command received]: {command}")

        if self._contains_stop_word(command):
            speak("Okay, going to sleep. Say Hey Mr Happy when you need me.")
            self.active = False
            return

        # Special commands
        if "status" in command:
            speak("All systems are online. Backend, agents, and voice server are running.")
            return
        if "what time" in command or "time is it" in command:
            from datetime import datetime
            t = datetime.now().strftime("%I:%M %p")
            speak(f"It is {t}")
            return
        if "your name" in command or "who are you" in command:
            speak("I am Mr Happy, the Digital CEO of Axzora. Your AI assistant.")
            return

        # General AI response
        response = ask_mr_happy(command)
        print(f"  [Mr Happy]: {response}")
        speak(response)

    def start(self):
        """Start the wake word loop"""
        self.running = True

        print("\n╔══════════════════════════════════════════╗")
        print("║  Mr Happy Wake Word Listener — ACTIVE    ║")
        print(f"║  Wake words: {', '.join(WAKE_WORDS[:2])}         ║")
        print("║  Say 'Hey Mr Happy' to activate          ║")
        print("║  Press Ctrl+C to stop                    ║")
        print("╚══════════════════════════════════════════╝\n")

        speak("Wake word listener active. Say Hey Mr Happy to talk to me.")

        while self.running:
            try:
                text = self._listen_once(timeout=10)

                if not text:
                    continue

                print(f"  [Heard]: {text}")

                if self._contains_wake_word(text):
                    self.session_count += 1
                    self.active = True
                    speak("Yes? I'm listening.")
                    print("  [Activated — waiting for command...]")

                    # Listen for command (up to 3 attempts)
                    command = ""
                    for _ in range(3):
                        command = self._listen_once(timeout=6, phrase_limit=10)
                        if command:
                            break
                        speak("I didn't catch that, please repeat.")

                    if command:
                        self._handle_command(command)
                    else:
                        speak("I didn't hear anything. Say Hey Mr Happy when ready.")
                    self.active = False

            except KeyboardInterrupt:
                print("\n\n[Wake word listener stopped]")
                self.running = False
                break

        speak("Mr Happy is going offline. Goodbye!")

    def stop(self):
        self.running = False


# ─────────────────────────────────────────────
# SIMULATED MODE (no microphone)
# ─────────────────────────────────────────────
def text_simulation_mode():
    """Simulate wake word via keyboard for testing on headless systems"""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Mr Happy Wake Word — TEXT SIMULATION    ║")
    print("║  Type: 'hey mr happy' to activate        ║")
    print("║  Type: quit to exit                      ║")
    print("╚══════════════════════════════════════════╝\n")

    speak("Text simulation mode. Type hey mr happy to activate.")

    while True:
        try:
            text = input("  [mic] ").strip().lower()
            if not text:
                continue
            if text in ("quit", "exit"):
                speak("Goodbye!")
                break

            if any(w in text for w in WAKE_WORDS):
                speak("Yes? I'm listening.")
                command = input("  [command] ").strip().lower()
                if command:
                    response = ask_mr_happy(command)
                    print(f"  [Mr Happy]: {response}")
                    speak(response)
                else:
                    speak("I didn't hear anything.")
        except KeyboardInterrupt:
            break

    print("\n[Simulation ended]")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(description="Mr Happy Wake Word Listener")
    p.add_argument("--sim", action="store_true", help="Text simulation (no mic required)")
    p.add_argument("--test", action="store_true", help="Quick TTS + LLM test and exit")
    args = p.parse_args()

    if args.test:
        print("[Testing TTS and LLM...]")
        speak("Hello, I am Mr Happy. Testing voice output.")
        r = ask_mr_happy("Say hello in one sentence.")
        print(f"LLM response: {r}")
        speak(r)
        return

    if args.sim or not SR_AVAILABLE:
        text_simulation_mode()
    else:
        try:
            listener = WakeWordListener()
            listener.start()
        except RuntimeError as e:
            print(f"[Wake word error: {e}]")
            print("[Falling back to text simulation mode...]")
            text_simulation_mode()


if __name__ == "__main__":
    main()
