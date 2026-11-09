import asyncio
from passlib.context import CryptContext
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, Leader

# Konfiguracija za hashiranje lozinki
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


INITIAL_USERS = [
    {
        "username": "superadmin",
        "email": "admin@optcg.local",
        "password_hash": hash_password("Admin123!"),
        "role": "super_admin",
        "is_active": True,
    },
    {
        "username": "organizer",
        "email": "organizer@optcg.local",
        "password_hash": hash_password("Organizer123!"),
        "role": "admin",
        "is_active": True,
    },
    {
        "username": "player1",
        "email": "player1@optcg.local",
        "password_hash": hash_password("Player123!"),
        "role": "user",
        "is_active": True,
    },
]

INITIAL_LEADERS = [
    {"name": "Monkey.D.Luffy", "code": "OP01-003", "color": "Red"},
    {"name": "Roronoa Zoro", "code": "OP01-025", "color": "Red"},
    {"name": "Trafalgar Law", "code": "OP01-047", "color": "Red/Green"},
    {"name": "Eustass\"Captain\"Kid", "code": "OP01-051", "color": "Green"},
    {"name": "Kaido", "code": "OP01-061", "color": "Purple"},
    {"name": "Donquixote Doflamingo", "code": "OP01-073", "color": "Blue"},
    {"name": "Smoker", "code": "OP02-093", "color": "Black"},
    {"name": "Edward.Newgate", "code": "OP02-004", "color": "Red"},
    {"name": "Nami", "code": "OP03-040", "color": "Blue"},
    {"name": "Katakuri", "code": "OP03-099", "color": "Yellow"},
    {"name": "Sakazuki", "code": "OP05-041", "color": "Blue/Black"},
    {"name": "Enel", "code": "OP05-098", "color": "Yellow"},
]


async def seed_database():
    async with AsyncSessionLocal() as session:
        # 1. Punjenje korisnika
        for user_data in INITIAL_USERS:
            stmt = select(User).where(User.username == user_data["username"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                session.add(User(**user_data))

        # 2. Punjenje leadera
        for leader_data in INITIAL_LEADERS:
            stmt = select(Leader).where(Leader.code == leader_data["code"])
            result = await session.execute(stmt)
            existing_leader = result.scalar_one_or_none()

            if not existing_leader:
                session.add(Leader(**leader_data))

        await session.commit()
        print("Baza je uspješno napunjena početnim podacima (seed complete)!")


if __name__ == "__main__":
    asyncio.run(seed_database())