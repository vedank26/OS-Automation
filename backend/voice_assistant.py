import sys
import os
# Change this at the top
from automation_1 import execute_command

# To this — import the module itself so LAST_RESULTS stays live
import automation_1

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech_engine import listen, listen_short
from automation_1 import execute_command

def start_assistant():
    print("=======================================")
    print("🚀 Voice Assistant Started")
    print("=======================================")
    print("Press Ctrl+C to stop.")
    print("=======================================\n")

    try:
        while True:
            print("👂 Waiting for command...\n")
            command = listen()

            if not command:
                print("⏳ No command recognized. Listening again...\n")
                continue

            known_keywords = [
                "open", "search", "create", "run", "start", "launch",
                "press", "click", "type", "write", "scroll", "move",
                "screenshot", "shutdown", "restart", "focus", "play"
            ]

            has_keyword = any(command.lower().startswith(k) for k in known_keywords)

            if not has_keyword and "youtube" not in command.lower():
                print(f"🎵 No keyword detected — treating as YouTube search")
                command = f"play {command} on youtube"
                print(f"⚙️ Modified command: {command}")

            print(f"⚙️ Executing: {command}")
            response = execute_command(command)

            if isinstance(response, dict):
                result_text = response.get('result', 'No result')
                options = response.get('options', None)
                print(f"DEBUG options: {options}")  # ADD THIS
            else:
                result_text = 'Command executed.'
                options = None

            print(f"➡️ {result_text}\n")

            # ─────────────────────────────────────────
            # YouTube options — wait for number pick
            # ─────────────────────────────────────────
            if options:
                print("🎵 Results:")
                for i, title in enumerate(options, 1):
                    print(f"  {i}. {title}")
                print("\n👂 Say a number to play (e.g. '2' or 'play 2')...\n")

                max_attempts = 3
                attempts = 0

                while attempts < max_attempts:
                    selection = listen_short()

                    if not selection:
                        attempts += 1
                        print(f"⏳ Didn't catch that. {max_attempts - attempts} attempts left...\n")
                        continue

                    print(f"⚙️ Selection: {selection}")
                    sel_response = execute_command(selection)

                    if isinstance(sel_response, dict):
                        sel_result = sel_response.get('result', 'No result')
                    else:
                        sel_result = 'Done.'

                    print(f"➡️ {sel_result}\n")

                    if "Playing video" in sel_result:
                        print("✅ Video playing! Listening for next command...\n")
                        break
                    elif "Invalid" in sel_result or "No YouTube" in sel_result:
                        attempts += 1
                        print(f"❌ Invalid. Try again ({max_attempts - attempts} left)...\n")
                    else:
                        # They said something else entirely — go back to main loop
                        break

                if attempts >= max_attempts:
                    print("⚠️ No valid selection made. Listening for next command...\n")

    except KeyboardInterrupt:
        print("\n\n🛑 Voice Assistant stopped.")


if __name__ == "__main__":
    start_assistant()