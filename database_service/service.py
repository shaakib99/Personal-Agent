import chromadb
import hashlib

class DatabaseService:
    def __init__(self, collection_name: str):
        db = chromadb.Client()
        self.collection = db.get_or_create_collection(collection_name)

    async def aget_one(self, id: str):
        return self.collection.query(
            ids=[id],
            n_results=1
        )

    async def aget(self, where: dict = {}, limit: int = 10):
        return self.collection.get(
            where=where,
            limit=limit
            
        )

    async def acreate_one(self, data: str, doc_id: str):
        return self.collection.upsert(
            documents=[data],
            ids=[doc_id],
            metadatas= {
                'id': doc_id
            }
        )

    async def aupdate_one(self, id: str, data: str):
        return self.collection.update(
            documents=[data],
            ids=[id]
        )

    async def adelete_one(self, id: str):
        return self.collection.delete(
            ids=[id]
        )
