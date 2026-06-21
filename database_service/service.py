import chromadb
import uuid
# from database_service.config import AllowedCollections
from typing import Dict, Any
from .models import QueryModel

class DatabaseService:
    def __init__(self, collection_name: str):
        db = chromadb.PersistentClient(path='db/local_chroma_db')
        self.collection = db.get_or_create_collection(collection_name)

    async def aget_one(self, id: str):
        return self.collection.get(
            ids=[id],
            limit=1,
            include=['documents', 'metadatas']
        )

    async def aget(self, data: QueryModel):
        return self.collection.query(
            query_texts=data.text,
            where=data.filter,
            n_results=data.limit,
            include=['data', 'documents', 'metadatas', 'distances']
        )

    async def acreate_one(self, text: str, data: Dict[str, Any]):
        record_id = data.get('id', uuid.uuid4())
        self.collection.upsert(
            documents=[text],
            ids=[record_id],
            metadatas=[data],
        )

    async def aupdate_one(self, id: str, text: str, data: Dict[str, Any]):
        return self.collection.update(
            documents=[text],
            ids=[id],
            metadatas=[data],
        )

    async def adelete_one(self, id: str):
        return self.collection.delete(
            ids=[id]
        )
