import os
import subprocess
import urllib.parse
import webbrowser
from typing import Tuple

APP_ALIASES = {
    # Browsers
    "chrome": "chrome",
    "google chrome": "chrome",
    "cốc cốc": "coc_coc",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    # Tools & Dev
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "git": "git-bash",
    # Utilities
    "notepad": "notepad",
    "ghi chú": "notepad",
    "calculator": "calc",
    "máy tính": "calc",
    "file explorer": "explorer",
    "thư mục": "explorer",
    "task manager": "taskmgr",
    "quản lý tác vụ": "taskmgr",
    "cài đặt": "ms-settings:",
    "settings": "ms-settings:",
    # Office
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    # Media
    "spotify": "spotify",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
}


def open_application(app_name: str) -> Tuple[bool, str]:
    """Launch an application or web service by name."""
    clean_name = app_name.strip().lower()
    target = APP_ALIASES.get(clean_name, clean_name)

    if target.startswith("http://") or target.startswith("https://"):
        webbrowser.open(target)
        return True, f"Đang mở {app_name}"

    if target.startswith("ms-settings:"):
        os.system(f"start {target}")
        return True, f"Đang mở Cài đặt Windows"

    try:
        # Use Windows shell start
        os.system(f'start "" "{target}"')
        return True, f"Đang mở {app_name}"
    except Exception as e:
        return False, f"Không thể mở {app_name}: {e}"


def search_google(query: str) -> Tuple[bool, str]:
    """Search Google with the given query in default browser."""
    if not query.strip():
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return True, f"Đang tìm kiếm '{query}' trên Google"


def search_youtube(query: str) -> Tuple[bool, str]:
    """Search YouTube with the given query in default browser."""
    if not query.strip():
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return True, f"Đang tìm kiếm '{query}' trên YouTube"
