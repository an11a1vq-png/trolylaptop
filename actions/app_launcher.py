import os
import subprocess
import urllib.parse
import webbrowser
import re
from typing import Tuple, Optional

APP_ALIASES = {
    # Browsers
    "chrome": "chrome",
    "google chrome": "chrome",
    "cốc cốc": "coc_coc",
    "coc coc": "coc_coc",
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
    # Media & Websites
    "spotify": "spotify",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
}


def open_application(app_name: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """
    Launch an application or web service by name.
    Supports opening websites directly or via a specific browser.
    """
    raw_name = app_name.strip().lower()

    # Detect if user said 'mở youtube bằng chrome' or 'qua chrome'
    browser_match = re.search(r"^(.*?)\s+(?:bằng|qua|trên|với|in|with)\s+(chrome|cốc cốc|coc coc|edge|firefox)$", raw_name)
    if browser_match:
        raw_name = browser_match.group(1).strip()
        specific_browser = browser_match.group(2).strip()

    target = APP_ALIASES.get(raw_name, raw_name)

    # 1. Opening a Website
    if target.startswith("http://") or target.startswith("https://"):
        if specific_browser:
            browser_cmd = APP_ALIASES.get(specific_browser, specific_browser)
            try:
                subprocess.Popen(f'start {browser_cmd} "{target}"', shell=True)
                return True, f"Đang mở {raw_name} qua {specific_browser}"
            except Exception:
                webbrowser.open(target)
                return True, f"Đang mở {raw_name}"
        else:
            webbrowser.open(target)
            return True, f"Đang mở {raw_name}"

    # 2. Windows Settings URI
    if target.startswith("ms-settings:"):
        os.system(f"start {target}")
        return True, "Đang mở Cài đặt Windows"

    # 3. Desktop Application Executable
    try:
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return True, f"Đang mở {raw_name}"
    except Exception as e:
        return False, f"Không thể mở {raw_name}: {e}"


def search_google(query: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """Search Google with the given query."""
    if not query.strip():
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    if specific_browser:
        browser_cmd = APP_ALIASES.get(specific_browser, specific_browser)
        try:
            subprocess.Popen(f'start {browser_cmd} "{url}"', shell=True)
            return True, f"Đang tìm kiếm '{query}' trên Google qua {specific_browser}"
        except Exception:
            webbrowser.open(url)
    else:
        webbrowser.open(url)
    return True, f"Đang tìm kiếm '{query}' trên Google"


def search_youtube(query: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """Search YouTube with the given query."""
    if not query.strip():
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    if specific_browser:
        browser_cmd = APP_ALIASES.get(specific_browser, specific_browser)
        try:
            subprocess.Popen(f'start {browser_cmd} "{url}"', shell=True)
            return True, f"Đang tìm kiếm '{query}' trên YouTube qua {specific_browser}"
        except Exception:
            webbrowser.open(url)
    else:
        webbrowser.open(url)
    return True, f"Đang tìm kiếm '{query}' trên YouTube"
