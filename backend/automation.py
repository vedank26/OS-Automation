import subprocess
import os
import webbrowser
import urllib.request
import urllib.parse
import re

# ─────────────────────────────────────────
# Store search results temporarily
# so user can pick which video to play
# ─────────────────────────────────────────
_last_search_results = []


def execute_command(command: str):
    global _last_search_results
    command = command.lower().strip()

    # ─────────────────────────────────────────
    # 🖥️ APPS
    # ─────────────────────────────────────────

    if "open vscode" in command:
        subprocess.run("code", shell=True)
        return "VS Code opened ✅"

    elif "open chrome" in command:
        subprocess.run("start chrome", shell=True)
        return "Chrome opened ✅"

    elif "open notepad" in command:
        subprocess.run("notepad", shell=True)
        return "Notepad opened ✅"

    elif "open explorer" in command or "open files" in command:
        subprocess.run("explorer", shell=True)
        return "File Explorer opened ✅"

    elif "open task manager" in command:
        subprocess.run("taskmgr", shell=True)
        return "Task Manager opened ✅"

    # ─────────────────────────────────────────
    # 🎯 USER PICKS VIDEO NUMBER
    # ─────────────────────────────────────────
    # After search results show, user says:
    # "play 1" / "play 2" / "play 3"
    # "first" / "second" / "third"
    # "play first one" / "play second video"
    # "1" / "2" / "3"

    elif _last_search_results and (
        command.strip() in ["1", "2", "3", "4", "5"]
        or "play 1" in command
        or "play 2" in command
        or "play 3" in command
        or "play 4" in command
        or "play 5" in command
        or "first" in command
        or "second" in command
        or "third" in command
        or "fourth" in command
        or "fifth" in command
        or "play first" in command
        or "play second" in command
        or "play third" in command
    ):
        # Figure out which number user wants
        index = _get_video_index(command)

        if index is not None and index < len(_last_search_results):
            video = _last_search_results[index]
            video_url = (
                f"https://www.youtube.com/watch?v={video['id']}"
                f"&autoplay=1"
            )
            webbrowser.open(video_url)
            title = video['title']
            return f"▶️ Playing video {index + 1}: '{title}'"
        else:
            return (
                f"❌ Only {len(_last_search_results)} videos found. "
                f"Say 'play 1' to 'play {len(_last_search_results)}'"
            )

    # ─────────────────────────────────────────
    # ▶️ YOUTUBE SEARCH + SHOW RESULTS
    # ─────────────────────────────────────────
    # Commands:
    # "play kantara on youtube"
    # "play python tutorial on youtube"
    # "youtube play mr beast"
    # "play on youtube: lofi music"

    elif (
        ("play" in command and "youtube" in command)
        or "play on youtube" in command
        or "youtube play" in command
    ):
        query = ""

        if "play on youtube:" in command:
            query = command.split("play on youtube:")[-1].strip()

        elif "play on youtube" in command:
            query = command.split("play on youtube")[-1].strip()

        elif "youtube play" in command:
            query = command.split("youtube play")[-1].strip()

        elif "play" in command and "on youtube" in command:
            after_play = command.split("play")[-1].strip()
            query = after_play.split("on youtube")[0].strip()

        elif "play" in command and "youtube" in command:
            after_play = command.split("play")[-1].strip()
            query = after_play.replace("youtube", "").strip()

        # Clean filler words
        filler_words = ["on", "the", "a", "an", "in", "at"]
        query_words = [w for w in query.split() if w not in filler_words]
        query = " ".join(query_words).strip()

        if query:
            # Fetch top 5 results and show to user
            results = _get_youtube_results(query, count=5)

            if results:
                # Save results so user can pick
                _last_search_results = results

                # Build response showing all options
                response = f"🎬 Found {len(results)} videos for '{query}':\n\n"
                for i, video in enumerate(results):
                    response += f"{i + 1}. {video['title']}\n"
                response += (
                    "\n👉 Say 'play 1', 'play 2', 'play 3'... "
                    "or 'first', 'second', 'third' to play"
                )
                return response
            else:
                # Fallback to search page
                url = (
                    f"https://www.youtube.com/results?search_query="
                    f"{query.replace(' ', '+')}"
                )
                webbrowser.open(url)
                return f"Opened YouTube search for '{query}' 🎬"
        else:
            webbrowser.open("https://www.youtube.com")
            return "YouTube opened ✅"

    # ─────────────────────────────────────────
    # 🎬 YOUTUBE SEARCH ONLY (no play)
    # ─────────────────────────────────────────

    elif "youtube" in command:
        query = ""

        if "youtube search" in command:
            query = command.split("youtube search")[-1].strip()

        elif "search on youtube" in command:
            query = command.split("search on youtube")[-1].strip()

        elif "search youtube for" in command:
            query = command.split("search youtube for")[-1].strip()

        elif "find on youtube" in command:
            query = command.split("find on youtube")[-1].strip()

        else:
            after_youtube = command.split("youtube")[-1].strip()
            for word in ["search", "for", "find", "open", ":"]:
                after_youtube = after_youtube.replace(word, "").strip()
            query = after_youtube

        if query:
            url = (
                f"https://www.youtube.com/results?search_query="
                f"{query.replace(' ', '+')}"
            )
            webbrowser.open(url)
            return f"Searching YouTube for '{query}' 🎬"
        else:
            webbrowser.open("https://www.youtube.com")
            return "YouTube opened ✅"

    # ─────────────────────────────────────────
    # 🔍 GOOGLE SEARCH
    # ─────────────────────────────────────────

    elif "search" in command:
        query = command.replace("search", "").strip()
        if query:
            url = (
                f"https://www.google.com/search?q="
                f"{query.replace(' ', '+')}"
            )
            webbrowser.open(url)
            return f"Searching Google for '{query}' 🔍"
        else:
            webbrowser.open("https://www.google.com")
            return "Google opened ✅"

    # ─────────────────────────────────────────
    # 📁 FILE & PROJECT CREATION
    # ─────────────────────────────────────────

    elif "create folder" in command:
        if "named" in command:
            folder_name = command.split("named")[-1].strip()
        elif "called" in command:
            folder_name = command.split("called")[-1].strip()
        else:
            folder_name = "NewFolder"

        path = os.path.join(os.path.expanduser("~"), "Desktop", folder_name)
        os.makedirs(path, exist_ok=True)
        return f"Folder '{folder_name}' created on Desktop 📁"

    elif "create react app" in command:
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
        return f"Creating React app '{app_name}' on Desktop... ⚛️"

    elif "create python project" in command:
        if "named" in command:
            project_name = command.split("named")[-1].strip().replace(" ", "_")
        elif "called" in command:
            project_name = command.split("called")[-1].strip().replace(" ", "_")
        else:
            project_name = "my_python_project"

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_path = os.path.join(desktop, project_name)
        os.makedirs(project_path, exist_ok=True)

        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write('# Main Python file\n\nprint("Hello World")\n')

        with open(os.path.join(project_path, "README.md"), "w") as f:
            f.write(f"# {project_name}\n\nCreated by FlowForge AI 🚀")

        subprocess.Popen(f"code {project_path}", shell=True)
        return f"Python project '{project_name}' created and opened in VS Code 🐍"

    # ─────────────────────────────────────────
    # ⚡ WORKFLOW COMMANDS
    # ─────────────────────────────────────────

    elif "start coding session" in command:
        subprocess.run("code", shell=True)
        subprocess.run("start chrome", shell=True)
        folder_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "TodayWork"
        )
        os.makedirs(folder_path, exist_ok=True)
        return (
            "Coding session started ⚡ "
            "VS Code + Chrome opened, TodayWork folder created"
        )

    # ─────────────────────────────────────────
    # 🎵 LOCAL MUSIC PLAYER
    # ─────────────────────────────────────────

    elif "play music" in command or "play song" in command:
        subprocess.run("start wmplayer", shell=True)
        return "Music player opened ✅"

    # ─────────────────────────────────────────
    # 💻 SYSTEM COMMANDS
    # ─────────────────────────────────────────

    elif "shutdown" in command:
        subprocess.run("shutdown /s /t 5", shell=True)
        return "PC will shutdown in 5 seconds ⚠️"

    elif "restart" in command:
        subprocess.run("shutdown /r /t 5", shell=True)
        return "PC will restart in 5 seconds ⚠️"

    # ─────────────────────────────────────────
    # ❌ NOT RECOGNIZED
    # ─────────────────────────────────────────

    else:
        return f"❌ Command not recognized: '{command}'"


