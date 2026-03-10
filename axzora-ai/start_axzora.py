#!/usr/bin/env python3
"""Axzora AI System Launcher - Start the entire infrastructure"""

import asyncio
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


class AxzoraLauncher:
    """Launch and manage the Axzora AI system"""
    
    def __init__(self):
        self.processes = []
        self.services = {
            'backend':  {'port': 8000,  'name': 'Mission Control Backend'},
            'mr_happy': {'port': 8001,  'name': 'Mr Happy Agent'},
            'frontend': {'port': 3000,  'name': 'Mission Control UI'},
            'gateway':  {'port': 18789, 'name': 'OpenClaw Gateway'},
            'voice_ws': {'port': 8765,  'name': 'Mr Happy Voice Server'},
        }
    
    def print_banner(self):
        """Print startup banner"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           ⚡ AXZORA AI INFRASTRUCTURE LAUNCHER ⚡                 ║
║                                                                  ║
║     Mr Happy AI + OpenClaw Gateway + Mission Control             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    async def start_backend(self):
        """Start FastAPI backend"""
        print("🚀 Starting Mission Control Backend...")
        
        proc = subprocess.Popen(
            ['uv', 'run', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'],
            cwd='backend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(('backend', proc))
        
        await asyncio.sleep(5)
        print("  ✅ Backend running on http://localhost:8000")
    
    async def start_mr_happy(self):
        """Start Mr Happy agent"""
        print("🤖 Starting Mr Happy AI Agent...")
        
        proc = subprocess.Popen(
            ['python', 'skills/agent_services.py', 'start', 'mr_happy'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(('mr_happy', proc))
        
        await asyncio.sleep(3)
        print("  ✅ Mr Happy running on http://localhost:8001")
    
    async def start_frontend(self):
        """Start Next.js frontend"""
        print("🎨 Starting Mission Control Dashboard...")
        
        # Use cmd.exe wrapper for Windows npm compatibility
        proc = subprocess.Popen(
            ['cmd.exe', '/c', 'cd', 'frontend', '&&', 'npm', 'run', 'dev'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        self.processes.append(('frontend', proc))
        
        await asyncio.sleep(10)
        print("  ✅ Dashboard running on http://localhost:3000")
    
    async def start_voice_server(self):
        """Start Mr Happy Voice WebSocket server"""
        print("🎙️  Starting Mr Happy Voice Server...")

        proc = subprocess.Popen(
            [sys.executable,
             str(Path(__file__).parent / 'mr-happy' / 'voice_integrated.py'),
             '--ws'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(('voice_ws', proc))

        await asyncio.sleep(3)
        print("  ✅ Voice server on ws://localhost:8765")

    async def start_gateway(self):
        """Start OpenClaw Gateway"""
        print("🔗 Starting OpenClaw Gateway...")
        
        # Use existing gateway or start new one
        proc = subprocess.Popen(
            ['openclaw', 'gateway', '--port', '18789'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(('gateway', proc))
        
        await asyncio.sleep(3)
        print("  ✅ Gateway running on ws://localhost:18789")
    
    def open_dashboard(self):
        """Open the dashboard in browser"""
        print("\n🌐 Opening Axzora Dashboard...")
        
        # Open custom dashboard
        dashboard_path = Path(__file__).parent / 'mission-control' / 'dashboard.html'
        webbrowser.open(f'file://{dashboard_path.absolute()}')
        
        # Also open Mission Control UI
        webbrowser.open('http://localhost:3000')
    
    def print_status(self):
        """Print system status"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    ✅ SYSTEM READY                                ║
╠══════════════════════════════════════════════════════════════════╣
║  Service                    │ URL                                ║
╠═════════════════════════════╪════════════════════════════════════╣
║  🎨 Mission Control UI      │ http://localhost:3000              ║
║  🔧 Backend API             │ http://localhost:8000/docs         ║
║  🤖 Mr Happy Agent          │ http://localhost:8001/chat         ║
║  🔗 OpenClaw Gateway        │ ws://localhost:18789               ║
║  🎙️  Mr Happy Voice WS       │ ws://localhost:8765                ║
║  📊 Custom Dashboard        │ axzora-ai/mission-control/         ║
╚══════════════════════════════════════════════════════════════════╝

🎙️  INTERACTIVE MODE:
   python axzora-ai/mr-happy/brain.py              - AI Brain (CLI)
   python axzora-ai/mr-happy/voice_integrated.py   - Voice Assistant (text)
   python axzora-ai/mr-happy/voice_integrated.py --ws   - Voice WebSocket
   python axzora-ai/mr-happy/wake_word.py          - Wake Word Listener
   python axzora-ai/mr-happy/autonomous_agent.py   - AutoGPT Agent

⚡ QUICK COMMANDS:
   /agents  - List all agents
   /status  - System status
   /sync    - Sync device
   /help    - Show help

Press Ctrl+C to stop all services
        """)
    
    async def run(self):
        """Run the complete system"""
        self.print_banner()
        
        try:
            # Start all services
            await self.start_backend()
            await self.start_mr_happy()
            await self.start_voice_server()
            await self.start_frontend()
            # await self.start_gateway()  # Gateway usually already running
            
            # Open dashboard
            self.open_dashboard()
            
            # Print status
            self.print_status()
            
            # Keep running
            print("\n⏳ Services running... Press Ctrl+C to stop\n")
            
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping Axzora AI System...")
            self.stop_all()
    
    def stop_all(self):
        """Stop all services"""
        print("\n🛑 Stopping all services...")
        
        for name, proc in self.processes:
            try:
                proc.terminate()
                print(f"  ✅ Stopped {name}")
            except:
                pass
        
        print("\n✅ All services stopped. Goodbye!")


def main():
    """Main entry point"""
    launcher = AxzoraLauncher()
    
    try:
        asyncio.run(launcher.run())
    except Exception as e:
        print(f"❌ Error: {e}")
        launcher.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
