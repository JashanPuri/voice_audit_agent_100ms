from typing import Optional
from .client import MongoDBClient

_mongo_client: Optional[MongoDBClient] = None

def get_mongo_client() -> MongoDBClient:
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Call init_mongo_db() first.")
    return _mongo_client

async def init_mongo_db():
    global _mongo_client
    
    if _mongo_client is not None:
        return _mongo_client
        
    _mongo_client = MongoDBClient()

    await _mongo_client.ping()
        
    return _mongo_client

async def close_mongo_db():
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None