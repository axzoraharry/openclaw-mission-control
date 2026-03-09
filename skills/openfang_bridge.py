#!/usr/bin/env python3
"""
OpenFang API Bridge - Connects Axzora Dashboard to Mission Control
Serves the dashboard HTML and provides API endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import httpx
import json

# ============ CONFIGURATION ============

MISSION_CONTROL_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
WHATSAPP_BRIDGE_URL = "http://localhost:8001"
HP_RATE = 1000# 1 HP =₹1000

app = FastAPI(title="OpenFang API Bridge", version="0.1.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELS ============

class ChatMessage(BaseModel):
    message: str

class Agent(BaseModel):
    id: str
    name: str
    description: str
    model_provider: str = "groq"
    model_name: str = "llama-3.3-70b-versatile"
    session_count: int = 0

# ============ SATYUG AGENTS ============

SATYUG_AGENTS = [
    {
        "id": "mr-happy",
        "name": "mr-happy",
        "description": "Primary AI orchestrator for Axzora. Manages all operations and coordinates between agents. Your Digital CEO.",
        "model_provider": "ollama",
        "model_name": "llama3.2:3b",
        "session_count": 42
    },
    {
        "id": "lucy",
        "name": "lucy",
        "description": "Research AI specializing in intelligence gathering and analysis. Perfect for market research and competitive analysis.",
        "model_provider": "ollama",
        "model_name": "llama3.2:3b",
        "session_count": 28
    },
    {
        "id": "tansi",
        "name": "tansi",
        "description": "Operations AI managing the Happy Paisa economy. Handles HP conversions, transactions, and financial operations.",
        "model_provider": "ollama",
        "model_name": "llama3.2:3b",
        "session_count": 35
    },
    {
        "id": "kyra",
        "name": "kyra",
        "description": "Analytics AI with vision and code capabilities. Handles data analysis, reporting, and visual tasks.",
        "model_provider": "ollama",
        "model_name": "llama3.2:3b",
        "session_count": 19
    }
]

# ============ HEALTH ENDPOINTS ============

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
async def status():
    """System status"""
    return {
        "default_provider": "ollama",
        "default_model": "llama3.2:3b",
        "hp_rate": HP_RATE,
        "agents_count": len(SATYUG_AGENTS)
    }

# ============ AGENTS API ============

@app.get("/api/agents")
async def list_agents():
    """List all Satyug agents"""
    return SATYUG_AGENTS

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get single agent by ID"""
    for agent in SATYUG_AGENTS:
        if agent["id"] == agent_id:
            return agent
    raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/api/agents/{agent_id}/message")
async def send_message(agent_id: str, msg: ChatMessage):
    """Send message to an agent via Ollama"""
    agent = None
    for a in SATYUG_AGENTS:
        if a["id"] == agent_id:
            agent = a
            break
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Build system prompt based on agent
    system_prompts = {
        "mr-happy": "You are Mr. Happy, the Digital CEO of Axzora. You are professional, concise, and focused on business operations. Respond briefly and helpfully.",
        "lucy": "You are Lucy, the Research AI for Axzora. You specialize in gathering intelligence and analyzing data. Be thorough but concise.",
        "tansi": "You are Tansi, the Operations AI managing Happy Paisa economy. 1 HP =₹1000 INR. Help with financial operations and conversions.",
        "kyra": "You are Kyra, the Analytics AI with vision and code capabilities. You analyze data and provide insights. Be precise and data-driven."
    }
    
    system_prompt = system_prompts.get(agent_id, "You are an Axzora AI agent. Be helpful and concise.")
    
    # Call Ollama
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": f"{system_prompt}\n\nUser: {msg.message}\nAssistant:",
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"response": result.get("response", "I'm processing your request.")}
            else:
                return {"response": f"Ollama returned status {response.status_code}"}
                
    except Exception as e:
        return {"response": f"I'm here to help! (Note: Ollama connection pending - {str(e)})"}

# ============ HAPPY PAISA API ============

@app.get("/api/hp/rate")
async def get_hp_rate():
    """Get current HP rate"""
    return {
        "rate": HP_RATE,
        "currency": "HP",
        "base": "INR",
        "updated": datetime.utcnow().isoformat()
    }

@app.post("/api/hp/convert")
async def convert_hp(amount: float, from_currency: str = "HP", to_currency: str = "INR"):
    """Convert between HP and INR"""
    if from_currency.upper() == "HP" and to_currency.upper() == "INR":
        result = amount * HP_RATE
        return {
            "from": {"amount": amount, "currency": "HP"},
            "to": {"amount": result, "currency": "INR"},
            "rate": HP_RATE
        }
    elif from_currency.upper() == "INR" and to_currency.upper() == "HP":
        result = amount / HP_RATE
        return {
            "from": {"amount": amount, "currency": "INR"},
            "to": {"amount": result, "currency": "HP"},
            "rate": HP_RATE
        }
    return {"error": "Invalid conversion pair"}

# ============ DASHBOARD HTML ============

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the Axzora Dashboard HTML"""
    html_path = "c:/Users/harry/Downloads/openclaw-main/openclaw-mission-control/frontend/public/axzora-dashboard.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
        <head><title>Axzora Dashboard</title></head>
        <body style="background:#080706;color:#fff;font-family:system-ui">
        <h1>⚠ Dashboard HTML not found</h1>
        <p>Please ensure the axzora-dashboard.html file exists.</p>
        <p>API is running at: <a href="/api/health" style="color:#FF5C00">/api/health</a></p>
        </body>
        </html>
        """

# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    print("🔥 OpenFang API Bridge")
    print("=" * 40)
    print(f"Dashboard: http://localhost:50051")
    print(f"Health: http://localhost:50051/api/health")
    print(f"Agents: http://localhost:50051/api/agents")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=50051)
