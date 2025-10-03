import os
from typing import Optional, Dict, Any, List
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from bson.objectid import ObjectId


class MongoDBClient:
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("MONGODB_DATABASE_NAME")
        if not self.connection_string:
            raise ValueError(
                "MongoDB connection string not found. Please set the MONGODB_URI environment variable."
            )
        
        if not self.database_name:
            raise ValueError(
                "Database name not found. Please set the MONGODB_DATABASE_NAME environment variable."
            )
        
        self.client: AsyncMongoClient = AsyncMongoClient(self.connection_string)
        self.db: AsyncDatabase = self.client.get_database(self.database_name)
    
    def get_collection(self, collection_name: str) -> AsyncCollection:
        return self.db.get_collection(collection_name)
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        collection = self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "_id" in query and query["_id"] is not None and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        collection = self.get_collection(collection_name)
        document = await collection.find_one(query)

        if document and "_id" in document:
            document["_id"] = str(document["_id"])
        
        return document
    
    
    async def find_many(
        self, 
        collection_name: str, 
        query: Dict[str, Any], 
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        if "_id" in query and query["_id"] is not None and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        collection = self.get_collection(collection_name)
        cursor = collection.find(query)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        
        documents = await cursor.to_list(length=limit)
        for document in documents:
            if "_id" in document:
                document["_id"] = str(document["_id"])
        return documents
    
    async def update_one(
        self, 
        collection_name: str, 
        query: Dict[str, Any], 
        update: Dict[str, Any]
    ) -> int:
        if "_id" in query and query["_id"] is not None and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        collection = self.get_collection(collection_name)
        result = await collection.update_one(query, update)
        return result.modified_count
    
    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        if "_id" in query and query["_id"] is not None and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        collection = self.get_collection(collection_name)
        result = await collection.delete_one(query)
        return result.deleted_count
    
    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        collection = self.get_collection(collection_name)
        return await collection.count_documents(query)
    
    def close(self):
        self.client.close()

    def ping(self):
        return self.client.admin.command("ping")

