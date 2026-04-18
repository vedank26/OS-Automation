import os
import re
import subprocess
import time
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import requests
from dotenv import load_dotenv

from ai_project_creator import create_ai_project, parse_create_command


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

pyautogui.FAILSAFE = True

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
print("YouTube API Loaded:", YOUTUBE_API_KEY)
LAST_RESULTS = []

# ─────────────────────────────────────────
# Filler words to strip from YouTube queries
# Merged from Aditya's file (Point 3)
# ─────────────────────────────────────────
FILLER_WORDS = {"on", "the", "a", "an", "in", "at"}


def _result(message: str, options: list[str] | None = None):
    payload = {"result": message}
    if options is not None:
        payload["options"] = options
    return payload


def _bring_window_to_front(keywords: list[str]):
    try:
        import pygetwindow as gw

        time.sleep(1.5)
        all_windows = gw.getAllTitles()
        for keyword in keywords:
            for title in all_windows:
                if keyword.lower() in title.lower() and title.strip():
                    try:
                        windows = gw.getWindowsWithTitle(title)
                        if not windows:
                            continue

                        window = windows[0]
                        try:
                            if window.isMinimized:
                                window.restore()
                                time.sleep(0.3)
                            window.activate()
                            time.sleep(0.3)
                            return "focused"
                        except Exception:
                            continue
                    except Exception:
                        continue
        return "opened"
    except Exception:
        return "opened"


def search_youtube(query: str):
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not configured in backend/.env")

    response = requests.get(
        YOUTUBE_API_URL,
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 5,
            "key": YOUTUBE_API_KEY,
        },
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    if not payload.get("items"):
        return []

    if "error" in payload:
        message = payload["error"].get("message", "Unknown YouTube API error")
        raise RuntimeError(message)

    results = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        title = item.get("snippet", {}).get("title")
        if video_id and title:
            results.append({"videoId": video_id, "title": title})

    return results


def play_video(index: int):
    if not LAST_RESULTS:
        return _result(
            "No YouTube results available. "
            "Use 'play <query> on youtube' first."
        )

    if index < 0 or index >= len(LAST_RESULTS):
        return _result(
            f"Invalid video number. Choose between 1 and {len(LAST_RESULTS)}."
        )

    video = LAST_RESULTS[index]
    video_url = (
        f"https://www.youtube.com/watch?v={video['videoId']}&autoplay=1"
    )
    webbrowser.open(video_url)
    _bring_window_to_front(["youtube", "edge", "chrome"])
    return _result(f"Playing video {index + 1}: '{video['title']}'")


def _get_video_index(command: str):
    word_map = {
        "play 1": 0,
        "first": 0,
        "1": 0,
        "play 2": 1,
        "second": 1,
        "2": 1,
        "play 3": 2,
        "third": 2,
        "3": 2,
        "play 4": 3,
        "fourth": 3,
        "4": 3,
        "play 5": 4,
        "fifth": 4,
        "5": 4,
    }
    return word_map.get(command.strip())


def extract_youtube_query(command: str):
    command = command.lower()

    remove_words = [
        "on youtube",
        "play",
        "open",
        "youtube",
        "and",
        "give me",
        "show me",
        "in",
    ]

    for word in remove_words:
        command = command.replace(word, "")

    return " ".join(command.split()).strip()


def _extract_youtube_play_query(raw_command: str):
    query = raw_command.lower()
    
    noise_phrases = [
        "on youtube",
        "in youtube", 
        "on the youtube",
        "youtube search",
        "search youtube",
        "search on youtube",
        "find on youtube",
        "play on youtube",
        "play in youtube",
        "youtube play",
        "on yt",
        "in yt",
    ]

    for phrase in noise_phrases:
        query = query.replace(phrase, "").strip()

    if query.startswith("play "):
        query = query[5:].strip()

    query = " ".join(query.split()).strip()
    return query if query else None


