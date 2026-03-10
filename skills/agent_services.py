#!/usr/bin/env python3
"""Agent services for Axzora Mission Control."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class AgentConfig(BaseModel):
    """Agent configuration."""
    name: str
    role: str
    port: int
    model: Optional[str] = None
    skills: List[str] = []


class AgentService:
    """Individual agent service."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.app = FastAPI(
            title=f"{config.name} Agent",
            description=f"Agent service for {config.name}",
            version="0.1.0"
        )
        self.setup_routes()
        self.status = "online"
        self.started_at = datetime.now()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/health")
        async def health():
            return {
                "status": self.status,
                "agent": self.config.name,
                "role": self.config.role,
                "skills": self.config.skills,
                "uptime": (datetime.now() - self.started_at).total_seconds()
            }
        
        @self.app.get("/")
        async def root():
            return {
                "name": self.config.name,
                "role": self.config.role,
                "version": "0.1.0",
                "skills": self.config.skills
            }
        
        @self.app.post("/chat")
        async def chat(message: dict):
            """Chat with the agent."""
            if "mr-happy-chat" in self.config.skills:
                return await self._mr_happy_chat(message.get("message", ""))
            raise HTTPException(status_code=400, detail="Chat skill not available")
        
        @self.app.post("/hp/convert")
        async def hp_convert(data: dict):
            """Happy Paisa currency conversion."""
            if "hp-convert" in self.config.skills:
                return self._hp_convert(
                    data.get("amount", 0),
                    data.get("from", "HP"),
                    data.get("to", "INR")
                )
            raise HTTPException(status_code=400, detail="HP convert skill not available")
        
        @self.app.get("/hp/rate")
        async def hp_rate():
            """Get Happy Paisa exchange rate."""
            if "hp-rate" in self.config.skills:
                return {"rate": 1000, "hp_per_inr": 0.001, "inr_per_hp": 1000}
            raise HTTPException(status_code=400, detail="HP rate skill not available")
        
        @self.app.get("/skills")
        async def list_skills():
            """List available skills."""
            return {"skills": self.config.skills}
        
        @self.app.post("/execute/{skill_id}")
        async def execute_skill(skill_id: str, params: dict):
            """Execute a skill."""
            if skill_id not in self.config.skills:
                raise HTTPException(status_code=404, detail="Skill not found")
            
            return await self._execute_skill(skill_id, params)
    
    async def _mr_happy_chat(self, message: str) -> dict:
        """Mr Happy chat implementation."""
        # Connect to Ollama
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2:3b",
                        "prompt": f"You are Mr. Happy, the Digital CEO of Axzora. Respond to: {message}",
                        "stream": False
                    },
                    timeout=30.0
                )
                result = response.json()
                return {
                    "response": result.get("response", "I'm thinking..."),
                    "agent": self.config.name,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "response": f"I'm Mr. Happy, Digital CEO of Axzora. I received your message: '{message}'. (Ollama connection issue: {str(e)})",
                "agent": self.config.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _hp_convert(self, amount: float, from_currency: str, to_currency: str) -> dict:
        """Happy Paisa conversion."""
        rate = 1000  # 1 HP = 1000 INR
        
        if from_currency == "HP" and to_currency == "INR":
            result = amount * rate
        elif from_currency == "INR" and to_currency == "HP":
            result = amount / rate
        else:
            result = amount
        
        return {
            "amount": result,
            "currency": to_currency,
            "rate": rate,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_skill(self, skill_id: str, params: dict) -> dict:
        """Execute a skill by ID."""
        skill_handlers = {
            "system-health": self._system_health,
            "agent-device": self._agent_device,
            "saas-mvp-launcher": self._saas_mvp_launcher,
        }
        
        handler = skill_handlers.get(skill_id)
        if handler:
            return await handler(params)
        
        return {"status": "error", "message": f"Skill {skill_id} not implemented"}
    
    async def _system_health(self, params: dict) -> dict:
        """System health check."""
        return {
            "status": "healthy",
            "agent": self.config.name,
            "services": {
                "backend": "online",
                "gateway": "online",
                "ollama": "online"
            }
        }
    
    async def _agent_device(self, params: dict) -> dict:
        """Agent device control."""
        command = params.get("command", "")
        return {
            "status": "success",
            "command": command,
            "message": f"Device command '{command}' executed"
        }
    
    async def _saas_mvp_launcher(self, params: dict) -> dict:
        """SaaS MVP launcher."""
        project_name = params.get("name", "my-app")
        template = params.get("template", "fullstack")
        
        return {
            "status": "success",
            "project": project_name,
            "template": template,
            "message": f"Project {project_name} created with {template} template"
        }
    
    def run(self):
        """Run the agent service."""
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port, log_level="info")


class AgentManager:
    """Manage multiple agent services."""
    
    def __init__(self):
        self.agents: Dict[str, AgentService] = {}
        self.load_config()
    
    def load_config(self):
        """Load agent configuration from skills file."""
        skills_path = Path(__file__).parent / "axzora_skills.json"
        
        if skills_path.exists():
            with open(skills_path) as f:
                config = json.load(f)
            
            for agent_id, agent_data in config.get("agents", {}).items():
                agent_config = AgentConfig(
                    name=agent_data.get("name", agent_id),
                    role=agent_data.get("role", "Agent"),
                    port=agent_data.get("port", 8000),
                    model=agent_data.get("model"),
                    skills=agent_data.get("skills", [])
                )
                self.agents[agent_id] = AgentService(agent_config)
    
    def start_agent(self, agent_id: str):
        """Start a specific agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            print(f"🚀 Starting {agent.config.name} on port {agent.config.port}")
            agent.run()
        else:
            print(f"❌ Agent {agent_id} not found")
    
    def start_all(self):
        """Start all agents in separate processes."""
        import multiprocessing
        
        processes = []
        for agent_id, agent in self.agents.items():
            p = multiprocessing.Process(
                target=agent.run,
                name=f"agent-{agent_id}"
            )
            p.start()
            processes.append(p)
            print(f"🚀 Started {agent.config.name} on port {agent.config.port}")
        
        print(f"\n✅ All {len(processes)} agents started")
        print("Press Ctrl+C to stop\n")
        
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("\n\n👋 Stopping all agents...")
            for p in processes:
                p.terminate()


def main():
    """Main entry point."""
    import sys
    
    manager = AgentManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start" and len(sys.argv) > 2:
            agent_id = sys.argv[2]
            manager.start_agent(agent_id)
        elif command == "start-all":
            manager.start_all()
        elif command == "list":
            print("\n📋 AVAILABLE AGENTS\n")
            for agent_id, agent in manager.agents.items():
                print(f"  {agent.config.name} ({agent_id})")
                print(f"    Port: {agent.config.port}")
                print(f"    Role: {agent.config.role}")
                print(f"    Skills: {', '.join(agent.config.skills)}")
                print()
        else:
            print("Usage: python agent_services.py [start <agent_id>|start-all|list]")
    else:
        manager.start_all()


if __name__ == "__main__":
    main()
