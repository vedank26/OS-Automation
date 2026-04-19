import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation import execute_command
from assignment_solver import is_assignment_command, solve_assignment

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
    Run commands in a thread pool so long-running operations
    (e.g. npm install during React project creation) don't block
    the event loop or time out the HTTP connection.

    Assignment commands are routed to assignment_solver BEFORE
    reaching automation.py — keeping automation.py untouched.

    execute_command and solve_assignment both return a dict shaped
    as {"result": "..."} or {"result": "...", "options": [...]}
    via the _result() helper, so return directly — no extra wrapping.
    """
    loop = asyncio.get_event_loop()

    if is_assignment_command(cmd.text):
        # Route to assignment solver — never touches automation.py
        result = await loop.run_in_executor(None, solve_assignment, cmd.text)
    else:
        result = await loop.run_in_executor(None, execute_command, cmd.text)

    return result