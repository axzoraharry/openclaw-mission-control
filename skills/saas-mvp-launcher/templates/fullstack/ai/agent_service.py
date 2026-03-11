#!/usr/bin/env python3
"""Mr Happy AI Agent Service - FastAPI microservice for AI agents"""

import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

app = FastAPI(title="Mr Happy AI Agent", version="1.0.0")

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
MODEL = os.getenv("MODEL", "llama3.2:3b")


class ChatRequest(BaseModel):
    message: str
    context: Optional[List[Dict]] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: str


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mr-happy-agent",
        "model": MODEL,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Mr Happy AI Agent",
        "version": "1.0.0",
        "model": MODEL,
        "endpoints": ["/health", "/chat", "/skills"]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with Mr Happy AI"""
    prompt = request.message
    
    # Build context
    context_str = ""
    if request.context:
        for turn in request.context[-4:]:
            context_str += f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}\n"
    
    full_prompt = f"{context_str}User: {prompt}\nMr Happy:"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": f"You are Mr Happy, a helpful AI assistant. {full_prompt}",
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return ChatResponse(
                    response=result.get("response", "").strip(),
                    model=MODEL,
                    timestamp=datetime.now().isoformat()
                )
            else:
                raise HTTPException(status_code=500, detail="LLM error")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/skills")
async def list_skills():
    """List available AI skills"""
    return {
        "skills": [
            {"id": "chat", "name": "Chat", "description": "General conversation"},
            {"id": "code", "name": "Code Assistant", "description": "Help with coding tasks"},
            {"id": "analyze", "name": "Analyzer", "description": "Analyze data and text"},
            {"id": "summarize", "name": "Summarizer", "description": "Summarize content"},
        ]
    }


@app.post("/execute/{skill_id}")
async def execute_skill(skill_id: str, request: ChatRequest):
    """Execute a specific skill"""
    skill_prompts = {
        "code": "You are an expert programmer. Help with this coding task:",
        "analyze": "You are a data analyst. Analyze the following:",
        "summarize": "Summarize the following content concisely:",
    }
    
    prefix = skill_prompts.get(skill_id, "You are a helpful assistant.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": f"{prefix}\n\n{request.message}",
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"skill": skill_id, "result": result.get("response", "").strip()}
            else:
                raise HTTPException(status_code=500, detail="Skill execution failed")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
