#!/usr/bin/env python3
"""System monitoring and health checks for Axzora Mission Control."""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import httpx


class SystemMonitor:
    """Monitor Axzora system health and performance."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = "openclaw_local_dev_token_very_secure_key_for_mission_control_2026"
        self.gateway_url = "ws://localhost:18789"
        self.checks = []
        self.alerts = []
    
    async def check_backend(self) -> Dict:
        """Check backend API health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/healthz",
                    timeout=5.0
                )
                return {
                    "service": "backend",
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "service": "backend",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_gateway(self) -> Dict:
        """Check gateway WebSocket connection."""
        try:
            import websockets
            start = time.time()
            async with websockets.connect(
                self.gateway_url
            ) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                elapsed = time.time() - start
                return {
                    "service": "gateway",
                    "status": "healthy",
                    "response_time": elapsed,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "service": "gateway",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_agents(self) -> Dict:
        """Check agent status."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/agents",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                data = response.json()
                agents = data.get("items", [])
                
                online = sum(1 for a in agents if a.get("status") == "online")
                provisioning = sum(1 for a in agents if a.get("status") == "provisioning")
                
                return {
                    "service": "agents",
                    "status": "healthy" if online > 0 else "degraded",
                    "total": len(agents),
                    "online": online,
                    "provisioning": provisioning,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "service": "agents",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_database(self) -> Dict:
        """Check database connectivity."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/boards",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                return {
                    "service": "database",
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "service": "database",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_all_checks(self) -> List[Dict]:
        """Run all health checks."""
        checks = [
            self.check_backend(),
            self.check_gateway(),
            self.check_agents(),
            self.check_database()
        ]
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        self.checks = [
            r if not isinstance(r, Exception) else {
                "service": "unknown",
                "status": "error",
                "error": str(r),
                "timestamp": datetime.now().isoformat()
            }
            for r in results
        ]
        
        return self.checks
    
    def generate_report(self) -> str:
        """Generate health report."""
        healthy = sum(1 for c in self.checks if c.get("status") == "healthy")
        total = len(self.checks)
        
        report = []
        report.append("\n" + "="*50)
        report.append("AXZORA SYSTEM HEALTH REPORT")
        report.append("="*50)
        report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overall: {healthy}/{total} services healthy")
        report.append("-"*50)
        
        for check in self.checks:
            status_emoji = "✅" if check.get("status") == "healthy" else "❌"
            report.append(f"\n{status_emoji} {check['service'].upper()}")
            report.append(f"   Status: {check.get('status', 'unknown')}")
            if 'response_time' in check:
                report.append(f"   Response: {check['response_time']:.3f}s")
            if 'total' in check:
                report.append(f"   Agents: {check.get('online', 0)}/{check['total']} online")
            if 'error' in check:
                report.append(f"   Error: {check['error']}")
        
        report.append("\n" + "="*50)
        return "\n".join(report)
    
    async def monitor_loop(self, interval: int = 60):
        """Continuous monitoring loop."""
        print("🔍 Starting system monitor...")
        print(f"   Check interval: {interval}s")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                await self.run_all_checks()
                print(self.generate_report())
                
                # Check for alerts
                unhealthy = [c for c in self.checks if c.get("status") != "healthy"]
                if unhealthy:
                    print(f"\n⚠️  {len(unhealthy)} service(s) unhealthy")
                
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped")


class MetricsCollector:
    """Collect and store system metrics."""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or Path.home() / ".axzora" / "metrics.json"
        self.metrics = []
    
    def record(self, metric_type: str, value: float, labels: Dict = None):
        """Record a metric."""
        self.metrics.append({
            "type": metric_type,
            "value": value,
            "labels": labels or {},
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
        
        self._save()
    
    def _save(self):
        """Save metrics to disk."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def get_stats(self, metric_type: str, hours: int = 24) -> Dict:
        """Get statistics for a metric type."""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        values = [
            m["value"] for m in self.metrics
            if m["type"] == metric_type and 
            datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff
        ]
        
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }


async def main():
    """Main entry point."""
    import sys
    
    monitor = SystemMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "loop":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        await monitor.monitor_loop(interval)
    else:
        # Single check
        await monitor.run_all_checks()
        print(monitor.generate_report())


if __name__ == "__main__":
    asyncio.run(main())