# ─────────────────────────────────────────
# 🔧 HELPER — Get YouTube search results
# Returns list of videos with title + id
# ─────────────────────────────────────────

def _get_youtube_results(query: str, count: int = 5):
    try:
        search_url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(query)
        )

        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )
        response = urllib.request.urlopen(req, timeout=5)
        html = response.read().decode("utf-8")

        # Extract video IDs
        video_ids = re.findall(
            r'"videoId":"([a-zA-Z0-9_-]{11})"', html
        )

        # Extract video titles
        video_titles = re.findall(
            r'"title":\{"runs":\[\{"text":"([^"]+)"',
            html
        )

        # Remove duplicates
        seen_ids = []
        results = []

        for i, vid in enumerate(video_ids):
            if vid not in seen_ids:
                seen_ids.append(vid)
                title = (
                    video_titles[len(seen_ids) - 1]
                    if len(seen_ids) - 1 < len(video_titles)
                    else f"Video {len(seen_ids)}"
                )
                results.append({
                    "id": vid,
                    "title": title
                })

            if len(results) >= count:
                break

        return results

    except Exception:
        return []


# ─────────────────────────────────────────
# 🔧 HELPER — Convert word to index number
# "first" → 0, "play 2" → 1, "third" → 2
# ─────────────────────────────────────────

def _get_video_index(command: str) -> int:
    # Word to number mapping
    word_map = {
        "first":   0,
        "1":       0,
        "play 1":  0,
        "second":  1,
        "2":       1,
        "play 2":  1,
        "third":   2,
        "3":       2,
        "play 3":  2,
        "fourth":  3,
        "4":       3,
        "play 4":  3,
        "fifth":   4,
        "5":       4,
        "play 5":  4,
    }

    for key, index in word_map.items():
        if key in command:
            return index

    return None