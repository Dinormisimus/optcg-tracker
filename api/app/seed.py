import asyncio
import json
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, Leader

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

INITIAL_USERS = [
    {
        "username": "superadmin",
        "email": "admin@example.com",
        "password_hash": hash_password("Admin123!"),
        "role": "super_admin",
        "is_active": True,
    },
    {
        "username": "organizer",
        "email": "organizer@example.com",
        "password_hash": hash_password("Organizer123!"),
        "role": "admin",
        "is_active": True,
    },
    {
        "username": "player1",
        "email": "player1@example.com",
        "password_hash": hash_password("Player123!"),
        "role": "user",
        "is_active": True,
    },
]

async def seed_database():
    async with AsyncSessionLocal() as session:
        # 1. Unos korisnika
        for user_data in INITIAL_USERS:
            stmt = select(User).where(User.username == user_data["username"])
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(User(**user_data))

        # 2. Unos vođa iz JSON datoteke
        json_path = Path(__file__).resolve().parents[2] / "src" / "data" / "leaders.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                leaders_list = json.load(f)

            for leader_data in leaders_list:
                stmt = select(Leader).where(Leader.code == leader_data["code"])
                result = await session.execute(stmt)
                if not result.scalar_one_or_none():
                    session.add(Leader(**leader_data))

        await session.commit()
        print("Baza je uspješno osvježena s vođama (seed complete)!")

if __name__ == "__main__":
    asyncio.run(seed_database())