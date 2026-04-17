from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import os
import webbrowser

app = FastAPI()

class Command(BaseModel):
    text: str

@app.post("/execute")
def execute(cmd: Command):
    command = cmd.text.lower()

    # ✅ Open VS Code
    if "open vscode" in command:
        subprocess.run("code", shell=True)
        return {"result": "VS Code opened"}

    # ✅ Open Chrome
    elif "open chrome" in command:
        subprocess.run("start chrome", shell=True)
        return {"result": "Chrome opened"}

    # ✅ Create Folder
    elif "create folder" in command:
        # Extract folder name after "named" or "called"
        if "named" in command:
            folder_name = command.split("named")[-1].strip()
        elif "called" in command:
            folder_name = command.split("called")[-1].strip()
        else:
            folder_name = "NewFolder"

        path = os.path.join(os.path.expanduser("~"), "Desktop", folder_name)
        os.makedirs(path, exist_ok=True)
        return {"result": f"Folder '{folder_name}' created on Desktop"}

    # ✅ Create React App
    elif "create react app" in command:
        # Extract app name if mentioned
        if "named" in command:
            app_name = command.split("named")[-1].strip().replace(" ", "-")
        elif "called" in command:
            app_name = command.split("called")[-1].strip().replace(" ", "-")
        else:
            app_name = "my-app"

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        subprocess.Popen(
            f"npx create-react-app {app_name}",
            shell=True,
            cwd=desktop
        )
        return {"result": f"Creating React app '{app_name}' on Desktop..."}

    # ✅ Search Query
    elif "search" in command:
        # Extract what to search
        query = command.replace("search", "").strip()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        else:
            url = "https://www.google.com"
        webbrowser.open(url)
        return {"result": f"Searching for '{query}'"}

    # ✅ Play Music
    elif "play music" in command or "play song" in command:
        # Opens default music player
        subprocess.run("start wmplayer", shell=True)
        return {"result": "Music player opened"}

    # ✅ Open Notepad
    elif "open notepad" in command:
        subprocess.run("notepad", shell=True)
        return {"result": "Notepad opened"}

    # ✅ Open File Explorer
    elif "open explorer" in command or "open files" in command:
        subprocess.run("explorer", shell=True)
        return {"result": "File Explorer opened"}

    # ✅ Open Task Manager
    elif "open task manager" in command:
        subprocess.run("taskmgr", shell=True)
        return {"result": "Task Manager opened"}

    # ✅ Shutdown PC
    elif "shutdown" in command:
        subprocess.run("shutdown /s /t 5", shell=True)
        return {"result": "PC will shutdown in 5 seconds"}

    # ✅ Restart PC
    elif "restart" in command:
        subprocess.run("shutdown /r /t 5", shell=True)
        return {"result": "PC will restart in 5 seconds"}

    # ❌ Not Recognized
    else:
        return {"result": f"Command not recognized: '{cmd.text}'"}


# ✅ Home route (just for checking server is alive)
@app.get("/")
def home():
    return {"message": "FlowForge AI Backend is running"}