import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation_1 import execute_command
from speech_engine import listen  # ADD THIS

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
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_command, cmd.text)
    return result

# ✅ ADD THIS NEW ENDPOINT
@app.post("/listen")
async def listen_command():
    """
    Activates Python microphone, transcribes speech,
    executes command, returns result to Flutter
    """
    loop = asyncio.get_event_loop()
    command = await loop.run_in_executor(None, listen)
    if command:
        result = await loop.run_in_executor(None, execute_command, command)
        return {
            "heard": command,
            "result": result.get("result", "Done"),
            "options": result.get("options", []),
        }
    return {
        "heard": None,
        "result": "Nothing heard. Try again.",
        "options": [],
    }