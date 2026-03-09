"""
AXZORA Super Agents API Bridge
==============================

FastAPI bridge that exposes Super Agents to the OpenFang dashboard.
Provides REST API for agent interaction, workflows, and automation.

Author: Mr. Happy AI (Digital CEO of Axzora)
"""

import os
import sys
import json
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import super agents
try:
    from super_agents import (
        SuperAgent, MrHappyAgent, LucyAgent, TansiAgent, KyraAgent,
        AgentOrchestrator, AgentState
    )
    from automation_workflows import WorkflowEngine, Workflow, WorkflowStep, TriggerType
    SUPER_AGENTS_AVAILABLE = True
except ImportError:
    SUPER_AGENTS_AVAILABLE = False
    print("Warning: Super Agents not available. Running in basic mode.")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    agent: str = "mr_happy"
    context: Optional[Dict] = None

class TaskRequest(BaseModel):
    agent: str
    description: str
    priority: int = 1

class WorkflowRequest(BaseModel):
    workflow_id: str
    context: Optional[Dict] = None

class CodeRequest(BaseModel):
    instruction: str
    language: str = "python"
    save_to: Optional[str] = None

class ExecuteRequest(BaseModel):
    command: str
    timeout: int = 60

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="AXZORA Super Agents API",
    description="Autonomous AI Agent System for AXZORA Digital Corporation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

orchestrator: Optional[Any] = None
workflow_engine: Optional[Any] = None

def initialize_agents():
    """Initialize agent orchestrator and workflow engine"""
    global orchestrator, workflow_engine
    
    if not SUPER_AGENTS_AVAILABLE:
        return
    
    workspace = os.path.join(os.path.dirname(__file__), "workspace")
    os.makedirs(workspace, exist_ok=True)
    
    orchestrator = AgentOrchestrator(workspace=workspace)
    workflow_engine = WorkflowEngine()
    
    print("🤖 Super Agents initialized:")
    for name in orchestrator.agents.keys():
        print(f"   - {name}")

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    initialize_agents()
    
    # Start workflow scheduler
    if workflow_engine:
        workflow_engine.start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    if workflow_engine:
        workflow_engine.stop_scheduler()

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "super_agents": SUPER_AGENTS_AVAILABLE,
        "agents_initialized": orchestrator is not None,
        "workflows_initialized": workflow_engine is not None
    }

@app.get("/api/status")
async def system_status():
    """Full system status"""
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "super_agents": {
            "available": SUPER_AGENTS_AVAILABLE,
            "agents": {}
        },
        "workflows": {
            "available": workflow_engine is not None,
            "count": 0,
            "scheduled": 0
        },
        "services": {
            "ollama": await check_service("http://localhost:11434/api/tags"),
            "mission_control": await check_service("http://localhost:8000/healthz"),
            "dashboard": await check_service("http://localhost:50051/api/health")
        }
    }
    
    if orchestrator:
        status["super_agents"]["agents"] = orchestrator.get_status()
    
    if workflow_engine:
        workflows = workflow_engine.list_workflows()
        status["workflows"]["count"] = len(workflows)
        status["workflows"]["scheduled"] = len([w for w in workflows if w["trigger"] == "schedule"])
    
    return status

async def check_service(url: str) -> Dict:
    """Check if a service is healthy"""
    import requests
    try:
        response = requests.get(url, timeout=5)
        return {"status": "ok" if response.status_code == 200 else "error", "code": response.status_code}
    except:
        return {"status": "offline"}

# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@app.get("/api/agents")
async def list_agents():
    """List all available agents"""
    if not orchestrator:
        return {"agents": [], "error": "Agents not initialized"}
    
    agents = []
    for name, agent in orchestrator.agents.items():
        agents.append({
            "name": agent.name,
            "role": agent.role,
            "state": agent.state.value,
            "model": agent.model,
            "tools": list(agent.skills.keys()),
            "pending_tasks": agent.task_queue.qsize()
        })
    
    return {"agents": agents}

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """Chat with a specific agent"""
    if not orchestrator:
        # Fallback to direct Ollama call
        return await chat_fallback(request.message)
    
    if request.agent not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent}")
    
    agent = orchestrator.agents[request.agent]
    
    try:
        response = agent.chat(request.message)
        return {
            "agent": request.agent,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def chat_fallback(message: str) -> Dict:
    """Fallback chat using direct Ollama API"""
    import requests
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [
                    {"role": "system", "content": "You are Mr. Happy, the Digital CEO of AXZORA."},
                    {"role": "user", "content": message}
                ],
                "stream": False
            },
            timeout=120
        )
        
        if response.status_code == 200:
            return {
                "agent": "mr_happy",
                "response": response.json().get("message", {}).get("content", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Ollama error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/task")
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Create a new task for an agent"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    if request.agent not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent}")
    
    task = orchestrator.assign_task(request.agent, request.description, request.priority)
    
    # Run agent in background
    background_tasks.add_task(run_agent_task, request.agent)
    
    return {
        "task_id": task.id,
        "agent": request.agent,
        "description": request.description,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat()
    }

def run_agent_task(agent_name: str):
    """Run agent task in background"""
    if orchestrator:
        agent = orchestrator.agents[agent_name]
        agent.run_autonomous(max_iterations=1)

@app.get("/api/tasks/{agent_name}")
async def get_agent_tasks(agent_name: str):
    """Get tasks for a specific agent"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")
    
    agent = orchestrator.agents[agent_name]
    
    return {
        "agent": agent_name,
        "current_task": agent.current_task.description if agent.current_task else None,
        "history": agent.history[-10:]  # Last 10 tasks
    }

# ============================================================================
# CODE GENERATION
# ============================================================================

@app.post("/api/code")
async def generate_code(request: CodeRequest):
    """Generate code using AI"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    agent = orchestrator.agents.get("mr_happy")
    if not agent:
        raise HTTPException(status_code=500, detail="Mr. Happy agent not available")
    
    try:
        code = agent._tool_code(request.instruction, request.language, request.save_to)
        return {
            "code": code,
            "language": request.language,
            "saved_to": request.save_to,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# COMMAND EXECUTION
# ============================================================================

@app.post("/api/execute")
async def execute_command(request: ExecuteRequest):
    """Execute a system command"""
    import subprocess
    
    try:
        result = subprocess.run(
            request.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=request.timeout
        )
        
        return {
            "command": request.command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.utcnow().isoformat()
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.get("/api/workflows")
async def list_workflows():
    """List all workflows"""
    if not workflow_engine:
        return {"workflows": [], "error": "Workflows not initialized"}
    
    return {"workflows": workflow_engine.list_workflows()}

@app.post("/api/workflows/run")
async def run_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Run a workflow"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="Workflows not initialized")
    
    workflow = workflow_engine.get_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {request.workflow_id}")
    
    # Run in background
    background_tasks.add_task(
        workflow_engine.run_workflow,
        request.workflow_id,
        request.context
    )
    
    return {
        "workflow_id": request.workflow_id,
        "status": "started",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/workflows/{workflow_id}/history")
async def workflow_history(workflow_id: str):
    """Get execution history for a workflow"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="Workflows not initialized")
    
    history = [
        h for h in workflow_engine.execution_history
        if h["workflow_id"] == workflow_id
    ]
    
    return {"workflow_id": workflow_id, "history": history[-20:]}

# ============================================================================
# HAPPY PAISA ENDPOINTS
# ============================================================================

@app.get("/api/hp/rate")
async def get_hp_rate():
    """Get current Happy Paisa rate"""
    return {
        "rate": 1000,
        "currency": "INR",
        "description": "1 HP = ₹1,000 INR",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/hp/convert")
async def convert_hp(amount: float, from_currency: str, to_currency: str):
    """Convert between Happy Paisa and INR"""
    rate = 1000
    
    if from_currency == "HP" and to_currency == "INR":
        result = amount * rate
    elif from_currency == "INR" and to_currency == "HP":
        result = amount / rate
    else:
        raise HTTPException(status_code=400, detail="Invalid conversion")
    
    return {
        "original_amount": amount,
        "original_currency": from_currency,
        "converted_amount": result,
        "converted_currency": to_currency,
        "rate": rate,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# SKILLS ENDPOINTS
# ============================================================================

@app.get("/api/skills")
async def list_skills():
    """List all available skills"""
    skills_file = os.path.join(os.path.dirname(__file__), "axzora_skills.json")
    
    if os.path.exists(skills_file):
        with open(skills_file, 'r') as f:
            data = json.load(f)
            return data
    
    return {"skills": [], "agents": {}, "configuration": {}}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 AXZORA SUPER AGENTS API 🚀                         ║
║                                                              ║
║     Autonomous AI Agent System                               ║
║                                                              ║
║     Dashboard: http://localhost:50052                        ║
║     API Docs: http://localhost:50052/docs                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=50052)
