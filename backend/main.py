import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation import execute_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "FlowForge AI Backend is running ✅"}

@app.post("/execute")
async def execute(cmd: Command):
    """
    Run execute_command in a thread pool so long-running operations
    (e.g. npm install during React project creation) don't block the
    event loop or time out the HTTP connection.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_command, cmd.text)
    # execute_command already returns a dict shaped as {"result": "..."}
    # (via the _result() helper), so return it directly — no extra wrapping.
    return result