import asyncio
from hyperion_task.core.database import AsyncSessionLocal
from hyperion_task.core.security import hash_password
from hyperion_task.models import User, Organization
import uuid
from datetime import datetime, timezone

async def seed():
    async with AsyncSessionLocal() as session:
        org = Organization(name="Admin Org")
        session.add(org)
        await session.flush()
        user = User(
            user_id=uuid.uuid4(),
            org_id=org.org_id,
            email="admin@hyperion.com",
            hashed_password=hash_password("admin123"),
            name="Admin User",
            role="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.commit()
        print("Admin user created: admin@hyperion.com / admin123")

if __name__ == "__main__":
    asyncio.run(seed())