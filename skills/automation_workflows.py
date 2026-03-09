"""Automation workflows for Axzora Mission Control."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class WorkflowEngine:
    """Execute automated workflows across the Axzora ecosystem."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path.home() / ".axzora" / "workflows.json"
        self.workflows = self._load_workflows()
    
    def _load_workflows(self) -> dict:
        """Load workflow definitions."""
        if Path(self.config_path).exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {}
    
    def _save_workflows(self):
        """Save workflow definitions."""
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.workflows, f, indent=2)
    
    def create_workflow(self, name: str, steps: list[dict]) -> str:
        """Create a new workflow."""
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.workflows[workflow_id] = {
            "name": name,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._save_workflows()
        return workflow_id
    
    async def execute_step(self, step: dict) -> dict:
        """Execute a single workflow step."""
        step_type = step.get("type")
        
        if step_type == "cli":
            return await self._execute_cli(step)
        elif step_type == "api":
            return await self._execute_api(step)
        elif step_type == "agent":
            return await self._execute_agent(step)
        elif step_type == "delay":
            await asyncio.sleep(step.get("seconds", 1))
            return {"status": "success", "type": "delay"}
        else:
            return {"status": "error", "message": f"Unknown step type: {step_type}"}
    
    async def _execute_cli(self, step: dict) -> dict:
        """Execute CLI command."""
        command = step.get("command")
        cwd = step.get("cwd")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=step.get("timeout", 60)
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _execute_api(self, step: dict) -> dict:
        """Execute API call."""
        import httpx
        
        method = step.get("method", "GET")
        url = step.get("url")
        headers = step.get("headers", {})
        data = step.get("data")
        
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                else:
                    return {"status": "error", "message": f"Unsupported method: {method}"}
                
                return {
                    "status": "success" if response.status_code < 400 else "error",
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _execute_agent(self, step: dict) -> dict:
        """Execute agent task."""
        agent_id = step.get("agent_id")
        task = step.get("task")
        
        # This would integrate with Mission Control agents
        return {
            "status": "success",
            "agent_id": agent_id,
            "task": task,
            "message": f"Task assigned to agent {agent_id}"
        }
    
    async def run_workflow(self, workflow_id: str, context: dict = None) -> dict:
        """Run a complete workflow."""
        if workflow_id not in self.workflows:
            return {"status": "error", "message": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        results = []
        context = context or {}
        
        print(f"🚀 Running workflow: {workflow['name']}")
        
        for i, step in enumerate(workflow["steps"]):
            print(f"  Step {i+1}/{len(workflow['steps'])}: {step.get('name', step.get('type'))}")
            
            # Replace context variables
            step = self._replace_context(step, context)
            
            result = await self.execute_step(step)
            results.append(result)
            
            if result["status"] == "error" and not step.get("continue_on_error"):
                print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")
                return {
                    "status": "error",
                    "step": i + 1,
                    "results": results
                }
            
            print(f"  ✅ Success")
            
            # Update context with result
            if step.get("save_to_context"):
                context[step["save_to_context"]] = result
        
        print(f"✅ Workflow completed: {workflow['name']}")
        return {
            "status": "success",
            "results": results,
            "context": context
        }
    
    def _replace_context(self, step: dict, context: dict) -> dict:
        """Replace context variables in step."""
        import copy
        step = copy.deepcopy(step)
        
        def replace_in_value(value):
            if isinstance(value, str):
                for key, val in context.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(val))
                return value
            elif isinstance(value, dict):
                return {k: replace_in_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_in_value(v) for v in value]
            return value
        
        return replace_in_value(step)


# Predefined workflows
WORKFLOWS = {
    "deploy_fullstack": {
        "name": "Deploy Full-Stack SaaS",
        "steps": [
            {
                "name": "Create project",
                "type": "cli",
                "command": "saas-mvp-launcher create {{project_name}} --template fullstack --auth {{auth}}",
                "cwd": "{{base_path}}"
            },
            {
                "name": "Start database",
                "type": "cli",
                "command": "docker-compose up -d db",
                "cwd": "{{base_path}}/{{project_name}}",
                "timeout": 120
            },
            {
                "name": "Wait for database",
                "type": "delay",
                "seconds": 5
            },
            {
                "name": "Health check",
                "type": "api",
                "method": "GET",
                "url": "http://localhost:8000/healthz",
                "continue_on_error": True
            }
        ]
    },
    "create_agent_task": {
        "name": "Create and Assign Agent Task",
        "steps": [
            {
                "name": "Create task",
                "type": "api",
                "method": "POST",
                "url": "http://localhost:8000/api/v1/boards/{{board_id}}/tasks",
                "headers": {
                    "Authorization": "Bearer {{token}}",
                    "Content-Type": "application/json"
                },
                "data": {
                    "title": "{{task_title}}",
                    "description": "{{task_description}}",
                    "status": "inbox",
                    "priority": "high",
                    "assigned_agent_id": "{{agent_id}}"
                },
                "save_to_context": "task_result"
            },
            {
                "name": "Notify agent",
                "type": "agent",
                "agent_id": "{{agent_id}}",
                "task": "New task assigned: {{task_title}}"
            }
        ]
    },
    "mobile_automation": {
        "name": "Mobile Device Automation",
        "steps": [
            {
                "name": "Open app",
                "type": "cli",
                "command": "agent-device open {{app_name}} --platform {{platform}}"
            },
            {
                "name": "Take screenshot",
                "type": "cli",
                "command": "agent-device screenshot --out {{screenshot_path}}"
            },
            {
                "name": "Get UI snapshot",
                "type": "cli",
                "command": "agent-device snapshot -i > {{snapshot_path}}"
            },
            {
                "name": "Close session",
                "type": "cli",
                "command": "agent-device close"
            }
        ]
    }
}


def init_workflows():
    """Initialize default workflows."""
    engine = WorkflowEngine()
    
    for workflow_id, workflow in WORKFLOWS.items():
        if workflow_id not in engine.workflows:
            engine.workflows[workflow_id] = workflow
    
    engine._save_workflows()
    print("✅ Workflows initialized")


async def run_workflow(workflow_id: str, **context):
    """Run a workflow with context."""
    engine = WorkflowEngine()
    return await engine.run_workflow(workflow_id, context)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python automation_workflows.py <command>")
        print("Commands: init, run <workflow_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_workflows()
    elif command == "run" and len(sys.argv) >= 3:
        workflow_id = sys.argv[2]
        result = asyncio.run(run_workflow(workflow_id))
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {command}")
