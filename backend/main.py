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
def execute(cmd: Command):
    result = execute_command(cmd.text)
    return {"result": result}