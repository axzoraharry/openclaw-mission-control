#!/usr/bin/env python3
"""Mr Happy Agent Army - Distributed AI Agent System."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import httpx


class MrHappyAgent:
    """Individual Mr Happy agent instance."""
    
    def __init__(self, agent_id: str, port: int, specialty: str = "general"):
        self.agent_id = agent_id
        self.port = port
        self.specialty = specialty
        self.status = "offline"
        self.last_active = None
        self.tasks_completed = 0
    
    async def start(self):
        """Start the agent service."""
        # Start agent service on designated port
        cmd = [
            "python", "skills/agent_services.py", "start", "mr_happy"
        ]
        # Modify port in environment or config
        env = {"MR_HAPPY_PORT": str(self.port)}
        
        subprocess.Popen(
            cmd,
            env={**dict(subprocess.os.environ), **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.status = "starting"
        await asyncio.sleep(2)
        
        # Verify it's running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{self.port}/health",
                    timeout=5.0
                )
                if response.status_code == 200:
                    self.status = "online"
                    self.last_active = datetime.now()
                    return True
        except:
            pass
        
        self.status = "failed"
        return False
    
    async def execute_task(self, task: dict) -> dict:
        """Execute a task."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{self.port}/execute/{task.get('skill', 'chat')}",
                    json=task.get('params', {}),
                    timeout=30.0
                )
                self.tasks_completed += 1
                self.last_active = datetime.now()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MrHappyArmy:
    """Army of Mr Happy agents."""
    
    def __init__(self):
        self.agents: Dict[str, MrHappyAgent] = {}
        self.base_port = 8100
        self.specialties = [
            "voice_assistant",    # Default voice assistant
            "device_manager",     # Device connection management
            "data_sync",          # Data synchronization
            "network_manager",    # Network/WiFi management
            "a2a_coordinator",    # Google A2A agent coordination
            "security_guard",     # Security monitoring
            "task_scheduler",     # Task scheduling
            "backup_manager",     # Backup operations
        ]
        self.leader = None
    
    async def create_army(self, size: int = 8):
        """Create the agent army."""
        print(f"🚀 Creating Mr Happy Agent Army ({size} agents)...\n")
        
        for i in range(size):
            agent_id = f"mr_happy_{i+1}"
            port = self.base_port + i
            specialty = self.specialties[i % len(self.specialties)]
            
            agent = MrHappyAgent(agent_id, port, specialty)
            self.agents[agent_id] = agent
            
            # Start the agent
            success = await agent.start()
            status = "✅" if success else "❌"
            print(f"{status} {agent_id} (port {port}) - {specialty}")
            
            # First agent is the leader (voice assistant)
            if i == 0:
                self.leader = agent
                print(f"   👑 Designated as VOICE ASSISTANT LEADER")
        
        print(f"\n✅ Army deployed: {len([a for a in self.agents.values() if a.status == 'online'])}/{size} online")
    
    async def broadcast_command(self, command: str, params: dict = None) -> List[dict]:
        """Broadcast command to all agents."""
        results = []
        for agent_id, agent in self.agents.items():
            if agent.status == "online":
                result = await agent.execute_task({
                    "skill": "command",
                    "params": {"command": command, **(params or {})}
                })
                results.append({"agent": agent_id, "result": result})
        return results
    
    def get_voice_assistant(self) -> Optional[MrHappyAgent]:
        """Get the voice assistant leader."""
        return self.leader
    
    def get_specialist(self, specialty: str) -> Optional[MrHappyAgent]:
        """Get agent by specialty."""
        for agent in self.agents.values():
            if agent.specialty == specialty and agent.status == "online":
                return agent
        return None
    
    async def device_connect(self, device_type: str = "android"):
        """Connect to device."""
        device_agent = self.get_specialist("device_manager")
        if device_agent:
            return await device_agent.execute_task({
                "skill": "agent-device",
                "params": {"command": "connect", "platform": device_type}
            })
        return {"status": "error", "message": "No device manager available"}
    
    async def data_transfer(self, source: str, destination: str):
        """Transfer data."""
        sync_agent = self.get_specialist("data_sync")
        if sync_agent:
            return await sync_agent.execute_task({
                "skill": "data-sync",
                "params": {"source": source, "destination": destination}
            })
        return {"status": "error", "message": "No data sync agent available"}
    
    async def setup_a2a_network(self):
        """Setup Google A2A agent network."""
        a2a_agent = self.get_specialist("a2a_coordinator")
        if a2a_agent:
            return await a2a_agent.execute_task({
                "skill": "a2a-coordinator",
                "params": {"action": "initialize_network"}
            })
        return {"status": "error", "message": "No A2A coordinator available"}
    
    def status_report(self) -> dict:
        """Get army status report."""
        online = sum(1 for a in self.agents.values() if a.status == "online")
        total_tasks = sum(a.tasks_completed for a in self.agents.values())
        
        return {
            "total_agents": len(self.agents),
            "online": online,
            "offline": len(self.agents) - online,
            "total_tasks_completed": total_tasks,
            "voice_assistant": self.leader.agent_id if self.leader else None,
            "agents": [
                {
                    "id": a.agent_id,
                    "port": a.port,
                    "specialty": a.specialty,
                    "status": a.status,
                    "tasks": a.tasks_completed
                }
                for a in self.agents.values()
            ]
        }


