#!/usr/bin/env python3
"""Mr Happy Voice Interface - Voice Assistant System"""

import asyncio
import json
import subprocess
from datetime import datetime
from typing import Optional
import httpx


class MrHappyVoice:
    """Voice interface for Mr Happy AI"""
    
    def __init__(self):
        self.wake_word = "Hey Mr Happy"
        self.listening = False
        self.mr_happy_endpoint = "http://localhost:8001"
        
    async def listen(self):
        """Start voice listening loop"""
        print("\n🎙️  MR HAPPY VOICE ASSISTANT")
        print(f"   Wake word: '{self.wake_word}'")
        print("   (Text mode - type your commands)\n")
        
        while True:
            try:
                # In real implementation, this would use speech recognition
                # For now, use text input
                user_input = input("🎤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("👋 Goodbye!")
                    break
                
                # Check for wake word
                if self.wake_word.lower() in user_input.lower():
                    command = user_input.lower().replace(self.wake_word.lower(), "").strip()
                else:
                    command = user_input
                
                # Process command
                response = await self.process_command(command)
                print(f"🤖 Mr Happy: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    
    async def process_command(self, command: str) -> str:
        """Process voice command"""
        
        # Command routing
        if command.startswith("/"):
            return await self._handle_slash_command(command)
        
        # Send to Mr Happy brain
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mr_happy_endpoint}/chat",
                    json={"message": command},
                    timeout=30.0
                )
                result = response.json()
                return result.get("response", "I'm thinking...")
        except Exception as e:
            return f"I'm Mr Happy! I heard: '{command}'. (Processing: {str(e)})"
    
    async def _handle_slash_command(self, command: str) -> str:
        """Handle special commands"""
        
        parts = command.split()
        cmd = parts[0].lower()
        
        commands = {
            "/status": self._cmd_status,
            "/agents": self._cmd_agents,
            "/sync": self._cmd_sync,
            "/search": self._cmd_search,
            "/code": self._cmd_code,
            "/help": self._cmd_help,
        }
        
        handler = commands.get(cmd, self._cmd_unknown)
        return await handler(parts[1:])
    
    async def _cmd_status(self, args) -> str:
        """System status"""
        return "✅ All systems operational. Mr Happy is online and ready."
    
    async def _cmd_agents(self, args) -> str:
        """List agents"""
        return "🤖 Active agents: Mr Happy (CEO), Code Agent, Research Agent, Auto Agent, Guard Agent"
    
    async def _cmd_sync(self, args) -> str:
        """Sync device"""
        return "📱 Device sync initiated. Transferring data to backup location."
    
    async def _cmd_search(self, args) -> str:
        """Web search"""
        query = " ".join(args) if args else "general"
        return f"🔍 Searching for: {query}... (Results would appear here)"
    
    async def _cmd_code(self, args) -> str:
        """Generate code"""
        task = " ".join(args) if args else "hello world"
        return f"💻 Generating code for: {task}...\n```python\nprint('Hello from Mr Happy!')\n```"
    
    async def _cmd_help(self, args) -> str:
        """Show help"""
        return """🤖 Mr Happy Commands:
/status - System status
/agents - List AI agents
/sync - Sync your device
/search <query> - Web search
/code <task> - Generate code
/help - Show this help

Or just ask me anything!"""
    
    async def _cmd_unknown(self, args) -> str:
        """Unknown command"""
        return f"❓ Unknown command. Type /help for available commands."
    
    def speak(self, text: str):
        """Text-to-speech output"""
        # In real implementation, use TTS engine
        print(f"🔊 Speaking: {text[:100]}...")


async def main():
    """Main entry point"""
    voice = MrHappyVoice()
    await voice.listen()


if __name__ == "__main__":
    asyncio.run(main())
