from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

SERVER_SELECTION_TIMEOUT_MS = 5000


def create_mongo_client(uri: str) -> AsyncMongoClient:
    return AsyncMongoClient(uri, serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS, tz_aware=True)


def get_database(client: AsyncMongoClient, name: str) -> AsyncDatabase:
    return client[name]


async def is_database_reachable(database: AsyncDatabase) -> bool:
    try:
        await database.command("ping")
    except Exception:
        return False
    return True
