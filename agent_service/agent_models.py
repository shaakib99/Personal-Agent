from pydantic import BaseModel, Field
from langchain_core.documents import Document

class BaseContext(BaseModel):
    user_email: str = Field('', description='This holds the user email')
    file_data: list[Document] = Field([], description='This field will hold the information about uploaded documents')

class Skill(BaseModel):
    name: str = Field(None, description='Name of the skill')
    description: str = Field(None, description='Description of the skill')

class ChatModel(BaseModel):
    query: str = Field('Hi!', description='This field contains the query of the user')
    checkpointer_id: str = Field(None, description='checkpointer_id to resume the conversation')
    context: BaseContext = Field(BaseContext(), description='context for the model')
    skills: list[Skill] = Field([], description='All skills send by the client')

class ResumeChatModel(BaseModel):
    checkpointer_id: str = Field(None, description='checkpointer_id to resume the conversation')
    decision: str = Field(None, description='Decision of the user after interruption')

class InvokableModel(ChatModel, ResumeChatModel):
    pass



