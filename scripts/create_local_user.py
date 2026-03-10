#!/usr/bin/env python3
"""
Script to create the local auth user directly in the database
This avoids the issue with the get_or_create function in the auth flow
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_PATH))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from app.core.config import settings
from app.core.auth import LOCAL_AUTH_USER_ID, LOCAL_AUTH_EMAIL, LOCAL_AUTH_NAME
from app.models.users import User
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid

def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return database_url

async def create_local_user_if_not_exists():
    database_url = _normalize_database_url(settings.database_url)
    engine = create_async_engine(database_url)
    
    async with AsyncSession(engine) as session:
        # Check if user already exists
        existing_user = await session.exec(
            select(User).where(User.clerk_user_id == LOCAL_AUTH_USER_ID)
        )
        user = existing_user.first()
        
        if user:
            print(f"✅ Local auth user already exists: {user.id}")
            return user
        
        # Create the local auth user
        user = User(
            id=uuid.uuid4(),
            clerk_user_id=LOCAL_AUTH_USER_ID,
            email=LOCAL_AUTH_EMAIL,
            name=LOCAL_AUTH_NAME,
            is_super_admin=True
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"✅ Created local auth user: {user.id}")
        return user

if __name__ == "__main__":
    asyncio.run(create_local_user_if_not_exists())