import os
import subprocess
import time
import requests
import json

# Configure Groq API (100% FREE!)
# Get your free API key from: https://console.groq.com/keys
GROQ_API_KEY = "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"  # Replace with your actual key


def create_ai_project(project_description: str, project_name: str = None):
    """
    Creates a complete project using AI:
    1. Generates project structure based on description
    2. Creates all files and folders
    3. Writes AI-generated code
    4. Opens the project in VS Code
    
    Args:
        project_description: What the user wants to build
        project_name: Optional project name (auto-generated if not provided)
    
    Returns:
        str: Status message
    """
    
    try:
        # Step 1: Generate project structure and code using AI
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

CRITICAL: Your response must START with {{ and END with }}. Nothing else."""

        
        print("🤖 AI is analyzing your project idea...")
        
        # Call Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a JSON generator. You ONLY output valid JSON. Never output code directly. Never use markdown. Never add explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"}  # Force JSON output
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            return f"❌ API Error: {response.status_code} - {response.text}"
        
        result = response.json()
        ai_output = result["choices"][0]["message"]["content"].strip()
        
        # Clean the response (remove markdown code blocks if present)
        if ai_output.startswith("```json"):
            ai_output = ai_output.replace("```json", "").replace("```", "").strip()
        elif ai_output.startswith("```"):
            ai_output = ai_output.replace("```", "").strip()
        
        # Additional cleanup - find JSON boundaries
        if "{" in ai_output and "}" in ai_output:
            start = ai_output.find("{")
            end = ai_output.rfind("}") + 1
            ai_output = ai_output[start:end]
        
        print(f"📄 Received {len(ai_output)} characters from AI")
        
        # Parse JSON response
        project_data = json.loads(ai_output)
        
        # Validate structure
        if "structure" not in project_data or not project_data["structure"]:
            return "❌ AI didn't generate any files. Try again with a more specific description."
        
        # Use provided project name or AI-generated one
        final_project_name = project_name if project_name else project_data.get("project_name", "my_project")
        
        # Clean project name
        final_project_name = final_project_name.replace(" ", "_").lower()
        
        # Step 2: Create project directory
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_path = os.path.join(desktop, final_project_name)
        
        # Create main project folder
        os.makedirs(project_path, exist_ok=True)
        print(f"📁 Created project folder: {final_project_name}")
        
        # Step 3: Create all files and directories from AI structure
        created_files = []
        structure = project_data.get("structure", {})
        
        for file_path, content in structure.items():
            # Skip empty content
            if not content or content.strip() == "":
                continue
                
            # Handle nested directories (e.g., "src/App.js")
            full_path = os.path.join(project_path, file_path)
            
            # Create parent directories if needed
            parent_dir = os.path.dirname(full_path)
            if parent_dir and parent_dir != project_path:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write the file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            created_files.append(file_path)
            print(f"   ✅ Created: {file_path}")
        
        if not created_files:
            return "❌ No files were created. AI response might be invalid."
        
        # Step 4: Open VS Code with the project
        time.sleep(0.5)
        subprocess.Popen(f'code "{project_path}"', shell=True)
        
        # Bring VS Code to front (Windows-specific)
        time.sleep(1)
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Visual Studio Code")
            if windows:
                windows[0].activate()
        except:
            pass
        
        # Build success message
        files_summary = ", ".join(created_files[:5])
        if len(created_files) > 5:
            files_summary += f" + {len(created_files) - 5} more"
        
        return (
            f"✅ AI Project Created: '{final_project_name}'\n"
            f"📂 Type: {project_data.get('project_type', 'N/A')}\n"
            f"📝 Files: {files_summary}\n"
            f"💻 Opened in VS Code\n"
            f"📍 Location: Desktop/{final_project_name}"
        )
    
    except json.JSONDecodeError as e:
        # Save the raw output to a file for debugging
        error_file = os.path.join(os.path.expanduser("~"), "Desktop", "ai_error_output.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(ai_output)
        
        return (
            f"❌ AI response parsing failed.\n"
            f"Error: {str(e)}\n"
            f"Raw output saved to: Desktop/ai_error_output.txt\n"
            f"Try the command again - sometimes the AI needs a retry."
        )
    
    except Exception as e:
        return f"❌ Project creation failed: {str(e)}"


def parse_create_command(command: str):
    """
    Extracts project description and optional name from command.
    
    Examples:
    - "create a snake game in python" -> ("snake game in python", None)
    - "create project named todo-app for a task manager" -> ("task manager", "todo-app")
    - "make me a calculator in react" -> ("calculator in react", None)
    """
    command = command.lower().strip()
    
    # Remove trigger words
    for trigger in ["create ai project", "create project", "make me", "build me", "create"]:
        command = command.replace(trigger, "", 1).strip()
    
    # Extract project name if specified
    project_name = None
    description = command
    
    if "named" in command:
        parts = command.split("named", 1)
        description = parts[0].strip()
        if len(parts) > 1:
            # Get everything after "named" until "for" or end of string
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
    
    # Clean up project name (remove spaces, make it filesystem-friendly)
    if project_name:
        project_name = project_name.strip().replace(" ", "-")
    
    # Clean up description
    description = description.strip()
    if description.startswith("for "):
        description = description[4:].strip()
    
    return description, project_name