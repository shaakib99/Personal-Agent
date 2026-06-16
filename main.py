from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from mcp_tools import get_mcp_tools
from agent import router as agent_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    tools = await get_mcp_tools()
    print(tools)
    yield


origins = [
    "*",      # React local development port
]

app = FastAPI(lifespan=lifespan)

routers = [agent_router]

for router in routers: app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allows specific traffic
    allow_credentials=True,          # Allows cookies and auth headers
    allow_methods=["*"],             # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allows all custom/standard headers
)

@app.get('/check')
async def chec():
    return {"status": "SUCCESS"}