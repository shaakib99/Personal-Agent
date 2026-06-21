from database_service.service import DatabaseService
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from .models import QueryModel
from uuid import uuid4
# from database_service.config import AllowedOps
from database_service.user_service import UserService

class CreatePreferenceMetaData(BaseModel):
    id: str = Field(None, description='Id of the user, if None, system will set')
    text: str = Field(description='can hold any string data, like complete json text for semantic search. This field does not necessarily has to match the metadata')
    type: str = Field(None, description='Type of preference')
    created_datetime: str = Field(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), description='datetime record created')
    user_id: str = Field('', description='prefrence of the user. Id will be coming from user collection')
    user_email: str = Field(description='''email of the user. this field is for ai agent''')


class UpdatePreferenceMetaData(BaseModel):
    id: str = Field(description='Id of the user')
    type: str = Field(None, description='Type of preference')
    text: str = Field(description='can hold any string data, like complete json text for semantic search. This field does not necessarily has to match the metadata')


class PreferenceQueryField(BaseModel):
    user_email: str = Field(description='''user_email of the user. type: str''')
    user_id: str = Field(None, description='''user_id of the user. For AI agent no need to populate it''')
    # type: str =  Field(None, description='Type of preference')


class PreferenceService:
    def __init__(self):
        self._collection = 'preference'
        self.database_service = DatabaseService(self._collection)
        self.user_service = UserService()

    async def aget_one(self, id: str):
        result = await self.database_service.aget_one(id)
        if result is None or len(result.get('ids')) == 0:
            raise ValueError('User not found')
        return result
    
    async def aget(self, data: Dict[str, Any]):
        query = QueryModel.model_validate(data)
        filter = PreferenceQueryField.model_validate(query.filter)
        if filter.user_email is not None:
            user_query_model = QueryModel(text='', filter={'email': filter.user_email}, limit=1)
            user = await self.user_service.aget(user_query_model.model_dump())
            if user is None or len(user.get('ids')) == 0: raise Exception(f'User not found with {filter.user_email}')
            filter.user_id = user.get('ids')[0][0]
        
        if filter.user_email == None and filter.user_id is None: raise Exception(f'user_id or user_email is required')
        
        query.filter = {
            k: v for k, v in filter.model_dump(exclude={'user_email'}).items()
            if v is not None and v != ''
        }
        return await self.database_service.aget(query)
    
    async def acreate_one(self, metadata: Dict[str, Any]):
        data = CreatePreferenceMetaData.model_validate(metadata)
        if data.user_email:
            user_query_model = QueryModel(text='', filter={'email': data.user_email}, limit=1)
            user = await self.user_service.aget(user_query_model.model_dump())
            if user is None or len(user.get('ids')) == 0: return f'Passed user id does not exist'
            data.user_id = user.get('ids')[0][0]
        
        # ✅ semantic duplicate check using the text
        existing_query = QueryModel(text=data.text, filter={'user_id': data.user_id}, limit=1)
        existing = await self.database_service.aget(existing_query)
        if existing and len(existing.get('ids', [[]])[0]) > 0:
            return f'Similar preference already exists: {existing.get("documents")[0][0]}. No need to try again, update the record instead. Skipping insert.'
        data.id = str(uuid4())
        await self.database_service.acreate_one(data.text, data.model_dump(exclude=['text']))
        return await self.aget_one(data.id)
    
    async def aupdate_one(self, metadata: Dict[str, Any]):
        data = UpdatePreferenceMetaData.model_validate(metadata)
        await self.database_service.aupdate_one(data.id, data.text, data.model_dump(exclude=['text', 'id']))
        return await self.aget_one(data.id)
    
    async def adelete_one(self, id: str):
        return await self.database_service.adelete_one(id)
    
    async def get_metadata_json(self, op: str):
        if op == 'create':
            return [{'field_name': field_name, 'field_description': field_info.description} for field_name, field_info in CreatePreferenceMetaData.model_fields.items()]
        elif op == 'update':
            return [{'field_name': field_name, 'field_description': field_info.description} for field_name, field_info in UpdatePreferenceMetaData.model_fields.items()]
        elif op == 'get':
            result = [{'field_name': field_name, 'field_description': field_info.description, 'is_required': field_info.is_required()} for field_name, field_info in QueryModel.model_fields.items()]
            available_filter_options = []
            for field_name, field_info in PreferenceQueryField.model_fields.items():
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



