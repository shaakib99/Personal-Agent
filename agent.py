from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from fastapi import APIRouter
from mcp_tools import get_mcp_tools
from dotenv import load_dotenv
import os
import json

load_dotenv()

checkpointer = InMemorySaver()



router = APIRouter(prefix='/chat')

SYSTEM_PROMPT = """
                You are a capable AI assistant with access to the following tools:

                - Web search: Find and retrieve information from the internet
                - Web browsing: Visit, read, and interact with websites
                - File system: Create, read, modify, and delete files and directories
                - Read and write into files

                Guidelines:
                - Use tools proactively when the task requires current or external information
                - Always confirm file paths before creating or modifying files
                - When browsing websites, extract only the information relevant to the task
                - Chain tools together when needed (e.g., search → visit → extract → write to file)

                If the provided context or available tools are insufficient to complete the task, respond with:
                "I need more information to complete this task. Please provide: [specific missing detail]"
                """

@router.post('')
async def chat(data: dict):
    query = data.get('query', '')
    files = data.get('files', [])
    checkpointer_id = data.get('checkpointer_id', None)
    tools = await get_mcp_tools()

    config = {"recursion_limit": 200, 
              "configurable": {
                "thread_id": checkpointer_id
                }
            }
    agent = create_agent(
        model = ChatOpenAI(
            base_url='http://localhost:3001/v1',
            model='automatic',
            api_key=os.getenv('FREELLM_APIKEY')
            ),
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=[
                HumanInTheLoopMiddleware(interrupt_on={
                    'run_system_command_tool': {
                        'allowed_decisions': ["approve", "reject"],
                        'description': 'System Command Tool Call Pending decision'
                    },
                    'write_into_file_tool': True
                })
            ]
        )
    # agent = create_agent(
    #     model = ChatOpenAI(
    #         base_url='http://192.168.0.103:1234/v1',
    #         model='google/gemma-4-12b-qat',
    #         api_key=os.getenv('FREELLM_APIKEY')
    #         ),
    #         tools=tools,
    #         system_prompt=SYSTEM_PROMPT,
            #   checkpointer=InMemorySaver()

    #     )
    message = HumanMessage(content=query + (f' Here are the files {files}' if files else ''))
    # result = await agent.ainvoke({'messages': [message]})
    # return result['messages'][-1].content

    # Stream Langchain events natively
    async for event in agent.astream_events({'messages': [message]}, version="v2", config=config):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # Uniform JSON mapping for text tokens
                yield json.dumps({"type": "token", "content": content}) + "\n"

    # Check for middleware interruptions
    state = await agent.aget_state(config)
    if hasattr(state, "tasks") and state.tasks and state.tasks[0].interrupts:
        interrupt_data = state.tasks[0].interrupts[0]
        
        # Format text representation details safely
        tool_info = interrupt_data.value if hasattr(interrupt_data, 'value') else str(interrupt_data)
        if isinstance(tool_info, dict):
            tool_info = json.dumps(tool_info, indent=2)

        interrupt_payload = {
            "type": "interrupt",
            "tool_details": tool_info,
            "checkpointer_id": checkpointer_id
        }
        yield json.dumps(interrupt_payload) + "\n"


from fastapi import APIRouter, HTTPException
from langgraph.types import Command

router = APIRouter(prefix='/chat')
agent = create_agent(...)  # global, with checkpointer

@router.post('')
async def chat(data: dict):
    query = data['query']
    thread_id = data.get('checkpointer_id')
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 200}
    
    inputs = {"messages": [HumanMessage(content=query)]}

    tools = await get_mcp_tools()


    agent = create_agent(
        model = ChatOpenAI(
            base_url='http://localhost:3001/v1',
            model='automatic',
            api_key=os.getenv('FREELLM_APIKEY')
            ),
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=[
                HumanInTheLoopMiddleware(interrupt_on={
                    'run_system_command_tool': {
                        'allowed_decisions': ["approve", "reject"],
                        'description': 'System Command Tool Call Pending decision'
                    },
                    'write_into_file_tool': True
                })
            ]
        )
    
    # Stream until an interrupt or completion
    async for event in agent.astream_events(inputs, version="v2", config=config):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield json.dumps({"type": "token", "content": content})
    
    # After stream ends, check for interrupts
    state = await agent.aget_state(config)
    if state.tasks and state.tasks[0].interrupts:
        interrupt = state.tasks[0].interrupts[0]
        # Build and yield interrupt payload
        yield json.dumps({
            "type": "interrupt",
            "tool_details": json.dumps(interrupt.value),
            "checkpointer_id": thread_id
        })

@router.post('/resume')
async def resume(data: dict):
    thread_id = data.get('checkpointer_id')
    decision = data.get('decision', None)
    config = {"configurable": {"thread_id": thread_id}}

    tools = await get_mcp_tools()

    agent = create_agent(
        model = ChatOpenAI(
            base_url='http://localhost:3001/v1',
            model='automatic',
            api_key=os.getenv('FREELLM_APIKEY')
            ),
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=[
                HumanInTheLoopMiddleware(interrupt_on={
                    'run_system_command_tool': {
                        'allowed_decisions': ["approve", "reject"],
                        'description': 'System Command Tool Call Pending decision'
                    },
                    'write_into_file_tool': True
                })
            ]
        )
    
    # Validate that there is a pending interrupt
    state = await agent.aget_state(config)
    if not state.tasks or not state.tasks[0].interrupts:
        raise HTTPException(400, "No interrupt to resume")
    
    # Resume with decision (True = approve, False = reject)
    resume_value = True if decision == "approve" else False
    async for event in agent.astream_events(
        Command(resume={"decisions": [{"type": decision}]}),
        version="v2",
        config=config
    ):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield json.dumps({"type": "token", "content": content}) + "\n"
        
    # After stream ends, check for interrupts
    state = await agent.aget_state(config)
    if state.tasks and state.tasks[0].interrupts:
        interrupt = state.tasks[0].interrupts[0]
        # Build and yield interrupt payload
        yield json.dumps({
            "type": "interrupt",
            "tool_details": json.dumps(interrupt.value),
            "checkpointer_id": thread_id
        }) + "\n"
    