def execute_command(command: str):
    global LAST_RESULTS

    try:
        raw_command = command.strip()
        normalized_command = raw_command.lower()

        if not normalized_command:
            return _result("No command provided.")

        if "open vscode" in normalized_command:
            subprocess.run("code", shell=True)
            _bring_window_to_front(["visual studio code", "vscode"])
            return _result("VS Code opened.")

        elif "open chrome" in normalized_command:
            subprocess.run("start chrome", shell=True)
            _bring_window_to_front(["chrome", "google chrome", "new tab"])
            return _result("Chrome opened.")

        elif "open notepad" in normalized_command:
            subprocess.run("notepad", shell=True)
            _bring_window_to_front(["notepad"])
            return _result("Notepad opened.")

        elif "open explorer" in normalized_command or "open files" in normalized_command:
            subprocess.run("explorer", shell=True)
            _bring_window_to_front(["file explorer", "explorer"])
            return _result("File Explorer opened.")

        elif "open task manager" in normalized_command:
            subprocess.run("taskmgr", shell=True)
            _bring_window_to_front(["task manager"])
            return _result("Task Manager opened.")

        elif _get_video_index(normalized_command) is not None:
            index = _get_video_index(normalized_command)
            return play_video(index)

        elif normalized_command.startswith("play ") and "youtube" not in normalized_command:
            try:
                index = int(normalized_command.split()[1]) - 1
                return play_video(index)
            except Exception:
                return _result("Invalid selection")

        elif re.fullmatch(r"open\s+\d+", normalized_command):
            try:
                index = int(normalized_command.split()[1]) - 1
                return play_video(index)
            except Exception:
                return _result("Invalid selection")

        elif "youtube" in normalized_command:
            query = _extract_youtube_play_query(raw_command)
            if query:
                try:
                    results = search_youtube(query)
                except requests.RequestException as exc:
                    LAST_RESULTS = []
                    return _result(f"YouTube API request failed: {exc}")
                except RuntimeError as exc:
                    LAST_RESULTS = []
                    return _result(f"YouTube search is not available: {exc}")
                except Exception as exc:
                    LAST_RESULTS = []
                    return _result(f"Failed to search YouTube: {exc}")

                if not results:
                    LAST_RESULTS = []
                    return _result("No results found")

                LAST_RESULTS = results
                url = (
                    "https://www.youtube.com/results?search_query="
                    f"{quote_plus(query)}"
                )
                webbrowser.open(url)
                _bring_window_to_front(["youtube", "edge", "chrome"])
                return {
                    "result": f"YouTube results for '{query}'. Say which to play.",
                    "options": [result["title"] for result in results],
                }

            webbrowser.open("https://www.youtube.com")
            _bring_window_to_front(["youtube", "edge", "chrome"])
            return _result("YouTube opened.")

        elif "search" in normalized_command and "youtube" not in normalized_command:
            query = raw_command.lower().replace("search", "").strip()
            
            noise_phrases = [
                "on chrome",
                "on google", 
                "in chrome",
                "in google",
                "in browser",
                "on browser",
                "using chrome",
                "using google",
                "on the internet",
                "on internet",
                "on web",
                "on the web",
            ]
            
            for phrase in noise_phrases:
                if query.endswith(phrase):
                    query = query.replace(phrase, "").strip()
                query = query.replace(phrase, "").strip()
            
            query = " ".join(query.split()).strip()
            
            if query:
                url = (
                    f"https://www.google.com/search?q="
                    f"{quote_plus(query)}"
                )
                webbrowser.open(url)
                _bring_window_to_front(["chrome", "edge", "google"])
                return _result(f"Searching Google for '{query}' \U0001f50d")
            else:
                webbrowser.open("https://www.google.com")
                _bring_window_to_front(["chrome", "edge"])
                return _result("Google opened \u2705")

        elif "screenshot" in normalized_command or "take screenshot" in normalized_command:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(desktop, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            subprocess.run(f'explorer "{desktop}"', shell=True)
            _bring_window_to_front(["file explorer", "explorer", "desktop"])
            return _result("Screenshot saved to Desktop.")

        elif "move cursor to center" in normalized_command:
            width, height = pyautogui.size()
            pyautogui.moveTo(width // 2, height // 2)
            return _result("Cursor moved to center.")

        elif "move cursor to top left" in normalized_command:
            pyautogui.moveTo(0, 0)
            return _result("Cursor moved to top-left.")

        elif "move cursor to top right" in normalized_command:
            width, _ = pyautogui.size()
            pyautogui.moveTo(width, 0)
            return _result("Cursor moved to top-right.")

        elif "move cursor to bottom left" in normalized_command:
            _, height = pyautogui.size()
            pyautogui.moveTo(0, height)
            return _result("Cursor moved to bottom-left.")

        elif "move cursor to bottom right" in normalized_command:
            width, height = pyautogui.size()
            pyautogui.moveTo(width, height)
            return _result("Cursor moved to bottom-right.")

        elif "move cursor to" in normalized_command:
            nums = re.findall(r"\d+", raw_command)
            if len(nums) >= 2:
                x, y = int(nums[0]), int(nums[1])
                pyautogui.moveTo(x, y)
                return _result(f"Cursor moved to ({x}, {y}).")
            return _result("Could not parse coordinates. Say 'move cursor to 500 300'.")

        elif "click at" in normalized_command:
            nums = re.findall(r"\d+", raw_command)
            if len(nums) >= 2:
                x, y = int(nums[0]), int(nums[1])
                pyautogui.click(x, y)
                return _result(f"Clicked at ({x}, {y}).")
            return _result("Could not parse coordinates. Say 'click at 500 300'.")

        elif "double click" in normalized_command:
            pyautogui.doubleClick()
            return _result("Double-clicked.")

        elif "right click" in normalized_command:
            pyautogui.rightClick()
            return _result("Right-clicked.")

        elif normalized_command == "click":
            pyautogui.click()
            return _result("Clicked.")

        elif normalized_command.startswith("type "):
            text = raw_command[5:].strip()
            pyautogui.typewrite(text, interval=0.05)
            return _result(f"Typed: '{text}'.")

        elif normalized_command.startswith("write "):
            text = raw_command[6:].strip()
            pyautogui.typewrite(text, interval=0.05)
            return _result(f"Written: '{text}'.")

        elif "press ctrl c" in normalized_command:
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.3)
            return _result("Pressed Ctrl+C.")

        elif "press ctrl v" in normalized_command:
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
            return _result("Pressed Ctrl+V.")

        elif "press ctrl s" in normalized_command:
            pyautogui.hotkey("ctrl", "s")
            time.sleep(0.3)
            return _result("Pressed Ctrl+S.")

        elif "press ctrl z" in normalized_command:
            pyautogui.hotkey("ctrl", "z")
            time.sleep(0.3)
            return _result("Pressed Ctrl+Z.")

        elif "press ctrl a" in normalized_command:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.3)
            return _result("Pressed Ctrl+A.")

        elif "press alt tab" in normalized_command:
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.3)
            return _result("Pressed Alt+Tab.")

        elif "press alt f4" in normalized_command:
            pyautogui.hotkey("alt", "f4")
            time.sleep(0.3)
            return _result("Pressed Alt+F4.")

        elif "press win d" in normalized_command:
            pyautogui.hotkey("win", "d")
            time.sleep(0.3)
            return _result("Pressed Win+D.")

        elif "press enter" in normalized_command:
            pyautogui.press("enter")
            return _result("Pressed Enter.")

        elif "press escape" in normalized_command:
            pyautogui.press("escape")
            return _result("Pressed Escape.")

        elif "press space" in normalized_command:
            pyautogui.press("space")
            return _result("Pressed Space.")

        elif "press tab" in normalized_command:
            pyautogui.press("tab")
            return _result("Pressed Tab.")

        elif "press backspace" in normalized_command:
            pyautogui.press("backspace")
            return _result("Pressed Backspace.")

        elif "press delete" in normalized_command:
            pyautogui.press("delete")
            return _result("Pressed Delete.")

        elif "scroll up" in normalized_command:
            nums = re.findall(r"\d+", raw_command)
            amount = int(nums[0]) if nums else 3
            pyautogui.scroll(amount)
            return _result(f"Scrolled up {amount}.")

        elif "scroll down" in normalized_command:
            nums = re.findall(r"\d+", raw_command)
            amount = int(nums[0]) if nums else 3
            pyautogui.scroll(-amount)
            return _result(f"Scrolled down {amount}.")

        elif "focus chrome" in normalized_command:
            _bring_window_to_front(["chrome"])
            return _result("Chrome focused.")

        elif "focus edge" in normalized_command:
            _bring_window_to_front(["edge"])
            return _result("Edge focused.")

        elif "focus vscode" in normalized_command:
            _bring_window_to_front(["visual studio code", "vscode"])
            return _result("VS Code focused.")

        elif "focus notepad" in normalized_command:
            _bring_window_to_front(["notepad"])
            return _result("Notepad focused.")

        elif "focus terminal" in normalized_command:
            _bring_window_to_front(
                ["cmd", "powershell", "terminal", "command prompt"]
            )
            return _result("Terminal focused.")

        elif "switch window" in normalized_command:
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.3)
            return _result("Switched window.")

        elif "minimize window" in normalized_command:
            pyautogui.hotkey("win", "down")
            time.sleep(0.3)
            return _result("Window minimized.")

        elif "maximize window" in normalized_command:
            pyautogui.hotkey("win", "up")
            time.sleep(0.3)
            return _result("Window maximized.")

        elif "close window" in normalized_command:
            pyautogui.hotkey("alt", "f4")
            time.sleep(0.3)
            return _result("Window closed.")

        elif "show desktop" in normalized_command:
            pyautogui.hotkey("win", "d")
            time.sleep(0.3)
            return _result("Desktop shown.")

        elif "create folder" in normalized_command:
            folder_name = "NewFolder"
            named_match = re.search(
                r"(?:named|called)\s+(.+)$",
                raw_command,
                flags=re.IGNORECASE,
            )
            if named_match:
                folder_name = named_match.group(1).strip()

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop, folder_name)
            os.makedirs(path, exist_ok=True)
            subprocess.run(f'explorer "{desktop}"', shell=True)
            _bring_window_to_front(["file explorer", "explorer", "desktop"])
            return _result(f"Folder '{folder_name}' created on Desktop.")

        elif "create react app" in normalized_command:
            app_name = "my-app"
            named_match = re.search(
                r"(?:named|called)\s+(.+)$",
                raw_command,
                flags=re.IGNORECASE,
            )
            if named_match:
                app_name = named_match.group(1).strip().replace(" ", "-")

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            subprocess.Popen(
                f"start cmd /k npx create-react-app {app_name}",
                shell=True,
                cwd=desktop,
            )
            _bring_window_to_front(["cmd", "command prompt", "terminal"])
            return _result(f"Creating React app '{app_name}' on Desktop.")

        elif "create python project" in normalized_command:
            project_name = "my_python_project"
            named_match = re.search(
                r"(?:named|called)\s+(.+)$",
                raw_command,
                flags=re.IGNORECASE,
            )
            if named_match:
                project_name = named_match.group(1).strip().replace(" ", "_")

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            project_path = os.path.join(desktop, project_name)
            os.makedirs(project_path, exist_ok=True)

            with open(
                os.path.join(project_path, "main.py"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write('# Main Python file\n\nprint("Hello World")\n')

            with open(
                os.path.join(project_path, "README.md"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write(f"# {project_name}\n\nCreated by FlowForge AI")

            subprocess.Popen(f'code "{project_path}"', shell=True)
            _bring_window_to_front(["visual studio code", "vscode"])
            return _result(
                f"Python project '{project_name}' created and opened in VS Code."
            )

        elif any(
            trigger in normalized_command
            for trigger in [
                "create ai project",
                "create project for",
                "build me",
                "make me a",
                "create a",
            ]
        ):
            description, project_name = parse_create_command(raw_command)
            if description:
                return _result(create_ai_project(description, project_name))
            return _result(
                "Please specify what project to create.\n"
                "Example: 'create ai project for a snake game in python'"
            )

        elif "start coding session" in normalized_command:
            subprocess.run("code", shell=True)
            subprocess.run("start chrome", shell=True)
            folder_path = os.path.join(
                os.path.expanduser("~"), "Desktop", "TodayWork"
            )
            os.makedirs(folder_path, exist_ok=True)
            _bring_window_to_front(["visual studio code", "vscode"])
            return _result(
                "Coding session started. "
                "VS Code and Chrome opened, TodayWork folder created."
            )

        elif "play music" in normalized_command or "play song" in normalized_command:
            subprocess.run("start wmplayer", shell=True)
            _bring_window_to_front(["windows media player", "wmplayer"])
            return _result("Music player opened.")

        elif "shutdown" in normalized_command:
            subprocess.run("shutdown /s /t 5", shell=True)
            return _result("PC will shut down in 5 seconds.")

        elif "restart" in normalized_command:
            subprocess.run("shutdown /r /t 5", shell=True)
            return _result("PC will restart in 5 seconds.")

        return _result(f"Command not recognized: '{raw_command}'")

    except Exception as exc:
        return _result(f"System error: {exc}")