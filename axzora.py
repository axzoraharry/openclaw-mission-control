#!/usr/bin/env python3
"""Axzora Mission Control - Unified CLI Controller."""

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent / "skills"))

from automation_workflows import WorkflowEngine, run_workflow


class AxzoraCLI:
    """Unified CLI for Axzora Mission Control."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = "openclaw_local_dev_token_very_secure_key_for_mission_control_2026"
    
    def status(self):
        """Show system status."""
        print("\n🚀 AXZORA MISSION CONTROL STATUS\n")
        
        services = [
            ("Backend API", 8000),
            ("Frontend", 3000),
            ("Gateway", 18789),
        ]
        
        for name, port in services:
            result = subprocess.run(
                ["powershell", "-Command", f"Test-NetConnection -ComputerName localhost -Port {port} -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"],
                capture_output=True,
                text=True
            )
            status = "✅ Running" if "True" in result.stdout else "❌ Stopped"
            print(f"  {name:20} {status}")
        
        print("\n📊 Quick Access:")
        print(f"  Mission Control: http://localhost:3000")
        print(f"  API Docs:        http://localhost:8000/docs")
        print(f"  Gateway:         ws://localhost:18789")
        print()
    
    def agents(self):
        """List all agents."""
        import httpx
        
        try:
            response = httpx.get(
                f"{self.base_url}/api/v1/agents",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            data = response.json()
            
            print("\n🤖 AGENTS\n")
            for agent in data.get("items", []):
                print(f"  {agent['name']}")
                print(f"    Role:   {agent.get('role', 'N/A')}")
                print(f"    Status: {agent.get('status', 'N/A')}")
                print()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def boards(self):
        """List all boards."""
        import httpx
        
        try:
            response = httpx.get(
                f"{self.base_url}/api/v1/boards",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            data = response.json()
            
            print("\n📋 BOARDS\n")
            for board in data.get("items", []):
                print(f"  {board['name']}")
                print(f"    ID:     {board['id']}")
                print(f"    Status: {board.get('status', 'N/A')}")
                print()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def skills(self):
        """List all skills."""
        skills_path = Path(__file__).parent / "skills" / "axzora_skills.json"
        
        try:
            with open(skills_path) as f:
                data = json.load(f)
            
            print("\n🛠️  SKILLS\n")
            for skill in data.get("skills", []):
                print(f"  {skill['name']}")
                print(f"    ID:       {skill['id']}")
                print(f"    Category: {skill.get('category', 'N/A')}")
                print(f"    Agent:    {skill.get('agent', 'N/A')}")
                print()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def launch(self, name: str, template: str = "fullstack"):
        """Launch a new SaaS MVP."""
        print(f"\n🚀 Launching {name} with template: {template}\n")
        
        skills_path = Path(__file__).parent / "skills" / "saas-mvp-launcher"
        result = subprocess.run(
            ["node", str(skills_path / "bin" / "saas-mvp-launcher.mjs"), 
             "create", name, "--template", template],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {name} launched successfully!")
            print(f"\nNext steps:")
            print(f"  cd {name}")
            if template == "fullstack":
                print(f"  docker-compose up -d")
        else:
            print(f"❌ Launch failed")
    
    def workflow(self, action: str, workflow_id: str = None, **kwargs):
        """Manage workflows."""
        if action == "list":
            engine = WorkflowEngine()
            print("\n📋 WORKFLOWS\n")
            for wf_id, workflow in engine.workflows.items():
                print(f"  {workflow['name']} ({wf_id})")
                print(f"    Steps: {len(workflow['steps'])}")
                print()
        
        elif action == "run" and workflow_id:
            result = asyncio.run(run_workflow(workflow_id, **kwargs))
            print(json.dumps(result, indent=2))
    
    def monitor(self):
        """Run system monitor."""
        import subprocess
        subprocess.run(["python", "skills/system_monitor.py"])
    
    def scheduler(self, action: str = "list"):
        """Manage task scheduler."""
        import subprocess
        if action == "start":
            subprocess.run(["python", "skills/task_scheduler.py", "start"])
        else:
            subprocess.run(["python", "skills/task_scheduler.py", "list"])


def main():
    parser = argparse.ArgumentParser(
        description="Axzora Mission Control CLI",
        prog="axzora"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Agents command
    subparsers.add_parser("agents", help="List all agents")
    
    # Boards command
    subparsers.add_parser("boards", help="List all boards")
    
    # Skills command
    subparsers.add_parser("skills", help="List all skills")
    
    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch a new SaaS MVP")
    launch_parser.add_argument("name", help="Project name")
    launch_parser.add_argument("--template", default="fullstack", 
                               choices=["fullstack", "nextjs", "fastapi"],
                               help="Template to use")
    
    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Manage workflows")
    workflow_parser.add_argument("action", choices=["list", "run"], help="Action")
    workflow_parser.add_argument("--id", help="Workflow ID (for run)")
    
    # Monitor command
    subparsers.add_parser("monitor", help="Run system health monitor")
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="Manage task scheduler")
    scheduler_parser.add_argument("action", nargs="?", default="list", 
                                  choices=["list", "start"], help="Action")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = AxzoraCLI()
    
    if args.command == "status":
        cli.status()
    elif args.command == "agents":
        cli.agents()
    elif args.command == "boards":
        cli.boards()
    elif args.command == "skills":
        cli.skills()
    elif args.command == "launch":
        cli.launch(args.name, args.template)
    elif args.command == "workflow":
        cli.workflow(args.action, args.id)
    elif args.command == "monitor":
        cli.monitor()
    elif args.command == "scheduler":
        cli.scheduler(args.action)


if __name__ == "__main__":
    main()
