import os
import re
import subprocess
import time
import webbrowser
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


def _check_windows_terminal():
    """Check if Windows Terminal (wt) is available"""
    try:
        result = subprocess.run(
            ["wt", "--version"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def _format_code(content: str, file_ext: str) -> str:
    """
    Basic formatter to ensure code is not minified.
    Adds line breaks if code appears to be on one line.
    """
    lines = content.strip().split('\n')
    
    if len(lines) <= 3 and len(content) > 200:
        if file_ext in [".html"]:
            content = content.replace('><', '>\n<')
            content = content.replace('> <', '>\n<')
            lines = content.split('\n')
            formatted = []
            indent = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('</') or line.startswith('/>'):
                    indent = max(0, indent - 1)
                formatted.append('  ' * indent + line)
                if (line.startswith('<') and 
                    not line.startswith('</') and 
                    not line.startswith('<!') and
                    not line.endswith('/>') and
                    not '/>' in line):
                    indent += 1
            return '\n'.join(formatted)
        
        elif file_ext in [".css"]:
            content = content.replace('{', '{\n  ')
            content = content.replace(';', ';\n  ')
            content = content.replace('}', '\n}\n')
            return content
        
        elif file_ext in [".js", ".jsx"]:
            content = content.replace('{', '{\n  ')
            content = content.replace('}', '\n}')
            content = content.replace(';', ';\n')
            return content
    
    return content


def _auto_run_project(project_path: str, project_type: str):
    project_type = project_type.lower().strip()

    if project_type in ["react", "vite"]:
        
        # Detect CRA vs Vite
        package_json_path = os.path.join(
            project_path, "package.json"
        )
        run_script = "start"
        
        try:
            with open(package_json_path, "r") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "dev" in scripts:
                run_script = "dev"
            elif "start" in scripts:
                run_script = "start"
        except Exception:
            run_script = "start"

        port = "5173" if run_script == "dev" else "3000"

        # Open VS Code with project AND run command
        # in VS Code integrated terminal
        vscode_cmd = (
            f'code "{project_path}" '
            f'--new-window'
        )
        subprocess.Popen(vscode_cmd, shell=True)
        time.sleep(3)

        # Use VS Code CLI to run command in integrated terminal
        terminal_cmd = (
            f'cd /d "{project_path}" '
            f'&& npm install '
            f'&& npm run {run_script}'
        )
        # Open new VS Code terminal with command
        subprocess.Popen(
            f'code "{project_path}" --new-window',
            shell=True
        )
        time.sleep(2)
        # Run in VS Code terminal using workspace
        subprocess.Popen(
            f'wt -d "{project_path}" cmd /k "{terminal_cmd}"'
            if _check_windows_terminal()
            else f'start cmd /k "{terminal_cmd}"',
            shell=True
        )

        return f"🚀 React app starting on http://localhost:{port}"

    elif project_type in ["python", "py", "pygame"]:
        main_py = os.path.join(project_path, "main.py")
        imports_to_install = []

        stdlib = {
            "os","sys","re","time","math","random","json",
            "datetime","pathlib","collections","itertools",
            "functools","string","io","subprocess","threading",
            "urllib","http","sqlite3","csv","logging",
            "unittest","abc","copy","typing","enum","tkinter"
        }

        try:
            with open(main_py, "r") as f:
                content = f.read()
            found = re.findall(
                r'^(?:import|from)\s+(\w+)',
                content, re.MULTILINE
            )
            imports_to_install = [
                m for m in found if m not in stdlib
            ]
        except Exception:
            pass

        if imports_to_install:
            pkg_list = " ".join(imports_to_install)
            terminal_cmd = (
                f'cd /d "{project_path}" '
                f'&& echo Installing: {pkg_list}... '
                f'&& pip install {pkg_list} '
                f'&& echo Running... '
                f'&& python main.py'
            )
        else:
            terminal_cmd = (
                f'cd /d "{project_path}" '
                f'&& python main.py'
            )

        # Try Windows Terminal first, fallback to CMD
        if _check_windows_terminal():
            subprocess.Popen(
                f'wt -d "{project_path}" cmd /k "{terminal_cmd}"',
                shell=True
            )
        else:
            subprocess.Popen(
                f'start cmd /k "{terminal_cmd}"',
                shell=True
            )

        return "🐍 Python app running in terminal"

    elif project_type in ["flask"]:
        terminal_cmd = (
            f'cd /d "{project_path}" '
            f'&& pip install flask '
            f'&& python app.py'
        )
        if _check_windows_terminal():
            subprocess.Popen(
                f'wt -d "{project_path}" cmd /k "{terminal_cmd}"',
                shell=True
            )
        else:
            subprocess.Popen(
                f'start cmd /k "{terminal_cmd}"',
                shell=True
            )
        return "🌐 Flask app on http://localhost:5000"

    elif project_type in ["html", "css", "javascript", "js"]:
        index = os.path.join(project_path, "index.html")
        if os.path.exists(index):
            webbrowser.open(f"file:///{index}")
        return "🌐 HTML project opened in browser"

    else:
        if _check_windows_terminal():
            subprocess.Popen(
                f'wt -d "{project_path}"',
                shell=True
            )
        else:
            subprocess.Popen(
                f'start cmd /k "cd /d "{project_path}""',
                shell=True
            )
        return "📂 Project terminal opened"


def create_ai_project(project_description: str, project_name: str = None):
    """
    Creates a complete project using AI:
    1. Generates project structure based on description
    2. Creates all files and folders
    3. Writes AI-generated code
    4. Opens the project in VS Code
    """

    try:
        prompt = f"""You are a project generator. Create a JSON response for: {project_description}

Return ONLY this exact JSON structure (no extra text, no code blocks, no explanations):

{{
  "project_name": "snake_game",
  "project_type": "python",
  "description": "A simple terminal-based snake game",
  "structure": {{
    "main.py": "FULL_PYTHON_CODE_HERE",
    "README.md": "# Project Title\\n\\nInstructions here"
  }}
}}

Rules:
- project_name: lowercase_with_underscores for python, lowercase-with-hyphens for web
- project_type: python, react, html, nodejs, or flutter
- structure: Each file path maps to COMPLETE working code
- Put actual code in the values, not placeholders
- For python: include main.py and README.md (add requirements.txt if needed)
- For react: include package.json, src/App.js, src/index.js, public/index.html
- For html: include index.html, style.css, script.js

CRITICAL FORMATTING RULES — YOU MUST FOLLOW:
1. ALL code must be properly formatted with indentation
2. NEVER put code on a single line
3. HTML files must have proper line breaks after every tag
4. Python files must have proper indentation (4 spaces)
5. JavaScript files must have proper formatting
6. CSS files must have each property on its own line
7. Every opening tag gets its own line
8. Every closing tag gets its own line
9. Nested elements must be indented
10. Use 2 spaces for HTML/CSS/JS indentation
11. Use 4 spaces for Python indentation
12. Add blank lines between logical sections
13. NEVER minify or compress code
14. Code must be readable by a human

BAD EXAMPLE (never do this):
<!DOCTYPE html><html><head><title>App</title></head><body><h1>Hello</h1></body></html>

GOOD EXAMPLE (always do this):
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>App</title>
  </head>
  <body>
    <h1>Hello</h1>
  </body>
</html>

CRITICAL: Your response must START with {{ and END with }}. Nothing else.

IMPORTANT: Format all code properly with:
- Each HTML tag on its own line
- Proper indentation throughout  
- No minification
- Human-readable output
- Separate lines for each CSS property
- Proper JS formatting with line breaks"""

        print("🤖 AI is analyzing your project idea...")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. You ONLY output valid JSON. Never output code directly. Never use markdown. Never add explanations.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.5,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )

        ai_output = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if ai_output.startswith("```json"):
            ai_output = ai_output.replace("```json", "").replace("```", "").strip()
        elif ai_output.startswith("```"):
            ai_output = ai_output.replace("```", "").strip()

        # Find JSON boundaries
        if "{" in ai_output and "}" in ai_output:
            start = ai_output.find("{")
            end = ai_output.rfind("}") + 1
            ai_output = ai_output[start:end]

        print(f"📄 Received {len(ai_output)} characters from AI")

        project_data = json.loads(ai_output)

        if "structure" not in project_data or not project_data["structure"]:
            return "❌ AI didn't generate any files. Try again with a more specific description."

        final_project_name = (
            project_name if project_name else project_data.get("project_name", "my_project")
        )
        final_project_name = final_project_name.replace(" ", "_").lower()

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_path = os.path.join(desktop, final_project_name)
        os.makedirs(project_path, exist_ok=True)
        print(f"📁 Created project folder: {final_project_name}")

        created_files = []
        structure = project_data.get("structure", {})

        for file_path, content in structure.items():
            if not content or content.strip() == "":
                continue

            full_path = os.path.join(project_path, file_path)
            parent_dir = os.path.dirname(full_path)
            if parent_dir and parent_dir != project_path:
                os.makedirs(parent_dir, exist_ok=True)

            ext = os.path.splitext(file_path)[1]
            formatted_content = _format_code(content, ext)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)

            created_files.append(file_path)
            print(f"   ✅ Created: {file_path}")

        if not created_files:
            return "❌ No files were created. AI response might be invalid."

        # Open project in VS Code (already handled in _auto_run_project if needed, but safe here too)
        # Actually, let _auto_run_project handle opening the project if it's React,
        # but for other projects, we want it open too.
        # Wait, the user's prompt says:
        # "Inside create_ai_project(), after VS Code opens, make sure it looks like this:"
        # "subprocess.Popen(f'code \"{project_path}\"', shell=True)"
        # So I will keep this here exactly.
        time.sleep(0.5)
        subprocess.Popen(f'code "{project_path}"', shell=True)

        wait_time = 2
        time.sleep(wait_time)
        run_result = _auto_run_project(project_path, project_data.get("project_type", "unknown"))

        time.sleep(1)
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Visual Studio Code")
            if windows:
                windows[0].activate()
        except Exception:
            pass

        files_summary = ", ".join(created_files[:5])
        if len(created_files) > 5:
            files_summary += f" + {len(created_files) - 5} more"

        return (
            f"✅ Project Created: '{final_project_name}'\n"
            f"📁 Type: {project_data.get('project_type', 'N/A')}\n"
            f"📝 Files: {files_summary}\n"
            f"🖥️ Opened in VS Code\n"
            f"📍 Location: Desktop/{final_project_name}\n"
            f"{run_result}"
        )

    except json.JSONDecodeError as e:
        error_file = os.path.join(os.path.expanduser("~"), "Desktop", "ai_error_output.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(ai_output)
        return (
            f"❌ AI response parsing failed.\n"
            f"Error: {str(e)}\n"
            f"Raw output saved to: Desktop/ai_error_output.txt\n"
            f"Try the command again."
        )

    except Exception as e:
        return f"❌ Project creation failed: {str(e)}"


def parse_create_command(command: str):
    """
    Extracts project description and optional name from a natural language command.

    Examples:
    - "create calculator project using python"     -> ("calculator using python", None)
    - "create project of calculator using python"  -> ("calculator using python", None)
    - "build attendance tracker using html css js" -> ("attendance tracker using html css js", None)
    - "make a snake game in python"                -> ("snake game in python", None)
    - "create project named todo-app for task mgr" -> ("task manager", "todo-app")
    - "build me a calculator"                      -> ("calculator", None)
    """
    command = command.lower().strip()

    # ── Step 1: Remove trigger words longest-first ─────────────────────────
    for trigger in [
        "create ai project",
        "create project for",
        "create project of",        # ✅ "create project of calculator"
        "create project named",
        "create project called",
        "create project",
        "build project for",
        "build project of",
        "build project",
        "make project for",
        "make project of",
        "make project",
        "make me an",
        "make me a",
        "make me",
        "build me an",
        "build me a",
        "build me",
        "make an",
        "make a",
        "create an",
        "create a",
        "build an",
        "build a",
        "create",
        "build",
        "make",
    ]:
        if command.startswith(trigger):
            command = command[len(trigger):].strip()
            break

    # ── Step 2: Strip leftover connector words at the start ────────────────
    # Handles: "of calculator", "for a snake game", "me a todo app"
    for connector in ["of ", "for a ", "for an ", "for ", "me a ", "me an ", "me "]:
        if command.startswith(connector):
            command = command[len(connector):].strip()
            break

    # ── Step 3: Extract optional project name ──────────────────────────────
    project_name = None
    description = command

    if "named" in command:
        parts = command.split("named", 1)
        description = parts[0].strip()
        if len(parts) > 1:
            name_part = parts[1].strip()
            if "for" in name_part:
                project_name = name_part.split("for")[0].strip()
                description = name_part.split("for")[1].strip() + " " + description
            else:
                project_name = name_part

    elif "called" in command:
        parts = command.split("called", 1)
        description = parts[0].strip()
        if len(parts) > 1:
            name_part = parts[1].strip()
            if "for" in name_part:
                project_name = name_part.split("for")[0].strip()
                description = name_part.split("for")[1].strip() + " " + description
            else:
                project_name = name_part

    # ── Step 4: Clean up ───────────────────────────────────────────────────
    if project_name:
        project_name = project_name.strip().replace(" ", "-")

    description = description.strip()
    for prefix in ["for ", "of "]:
        if description.startswith(prefix):
            description = description[len(prefix):].strip()

    return description, project_name