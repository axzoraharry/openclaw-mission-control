#!/usr/bin/env python3
"""
Mr. Happy Task Creation Script
Creates a sample task to test the local Llama 3.2 model processing
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "openclaw_local_dev_token_very_secure_key_for_mission_control_2026"

class TaskCreator:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
    def create_sample_task(self):
        """Create a sample task to test the local AI processing"""
        task_data = {
            "title": "Morning Briefing Analysis",
            "description": f"Analyze current project status for Satyug, Happy Cricket, and Happy Paisa using the local Llama 3.2 model. Generate strategic insights and next steps. Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "status": "pending",
            "priority": "high",
            "tags": ["ceo-briefing", "local-ai", "strategic"]
        }
        
        # First, let's check if we have any boards
        try:
            boards_response = requests.get(
                f"{API_BASE_URL}/api/v1/boards",
                headers=self.headers
            )
            
            if boards_response.status_code == 200:
                boards_data = boards_response.json()
                boards = boards_data.get("items", [])
                if boards and len(boards) > 0:
                    board_id = boards[0]["id"]
                    board_name = boards[0].get("name", "Unknown Board")
                    print(f"📝 Using board: {board_name} (ID: {board_id})")
                else:
                    print("❌ No boards found. Please create a board first in the UI.")
                    return None
            else:
                print(f"❌ Failed to fetch boards: {boards_response.status_code}")
                return None
                
            # Create task in the first board
            response = requests.post(
                f"{API_BASE_URL}/api/v1/boards/{board_id}/tasks",
                headers=self.headers,
                json=task_data
            )
            
            if response.status_code == 201:
                task = response.json()
                print("✅ Task created successfully!")
                print(f"Task ID: {task.get('id')}")
                print(f"Title: {task.get('title')}")
                print(f"Status: {task.get('status')}")
                return task
            else:
                print(f"❌ Failed to create task: {response.status_code}")
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            return None
    
    def get_task_status(self, task_id):
        """Check the status of a created task"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/tasks/{task_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                task = response.json()
                print(f"📊 Task Status Update:")
                print(f"   ID: {task.get('id')}")
                print(f"   Status: {task.get('status')}")
                print(f"   Updated: {task.get('updated_at')}")
                return task
            else:
                print(f"❌ Failed to get task status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error checking task status: {e}")
            return None

def main():
    print("🦞 Mr. Happy Task Creation Test")
    print("=" * 40)
    
    creator = TaskCreator()
    
    # Create a sample task
    task = creator.create_sample_task()
    
    if task:
        task_id = task.get('id')
        print(f"\n📋 Created task with ID: {task_id}")
        print("⏳ Waiting for local Llama 3.2 processing...")
        
        # Wait a moment and check status
        import time
        time.sleep(3)
        
        # Check task status
        updated_task = creator.get_task_status(task_id)
        
        if updated_task:
            print(f"\n🎉 Task is being processed by your local Digital CEO!")
            print("The Llama 3.2 model should now be analyzing your business data locally.")
        else:
            print("\n⚠️  Task status check failed, but task was created successfully.")

if __name__ == "__main__":
    main()