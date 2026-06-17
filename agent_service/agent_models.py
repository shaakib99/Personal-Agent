from pydantic import BaseModel, Field

class ChatModel(BaseModel):
    query: str = Field('Hi!', description='This field contains the query of the user')
    checkpointer_id: str = Field(None, description='checkpointer_id to resume the conversation')
    files: list[str] = Field([], description='List of files uploaded with the message')

class ResumeChatModel(BaseModel):
    checkpointer_id: str = Field(None, description='checkpointer_id to resume the conversation')
    decision: str = Field(None, description='Decision of the user after interruption')

class InvokableModel(ChatModel, ResumeChatModel):
    pass

class BaseContext(BaseModel):
    user_email: str = Field('', description='This holds the user email')


