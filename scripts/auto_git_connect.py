#!/usr/bin/env python3
"""
Auto Git Repository Connection Script
Automatically connects all your Git repositories to Mission Control via webhooks
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import subprocess
import requests
from urllib.parse import urlparse

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_PATH))

from app.core.config import settings
from app.models.boards import Board
from app.models.board_webhooks import BoardWebhook
from app.db.session import get_session
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid

class GitRepoConnector:
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.api_token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.api_token else {}
        
    async def get_user_repos(self) -> List[Dict[str, Any]]:
        """Get all repositories for the authenticated user"""
        if not self.api_token:
            print("⚠️  No GitHub token found. Using local git repositories only.")
            return await self.get_local_repos()
        
        repos = []
        page = 1
        
        while True:
            url = f"https://api.github.com/user/repos?per_page=100&page={page}"
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                page_repos = response.json()
                
                if not page_repos:
                    break
                    
                repos.extend(page_repos)
                page += 1
                
            except requests.RequestException as e:
                print(f"❌ Error fetching repositories: {e}")
                break
        
        return repos
    
    async def get_local_repos(self) -> List[Dict[str, Any]]:
        """Find local git repositories on the system"""
        local_repos = []
        
        # Common directories to search
        search_paths = [
            Path.home() / 'Documents',
            Path.home() / 'Projects',
            Path.home() / 'Code',
            Path.home() / 'Development',
            Path('C:/Users') / os.getenv('USERNAME') / 'Documents' if os.name == 'nt' else Path('/home') / os.getenv('USER')
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                try:
                    for git_dir in search_path.rglob('.git'):
                        repo_path = git_dir.parent
                        repo_name = repo_path.name
                        repo_url = self.get_repo_remote_url(repo_path)
                        
                        if repo_url:
                            local_repos.append({
                                'name': repo_name,
                                'full_name': f"local/{repo_name}",
                                'html_url': repo_url,
                                'ssh_url': repo_url,
                                'clone_url': repo_url,
                                'private': False,
                                'local_path': str(repo_path)
                            })
                except Exception as e:
                    print(f"⚠️  Error searching {search_path}: {e}")
        
        return local_repos
    
    def get_repo_remote_url(self, repo_path: Path) -> str:
        """Get the remote URL of a local git repository"""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return f"file://{repo_path}"

class WebhookManager:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.token = "openclaw_local_dev_token_very_secure_key_for_mission_control_2026"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    async def get_boards(self) -> List[Dict[str, Any]]:
        """Get all boards from Mission Control"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/boards",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except requests.RequestException as e:
            print(f"❌ Error fetching boards: {e}")
            return []
    
    async def create_webhook(self, board_id: str, repo_name: str, repo_url: str) -> Dict[str, Any]:
        """Create a webhook for a specific repository"""
        webhook_data = {
            "description": f"Auto-created webhook for {repo_name}",
            "enabled": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/boards/{board_id}/webhooks",
                headers=self.headers,
                json=webhook_data
            )
            response.raise_for_status()
            webhook = response.json()
            
            print(f"✅ Created webhook for {repo_name}")
            print(f"   Webhook ID: {webhook['id']}")
            print(f"   Endpoint: {webhook['endpoint_url']}")
            
            return webhook
        except requests.RequestException as e:
            print(f"❌ Error creating webhook for {repo_name}: {e}")
            return {}

async def main():
    print("🎯 Auto Git Repository Connection")
    print("=" * 50)
    
    # Initialize connectors
    git_connector = GitRepoConnector()
    webhook_manager = WebhookManager()
    
    # Get repositories
    print("🔍 Finding Git repositories...")
    repos = await git_connector.get_user_repos()
    
    if not repos:
        print("❌ No repositories found")
        return
    
    print(f"✅ Found {len(repos)} repositories")
    
    # Get boards
    print("\n📋 Getting Mission Control boards...")
    boards = await webhook_manager.get_boards()
    
    if not boards:
        print("❌ No boards found. Please create a board first.")
        return
    
    print(f"✅ Found {len(boards)} boards")
    for board in boards:
        print(f"   - {board['name']} (ID: {board['id']})")
    
    # Select target board (default to first board)
    target_board = boards[0]
    print(f"\n🎯 Using board: {target_board['name']}")
    
    # Create webhooks for all repositories
    print(f"\n🔗 Creating webhooks for {len(repos)} repositories...")
    created_webhooks = []
    
    for repo in repos:
        repo_name = repo['full_name']
        repo_url = repo.get('html_url', repo.get('ssh_url', ''))
        
        webhook = await webhook_manager.create_webhook(
            target_board['id'], 
            repo_name, 
            repo_url
        )
        
        if webhook:
            created_webhooks.append({
                'repo_name': repo_name,
                'repo_url': repo_url,
                'webhook': webhook
            })
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total repositories found: {len(repos)}")
    print(f"   Webhooks created: {len(created_webhooks)}")
    print(f"   Target board: {target_board['name']}")
    
    if created_webhooks:
        print(f"\n📋 Created webhooks:")
        for item in created_webhooks:
            print(f"   - {item['repo_name']}: {item['webhook']['endpoint_url']}")
        
        # Save configuration
        config = {
            'timestamp': asyncio.get_event_loop().time(),
            'board_id': target_board['id'],
            'board_name': target_board['name'],
            'webhooks': [
                {
                    'repo_name': item['repo_name'],
                    'repo_url': item['repo_url'],
                    'webhook_id': item['webhook']['id'],
                    'endpoint_url': item['webhook']['endpoint_url']
                }
                for item in created_webhooks
            ]
        }
        
        config_file = PROJECT_ROOT / 'git_webhooks_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Configuration saved to: {config_file}")
        print("\n🎯 Next steps:")
        print("1. Configure your Git repositories to send webhooks to the endpoints above")
        print("2. For GitHub: Go to repo Settings → Webhooks → Add webhook")
        print("3. For GitLab: Go to repo Settings → Webhooks")
        print("4. Set payload URL to the webhook endpoint URLs")
        print("5. Select events: push, pull_request, issues, etc.")
        
    else:
        print("\n❌ No webhooks were created successfully")

if __name__ == "__main__":
    asyncio.run(main())