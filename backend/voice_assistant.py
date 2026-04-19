import time
import sys
import os

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech_engine import listen
from automation_1 import execute_command

def start_assistant():
    print("=======================================")
    print("🚀 Voice Assistant Started")
    print("=======================================")
    print("You can say commands like:")
    print(" - 'open chrome'")
    print(" - 'open vscode'")
    print(" - 'play shape of you'")
    print(" - 'create react app called myapp'")
    print("\nPress Ctrl+C to stop.")
    print("=======================================\n")
    
    try:
        # Listen to the microphone
        command = listen()
        
        if command:
            print(f"\n⚙️ Executing: {command}")
            
            # Forward to the existing automation engine
            response = execute_command(command)
            
            # Print result
            if isinstance(response, dict):
                result_text = response.get('result', 'No result')
            else:
                result_text = 'Command executed.'
            print(f"➡️ Outcome: {result_text}\n")
            
            print("👋 Single command executed. Shutting down the Voice Assistant!")
        else:
            print("⏳ No command was recognized. Shutting down automatically.")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Voice Assistant stopped.")

if __name__ == "__main__":
    start_assistant()
