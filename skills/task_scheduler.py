#!/usr/bin/env python3
"""Automated task scheduler for Axzora Mission Control."""

import asyncio
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List
import threading


class ScheduledTask:
    """Represents a scheduled task."""
    
    def __init__(self, name: str, schedule: str, action: Callable, **kwargs):
        self.name = name
        self.schedule = schedule  # "interval:60" or "daily:14:00"
        self.action = action
        self.kwargs = kwargs
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.enabled = True
        
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate next run time based on schedule."""
        if self.schedule.startswith("interval:"):
            seconds = int(self.schedule.split(":")[1])
            self.next_run = datetime.now() + timedelta(seconds=seconds)
        elif self.schedule.startswith("daily:"):
            time_str = self.schedule.split(":", 1)[1]
            hour, minute = map(int, time_str.split(":"))
            next_run = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= datetime.now():
                next_run += timedelta(days=1)
            self.next_run = next_run
    
    def should_run(self) -> bool:
        """Check if task should run now."""
        return self.enabled and self.next_run and datetime.now() >= self.next_run
    
    async def run(self):
        """Execute the task."""
        if not self.enabled:
            return
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {self.name}")
        
        try:
            if asyncio.iscoroutinefunction(self.action):
                await self.action(**self.kwargs)
            else:
                self.action(**self.kwargs)
            
            self.last_run = datetime.now()
            self.run_count += 1
            self._calculate_next_run()
            print(f"  ✅ Completed")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


class TaskScheduler:
    """Schedule and execute automated tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._thread = None
    
    def add_task(self, name: str, schedule: str, action: Callable, **kwargs) -> ScheduledTask:
        """Add a new scheduled task."""
        task = ScheduledTask(name, schedule, action, **kwargs)
        self.tasks[name] = task
        print(f"📅 Scheduled: {name} ({schedule})")
        return task
    
    def remove_task(self, name: str):
        """Remove a scheduled task."""
        if name in self.tasks:
            del self.tasks[name]
            print(f"🗑️  Removed: {name}")
    
    def enable_task(self, name: str):
        """Enable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = True
            print(f"✅ Enabled: {name}")
    
    def disable_task(self, name: str):
        """Disable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = False
            print(f"⏸️  Disabled: {name}")
    
    def list_tasks(self):
        """List all tasks."""
        print("\n📋 SCHEDULED TASKS\n")
        for name, task in self.tasks.items():
            status = "🟢" if task.enabled else "🔴"
            next_run = task.next_run.strftime("%H:%M:%S") if task.next_run else "N/A"
            print(f"{status} {name}")
            print(f"   Schedule: {task.schedule}")
            print(f"   Next run: {next_run}")
            print(f"   Runs: {task.run_count}")
            print()
    
    async def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            for task in self.tasks.values():
                if task.should_run():
                    await task.run()
            
            await asyncio.sleep(1)
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        print("\n🚀 Task scheduler started")
        print(f"   Tasks: {len(self.tasks)}")
        print("   Press Ctrl+C to stop\n")
        
        try:
            asyncio.run(self._run_loop())
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        print("\n👋 Scheduler stopped")


# Predefined task actions
async def health_check():
    """Run system health check."""
    subprocess.run(["python", "skills/system_monitor.py"])


async def sync_agents():
    """Sync agent status with gateway."""
    print("  Syncing agents...")
    # Implementation would sync with Mission Control API


async def backup_data():
    """Backup system data."""
    backup_dir = Path.home() / ".axzora" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"
    
    # Backup workflows
    workflows_file = Path.home() / ".axzora" / "workflows.json"
    if workflows_file.exists():
        with open(workflows_file) as f:
            workflows = json.load(f)
        
        backup_data = {
            "timestamp": timestamp,
            "workflows": workflows
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"  Backup saved: {backup_file}")


def create_default_scheduler() -> TaskScheduler:
    """Create scheduler with default tasks."""
    scheduler = TaskScheduler()
    
    # Health check every 5 minutes
    scheduler.add_task(
        "health_check",
        "interval:300",
        health_check
    )
    
    # Agent sync every 2 minutes
    scheduler.add_task(
        "agent_sync",
        "interval:120",
        sync_agents
    )
    
    # Daily backup at 2 AM
    scheduler.add_task(
        "daily_backup",
        "daily:02:00",
        backup_data
    )
    
    return scheduler


def main():
    """Main entry point."""
    import sys
    
    scheduler = create_default_scheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            scheduler.list_tasks()
        elif command == "start":
            scheduler.start()
        elif command == "run" and len(sys.argv) > 2:
            task_name = sys.argv[2]
            if task_name in scheduler.tasks:
                asyncio.run(scheduler.tasks[task_name].run())
            else:
                print(f"Task not found: {task_name}")
        else:
            print("Usage: python task_scheduler.py [list|start|run <task_name>]")
    else:
        scheduler.list_tasks()


if __name__ == "__main__":
    main()
