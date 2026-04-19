import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation import execute_command
from assignment_solver import is_assignment_command, solve_assignment
from ai_engine import interpret_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Command(BaseModel):
    text: str = ""
    command: str = ""


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


@app.post("/smart-execute")
async def smart_execute(cmd: Command):
    loop = asyncio.get_event_loop()

    # Always use cmd.text — Flutter sends {"text": "..."}
    input_text = cmd.text.strip() if cmd.text else ""

    try:
        # Step 1 — AI interprets natural language
        interpreted = await loop.run_in_executor(
            None, interpret_command, input_text
        )

        # Step 2 — Route to correct handler
        if is_assignment_command(input_text):
            raw_result = await loop.run_in_executor(
                None, solve_assignment, input_text
            )
        else:
            raw_result = await loop.run_in_executor(
                None, execute_command, interpreted
            )

        # Step 3 — Normalize result to clean dict
        # execute_command returns dict like {"result": "...", "options": [...]}
        # We must NOT wrap it again
        if isinstance(raw_result, dict):
            # Add AI metadata to existing dict
            raw_result["original"] = input_text
            raw_result["interpreted"] = interpreted
            return raw_result
        else:
            # Fallback if somehow a string is returned
            return {
                "result": str(raw_result),
                "options": [],
                "original": input_text,
                "interpreted": interpreted,
            }

    except Exception as e:
        return {
            "result": f"❌ Error: {str(e)}",
            "options": [],
            "original": input_text,
            "interpreted": input_text,
        }

@app.get("/ai-status")
def ai_status_check():
    try:
        from ai_engine import get_ai_status
        return get_ai_status()
    except Exception as e:
        return {"status": "error", "error": str(e)}