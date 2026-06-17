from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from agent_service.router import router as agent_router
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


origins = ["*"]

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
async def check():
    return {"status": "SUCCESS"}