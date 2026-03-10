#!/usr/bin/env python3
"""Mr Happy AI Brain - Central Intelligence System"""

import asyncio
import json
import sys
import os
import threading
import websockets
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

# Optional TTS (speak responses aloud)
try:
    import pyttsx3 as _pyttsx3
    _tts_engine = _pyttsx3.init()
    _tts_engine.setProperty("rate", 160)
    _tts_lock = threading.Lock()
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False


def _speak_async(text: str):
    """Speak text in a background thread (non-blocking)"""
    if not TTS_AVAILABLE:
        return
    def _run():
        with _tts_lock:
            try:
                _tts_engine.say(text)
                _tts_engine.runAndWait()
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True).start()


@dataclass
class Task:
    id: str
    type: str
    payload: dict
    priority: int = 1
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Agent:
    id: str
    name: str
    role: str
    skills: List[str]
    status: str = "idle"
    current_task: Optional[str] = None


class MrHappyBrain:
    """Central AI Brain for Axzora System"""
    
    def __init__(self, gateway_url: str = "ws://localhost:18789"):
        self.gateway_url = gateway_url
        self.mission_control = "http://localhost:8000"
        self.ollama_url = "http://localhost:11434"
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Task] = []
        self.memory: List[dict] = []
        self.running = False
        self.websocket = None
        
        # Register core agents
        self._register_agents()
    
    def _register_agents(self):
        """Register AI agent swarm"""
        agents_config = [
            Agent("mr_happy_001", "Mr Happy Prime", "CEO", 
                  ["chat", "orchestrate", "decide", "voice"]),
            Agent("coder_001", "Code Agent", "Developer",
                  ["code", "debug", "review", "git"]),
            Agent("research_001", "Research Agent", "Analyst",
                  ["search", "analyze", "summarize", "report"]),
            Agent("automation_001", "Auto Agent", "Executor",
                  ["script", "schedule", "monitor", "alert"]),
            Agent("security_001", "Guard Agent", "Security",
                  ["scan", "protect", "audit", "encrypt"]),
        ]
        
        for agent in agents_config:
            self.agents[agent.id] = agent
            print(f"🤖 Registered: {agent.name} ({agent.role})")
    
    async def connect_gateway(self):
        """Connect to Axzora Gateway"""
        print(f"🔗 Connecting to Gateway: {self.gateway_url}")
        
        try:
            self.websocket = await websockets.connect(self.gateway_url)
            print("✅ Connected to Axzora Gateway")
            
            # Register with gateway
            await self.websocket.send(json.dumps({
                "type": "register",
                "agent": "mr-happy-brain",
                "capabilities": list(self.agents.keys())
            }))
            
            return True
        except Exception as e:
            print(f"⚠️  Gateway connection failed: {e}")
            return False
    
    async def think(self, input_text: str) -> str:
        """Main thinking process"""
        print(f"🧠 Thinking about: {input_text[:50]}...")
        
        # Log to memory
        self.memory.append({
            "type": "input",
            "content": input_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Route to appropriate agent
        agent_id = self._route_task(input_text)
        agent = self.agents.get(agent_id)
        
        if agent:
            print(f"📡 Routing to {agent.name}")
            result = await self._execute_with_agent(agent, input_text)
        else:
            # Use local LLM
            result = await self._query_llm(input_text)
        
        # Store response
        self.memory.append({
            "type": "response",
            "content": result,
            "agent": agent_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Speak the response aloud
        _speak_async(result)
        
        return result
    
    def _route_task(self, task: str) -> str:
        """Intelligent task routing"""
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["code", "program", "debug", "git", "script"]):
            return "coder_001"
        elif any(kw in task_lower for kw in ["search", "research", "find", "analyze"]):
            return "research_001"
        elif any(kw in task_lower for kw in ["run", "execute", "schedule", "automate"]):
            return "automation_001"
        elif any(kw in task_lower for kw in ["security", "scan", "protect", "encrypt"]):
            return "security_001"
        else:
            return "mr_happy_001"
    
    async def _execute_with_agent(self, agent: Agent, task: str) -> str:
        """Execute task with specific agent"""
        agent.status = "working"
        
        # Simulate agent processing
        await asyncio.sleep(0.5)
        
        if agent.id == "coder_001":
            return await self._code_agent_task(task)
        elif agent.id == "research_001":
            return await self._research_agent_task(task)
        elif agent.id == "automation_001":
            return await self._automation_agent_task(task)
        else:
            return await self._query_llm(task)
    
    async def _code_agent_task(self, task: str) -> str:
        """Code generation agent"""
        prompt = f"You are an expert programmer. Task: {task}"
        return await self._query_llm(prompt)
    
    async def _research_agent_task(self, task: str) -> str:
        """Research agent"""
        prompt = f"You are a research analyst. Research and summarize: {task}"
        return await self._query_llm(prompt)
    
    async def _automation_agent_task(self, task: str) -> str:
        """Automation agent"""
        return f"🤖 Automation Agent: I'll create a script for '{task}'. Use /script command to generate."
    
    async def _query_llm(self, prompt: str) -> str:
        """Query local LLM via Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.2:3b",
                        "prompt": f"You are Mr Happy, Digital CEO of Axzora. {prompt}",
                        "stream": False
                    },
                    timeout=30.0
                )
                result = response.json()
                return result.get("response", "I'm processing your request...")
        except Exception as e:
            return f"Mr Happy here! I received: '{prompt[:50]}...' (LLM connection: {str(e)})"
    
    async def broadcast_to_swarm(self, message: str):
        """Broadcast to all agents"""
        print(f"📢 Broadcasting: {message}")
        
        tasks = []
        for agent in self.agents.values():
            if agent.status == "idle":
                tasks.append(self._notify_agent(agent, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _notify_agent(self, agent: Agent, message: str):
        """Notify specific agent"""
        print(f"  → Notifying {agent.name}")
        await asyncio.sleep(0.1)
    
    async def run_interactive(self):
        """Interactive mode"""
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║     MR HAPPY AI BRAIN - INTERACTIVE MODE                   ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
        print("Commands:")
        print("  /agents  - List all agents")
        print("  /memory  - Show recent memory")
        print("  /status  - System status")
        print("  /swarm   - Broadcast to all agents")
        print("  exit     - Quit\n")
        
        # Try to connect gateway
        await self.connect_gateway()
        
        self.running = True
        while self.running:
            try:
                user_input = input("\n🧠 Mr Happy > ").strip()
                
                if not user_input:
                    continue
                
                if user_input == "exit":
                    self.running = False
                    break
                elif user_input == "/agents":
                    self._show_agents()
                elif user_input == "/memory":
                    self._show_memory()
                elif user_input == "/status":
                    await self._show_status()
                elif user_input == "/swarm":
                    msg = input("Broadcast message: ")
                    await self.broadcast_to_swarm(msg)
                else:
                    response = await self.think(user_input)
                    print(f"\n🤖 {response}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_agents(self):
        """Display all agents"""
        print("\n🤖 AGENT SWARM:")
        for agent in self.agents.values():
            status_emoji = "🟢" if agent.status == "idle" else "🔵"
            print(f"  {status_emoji} {agent.name} ({agent.role})")
            print(f"     Skills: {', '.join(agent.skills)}")
    
    def _show_memory(self):
        """Show recent memory"""
        print("\n🧠 RECENT MEMORY:")
        for item in self.memory[-5:]:
            print(f"  [{item['type']}] {item['content'][:50]}...")
    
    async def _show_status(self):
        """Show system status"""
        print("\n📊 SYSTEM STATUS:")
        print(f"  Agents: {len(self.agents)}")
        print(f"  Memory entries: {len(self.memory)}")
        print(f"  Gateway: {'Connected' if self.websocket else 'Disconnected'}")


async def main():
    """Main entry point"""
    brain = MrHappyBrain()
    await brain.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
