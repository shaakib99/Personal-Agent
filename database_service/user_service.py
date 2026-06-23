from database_service.service import DatabaseService
from pydantic import BaseModel, Field
# from database_service.config import AllowedOps
from datetime import datetime
from .models import QueryModel
from typing import Dict, Any
import hashlib
from uuid import uuid4


class CreateUserMetaData(BaseModel):
    id: str = Field(None, description='Id of the user, if None, system will set')
    name: str = Field(description='Name of the user')
    email: str = Field(description='Email of the user')
    text: str = Field(description='can hold anything json data, like complete json text for semantic search. This field does not necessarily has to match the metadata')
    created_datetime: str = Field(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), description='datetime record created')


class UpdateUserMetaData(BaseModel):
    id: str = Field(description='Id of the user')
    name: str = Field(description='Name of the user')
    text: str = Field(description='can hold any string data, like complete json text for semantic search. This field does not necessarily has to match the metadata')


class UserQueryFields(BaseModel):
    email: str = Field(description='Email of the user. Example: {"filter": {"email": USER_EMAIL}}')
    


class UserService:
    def __init__(self):
        self._collection = 'user'
        self.database_service = DatabaseService(self._collection)

    async def aget_one(self, id: str):
        result = await self.database_service.aget_one(id)
        if result is None or len(result.get('ids')) == 0:
            raise ValueError('User not found')
        return result
    
    async def aget(self, query: Dict[str, Any]):
        data = QueryModel.model_validate(query)
        filter = UserQueryFields.model_validate(data.filter)
        data.filter = {
            k: v for k, v in filter.model_dump(exclude=[]).items()
            if v is not None and v != ''
        }
        return await self.database_service.aget(data)
    
    async def acreate_one(self, metadata: Dict[str, Any]):
        data = CreateUserMetaData.model_validate(metadata)
        data.id = str(uuid4())
        # ✅ semantic duplicate check using the text
        existing_query = QueryModel(text=data.text, filter={'id': data.id}, limit=1)
        existing = await self.database_service.aget(existing_query)
        if existing and len(existing.get('ids', [[]])[0]) > 0:
            return f'Similar user already exists: {existing.get("documents")[0][0]}. No need to try again, update the record instead. Skipping insert.'
        await self.database_service.acreate_one(data.text, data.model_dump(exclude=['text']))
        return await self.aget_one(data.id)
    
    async def aupdate_one(self, metadata: Dict[str, Any]):
        data = UpdateUserMetaData.model_validate(metadata)
        await self.database_service.aupdate_one(data.id, data.text, data.model_dump(exclude=['text', 'id']))
        return await self.aget_one(id)
    
    async def adelete_one(self, id: str):
        return await self.database_service.adelete_one(id)
    
    async def get_metadata_json(self, op: str):
        if op == 'create':
            return [{'field_name': field_name, 'field_description': field_info.description} for field_name, field_info in CreateUserMetaData.model_fields.items()]
        elif op == 'update':
            return [{'field_name': field_name, 'field_description': field_info.description} for field_name, field_info in UpdateUserMetaData.model_fields.items()]
        elif op == 'get':
            result =  [{'field_name': field_name, 'field_description': field_info.description, 'is_required': field_info.is_required()} for field_name, field_info in QueryModel.model_fields.items()]
            available_filter_options = []
            for field_name, field_info in UserQueryFields.model_fields.items():
                available_filter_options.append({
                        'field_name' : field_name,
                        'description': field_info.description,
                        'is_required': field_info.is_required()
                    })
            result.append({
                'available_filter_options': available_filter_options
            })
            print(result)
            return result
        elif op == 'get_one':
            return [{'field_name': 'id', 'field_description': 'id of the record'}]
        else:
            return f'metadata type not found'



