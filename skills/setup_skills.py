#!/usr/bin/env python3
"""
Axzora Skills Setup - Register all skills in Mission Control
"""

import json
import requests
from pathlib import Path

MISSION_CONTROL_URL = "http://localhost:8000"
TOKEN = "openclaw_local_dev_token_very_secure_key_for_mission_control_2026"

def load_skills():
    """Load skills from JSON file"""
    skills_file = Path(__file__).parent / "axzora_skills.json"
    with open(skills_file) as f:
        return json.load(f)

def check_mission_control():
    """Check if Mission Control is running"""
    try:
        response = requests.get(f"{MISSION_CONTROL_URL}/healthz", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_skill_webhooks(board_id: str, skills: list):
    """Create webhooks for each skill"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    created = []
    for skill in skills:
        webhook_data = {
            "description": f"Skill: {skill['name']} - {skill['description']}",
            "enabled": True
        }
        
        try:
            response = requests.post(
                f"{MISSION_CONTROL_URL}/api/v1/boards/{board_id}/webhooks",
                headers=headers,
                json=webhook_data
            )
            
            if response.status_code == 200:
                webhook = response.json()
                created.append({
                    "skill_id": skill["id"],
                    "skill_name": skill["name"],
                    "webhook_id": webhook["id"],
                    "endpoint": webhook["endpoint_path"]
                })
                print(f"✅ Created webhook for: {skill['name']}")
            else:
                print(f"❌ Failed to create webhook for: {skill['name']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return created

def get_or_create_board():
    """Get existing board or create new one"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Check for existing skills board
    response = requests.get(
        f"{MISSION_CONTROL_URL}/api/v1/boards",
        headers=headers
    )
    
    if response.status_code == 200:
        boards = response.json().get("items", [])
        for board in boards:
            if "skill" in board.get("name", "").lower():
                return board["id"]
    
    # Get gateway ID
    gateways_response = requests.get(
        f"{MISSION_CONTROL_URL}/api/v1/gateways",
        headers=headers
    )
    
    if gateways_response.status_code == 200:
        gateways = gateways_response.json().get("items", [])
        if gateways:
            gateway_id = gateways[0]["id"]
            
            # Create skills board
            board_data = {
                "name": "Axzora Skills Board",
                "slug": "axzora-skills",
                "description": "Skills and agents for the Axzora ecosystem",
                "gateway_id": gateway_id
            }
            
            create_response = requests.post(
                f"{MISSION_CONTROL_URL}/api/v1/boards",
                headers=headers,
                json=board_data
            )
            
            if create_response.status_code == 200:
                return create_response.json()["id"]
    
    return None

def main():
    print("🎯 Axzora Skills Setup")
    print("=" * 50)
    
    # Check Mission Control
    print("\n📡 Checking Mission Control...")
    if not check_mission_control():
        print("❌ Mission Control is not running!")
        print("Start it with: cd backend && uv run uvicorn app.main:app --port 8000")
        return
    
    print("✅ Mission Control is running")
    
    # Load skills
    print("\n📦 Loading skills configuration...")
    data = load_skills()
    skills = data.get("skills", [])
    print(f"✅ Loaded {len(skills)} skills")
    
    # Get or create board
    print("\n📋 Setting up skills board...")
    board_id = get_or_create_board()
    
    if board_id:
        print(f"✅ Board ID: {board_id}")
        
        # Create webhooks
        print("\n🔗 Creating skill webhooks...")
        created = create_skill_webhooks(board_id, skills)
        
        # Save mapping
        output_file = Path(__file__).parent / "skill_webhooks_mapping.json"
        with open(output_file, "w") as f:
            json.dump({
                "board_id": board_id,
                "webhooks": created,
                "skills": skills,
                "agents": data.get("agents", {}),
                "configuration": data.get("configuration", {})
            }, f, indent=2)
        
        print(f"\n✅ Saved mapping to: {output_file}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎉 Setup Complete!")
        print(f"Board: http://localhost:3000/boards/{board_id}")
        print(f"Skills registered: {len(created)}")
        print("=" * 50)
    else:
        print("❌ Failed to create board")

if __name__ == "__main__":
    main()
