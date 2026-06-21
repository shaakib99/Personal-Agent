from pydantic import BaseModel, Field
from typing import Dict, Any

class QueryModel(BaseModel):
    text: str = Field('', description='text for semantic search')
    filter: Dict[str, Any] = Field(description='where clause, usually add user_id and other filters here, for example {"user_id": USER_ID}')
    limit: int = 10

