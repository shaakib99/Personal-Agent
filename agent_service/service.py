from langchain.agents import create_agent
from langchain_openai.chat_models import ChatOpenAI
from agent_service.config import SYSTEM_PROMPT, MODEL_BASE_URL, MODEL_NAME, USER_EMAIL
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
from agent_service.agent_models import ChatModel, ResumeChatModel, InvokableModel, BaseContext
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel
from langgraph.types import Command
from fastapi import HTTPException
from langchain.tools import BaseTool
from database_service.tools.database_tool import get_basic_information_of_current_user, get_metadata_json, get_records, create_new_record, update_one_record, delete_one_record
from mcp_tools import get_mcp_tools
from .tools.load_skill import load_skill
from typing import AsyncGenerator
import os
import json


class AgentService:
    def __init__(self, checkpointer = None):
        self.model = ChatOpenAI(
            base_url=MODEL_BASE_URL,
            model=MODEL_NAME,
            api_key=os.getenv('FREELLM_APIKEY')
        )
        self.checkpointer = checkpointer or InMemorySaver()
        self.agent: CompiledStateGraph | None = None
    
    @classmethod
    async def create(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        mcp_tools = await get_mcp_tools()
        local_tools = [load_skill, get_basic_information_of_current_user, get_metadata_json, get_records, create_new_record, update_one_record, delete_one_record]
        available_tools = [*mcp_tools, *local_tools]
        instance.agent = create_agent(
            model=instance.model,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=instance.checkpointer,
            tools = available_tools,
            context_schema=BaseContext,
            middleware=[
                HumanInTheLoopMiddleware(interrupt_on={
                    'run_system_command_tool': {
                        'allowed_decisions': ["approve", "reject"],
                        'description': 'System Command Tool Call Pending decision'
                    },
                    'delete_user_data': {
                        'allowed_decisions': ["approve", "reject"],
                        'description': 'System Command Tool Call Pending decision'
                    },
                    'write_into_file_tool': True
                })
            ]
        )

        return instance


    async def chat(self, data: ChatModel)-> AsyncGenerator[str, str]:
        if self.agent is None: raise Exception('Agent is not initiazed')

        config: RunnableConfig = {
            'configurable': {
                'thread_id': data.checkpointer_id,
            }
        }

        context = data.context
        context.user_email = USER_EMAIL

        invokable_model = InvokableModel()
        invokable_model.checkpointer_id = data.checkpointer_id
        invokable_model.query = data.query

        async for chunk in self._invoke_stream(invokable_model, config, context):
            yield chunk

    async def resume(self, data: ResumeChatModel):
        config: RunnableConfig = {
            'configurable': {
                'thread_id': data.checkpointer_id
            },
        }

        context = BaseContext(user_email=USER_EMAIL)

        # Validate that there is a pending interrupt
        state = await self.agent.aget_state(config)
        if not state.tasks or not state.tasks[0].interrupts:
            raise HTTPException(400, "No interrupt to resume")
        
        invokable_model = InvokableModel()
        invokable_model.checkpointer_id = data.checkpointer_id
        invokable_model.decision = data.decision
        
        async for chunk in self._invoke_stream(invokable_model, config, context ):
            yield chunk

    async def _invoke_stream(self, data: InvokableModel, config: dict, context: BaseModel = None) -> AsyncGenerator[str, str]:
        config['recursion_limit'] = 80
        if data.decision is None:
            message = HumanMessage(content=data.query)
            events = self.agent.astream_events({'messages': [message]}, version='v2', config=config, context=context)
        else:
            events = self.agent.astream_events(Command(resume={"decisions": [{"type": data.decision}]}), version='v2', config=config, context=context)
        
        async for event in events:
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield json.dumps({"type": "token", "content": content}) + "\n"
        
        # Check for middleware interruptions
        state = await self.agent.aget_state(config)
        if hasattr(state, "tasks") and state.tasks and state.tasks[0].interrupts:
            interrupt_data = state.tasks[0].interrupts[0]
            
            # Format text representation details safely
            tool_info = interrupt_data.value if hasattr(interrupt_data, 'value') else str(interrupt_data)
            if isinstance(tool_info, dict):
                tool_info = json.dumps(tool_info, indent=2)

            interrupt_payload = {
                "type": "interrupt",
                "tool_details": tool_info,
                "checkpointer_id": data.checkpointer_id
            }
            yield json.dumps(interrupt_payload) + "\n"


class AgentServiceSingleton:
    _instance = None

    @classmethod
    async def get_instance(cls, *args, **kwargs):
        if cls._instance is not None: return cls._instance
        cls._instance = await AgentService.create(*args, **kwargs)
        return cls._instance