from fastapi import APIRouter
from agent_service.agent_models import ChatModel, ResumeChatModel
from agent_service.service import AgentServiceSingleton


router = APIRouter(prefix='/chat', tags=['chat', 'resume'])

@router.post('')
async def chat(data: ChatModel):
    agent_service = await AgentServiceSingleton.get_instance()
    async for chunk in agent_service.chat(data):
        yield chunk

@router.post('/resume')
async def resume(data: ResumeChatModel):
    agent_service = await AgentServiceSingleton.get_instance()
    async for chunk in agent_service.resume(data):
        yield chunk