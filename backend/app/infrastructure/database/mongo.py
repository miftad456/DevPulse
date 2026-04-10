from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGO_URL, DB_NAME

client: AsyncIOMotorClient | None = None
database = None  # rename to avoid confusion


async def connect_to_mongo():
    global client, database

    print("Connecting to MongoDB...")
    print("MONGO_URL:", MONGO_URL)
    print("DB_NAME:", DB_NAME)

    client = AsyncIOMotorClient(MONGO_URL)
    database = client[DB_NAME]


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database():
    return database