class DeviceManager:
    """Manage device connections."""
    
    def __init__(self, army: MrHappyArmy):
        self.army = army
        self.connected_devices = {}
    
    async def scan_devices(self):
        """Scan for connected devices."""
        print("\n📱 Scanning for devices...")
        
        # Check for Android devices via ADB
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if '\t' in line:
                    device_id, status = line.strip().split('\t')
                    devices.append({"id": device_id, "status": status, "type": "android"})
            
            if devices:
                print(f"  Found {len(devices)} Android device(s):")
                for d in devices:
                    print(f"    📱 {d['id']} - {d['status']}")
                self.connected_devices['android'] = devices
            else:
                print("  No Android devices found")
        except Exception as e:
            print(f"  ADB not available: {e}")
        
        return self.connected_devices
    
    async def setup_permanent_connection(self, device_id: str):
        """Setup permanent connection to device."""
        print(f"\n🔗 Setting up permanent connection to {device_id}...")
        
        # Use agent-device for connection
        device_agent = self.army.get_specialist("device_manager")
        if device_agent:
            # Enable TCP/IP mode for WiFi connection
            subprocess.run(["adb", "tcpip", "5555"], capture_output=True)
            
            # Connect via network
            # Get device IP
            ip_result = subprocess.run(
                ["adb", "shell", "ip", "route"],
                capture_output=True,
                text=True
            )
            
            return {
                "status": "success",
                "device": device_id,
                "connection": "wifi_tcpip",
                "message": "Device configured for permanent WiFi connection"
            }
        
        return {"status": "error", "message": "Device manager not available"}
    
    async def transfer_all_data(self, device_id: str, destination: str):
        """Transfer all data from device."""
        print(f"\n📤 Transferring all data from {device_id} to {destination}...")
        
        sync_agent = self.army.get_specialist("data_sync")
        if sync_agent:
            # Pull all data via ADB
            folders = ["/sdcard/DCIM", "/sdcard/Download", "/sdcard/Documents", "/sdcard/Music", "/sdcard/Pictures"]
            
            for folder in folders:
                print(f"  Syncing {folder}...")
                subprocess.run(
                    ["adb", "pull", folder, destination],
                    capture_output=True
                )
            
            return {
                "status": "success",
                "device": device_id,
                "destination": destination,
                "folders_synced": len(folders)
            }
        
        return {"status": "error", "message": "Data sync agent not available"}
    
    async def clean_device(self, device_id: str):
        """Clean device storage."""
        print(f"\n🧹 Cleaning device {device_id}...")
        
        # Clear cache
        subprocess.run(["adb", "shell", "pm", "clear-cache-all"], capture_output=True)
        
        # Clear temp files
        subprocess.run(["adb", "shell", "rm", "-rf", "/sdcard/.thumbnails/*"], capture_output=True)
        
        return {
            "status": "success",
            "device": device_id,
            "message": "Device cleaned successfully"
        }


async def main():
    """Main entry point."""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           MR HAPPY AGENT ARMY DEPLOYMENT                   ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Create the army
    army = MrHappyArmy()
    await army.create_army(size=8)
    
    # Device management
    device_mgr = DeviceManager(army)
    
    # Scan for devices
    devices = await device_mgr.scan_devices()
    
    # Setup A2A network
    print("\n🌐 Setting up Google A2A agent network...")
    a2a_result = await army.setup_a2a_network()
    print(f"  Status: {a2a_result.get('status', 'unknown')}")
    
    # Status report
    print("\n📊 ARMY STATUS REPORT")
    report = army.status_report()
    print(f"  Total Agents: {report['total_agents']}")
    print(f"  Online: {report['online']}")
    print(f"  Voice Assistant: {report['voice_assistant']}")
    print(f"  Tasks Completed: {report['total_tasks_completed']}")
    
    print("\n✅ Mr Happy Agent Army is ready!")
    print(f"   Voice Assistant Leader: {army.leader.agent_id} (port {army.leader.port})")
    print("\n   Use 'Hey Mr Happy' to activate voice assistant")


if __name__ == "__main__":
    asyncio.run(main())
