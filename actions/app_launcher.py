import os
import shutil
import subprocess
import urllib.parse
import webbrowser
import re
import winreg
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
    
    # Dev & Tools
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "git": "git-bash",
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
    
    # Desktop Apps
    "spotify": "spotify",
    "zalo": "zalo",
    "telegram": "telegram",
    "discord": "discord",
    "steam": "steam",
    
    # Websites & Online Services
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "chatgpt": "https://chatgpt.com",
    "tiktok": "https://www.tiktok.com",
    "gmail": "https://mail.google.com",
    "drive": "https://drive.google.com",
    "netflix": "https://www.netflix.com",
    "reddit": "https://www.reddit.com",
    "shopee": "https://shopee.vn",
    "lazada": "https://lazada.vn",
    "canva": "https://www.canva.com",
    "dantri": "https://dantri.com.vn",
    "vnexpress": "https://vnexpress.net"
}


def clean_target_name(name: str) -> str:
    """Strip filler words like 'trang web', 'ứng dụng', 'cho tôi', etc."""
    cleaned = name.strip().lower()
    # Remove polite phrases
    cleaned = re.sub(r"^(?:hãy\s+|làm ơn\s+|cho tôi\s+|cho mình\s+|giúp tôi\s+|giùm tôi\s+|hộ tôi\s+|hộ mình\s+|vui lòng\s+)", "", cleaned)
    # Remove app/web prefix fillers
    cleaned = re.sub(r"^(?:trang web\s+|trang\s+|web\s+|website\s+|ứng dụng\s+|phần mềm\s+|app\s+)", "", cleaned)
    # Remove trailing platform references
    cleaned = re.sub(r"\s+(?:trên|qua|ở|tại|bằng|on)\s+(?:youtube|google|web|mạng)$", "", cleaned, flags=re.IGNORECASE)
    # Remove trailing words
    cleaned = re.sub(r"\s+(?:lên|đi|giùm|hộ|nào)$", "", cleaned)
    return cleaned.strip()


def _find_app_path(target: str) -> Optional[str]:
    """Find absolute path of an application via filesystem, PATH, or Windows Registry."""
    # 1. Full path exists
    if os.path.exists(target):
        return target

    # 2. Check PATH with PATHEXT
    w = shutil.which(target)
    if w:
        return w
    if not target.endswith((".exe", ".cmd", ".bat")):
        w = shutil.which(f"{target}.exe")
        if w:
            return w

    # 3. Check Windows Registry App Paths (HKCU and HKLM)
    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        for subkey in [f"{target}.exe", target]:
            try:
                key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{subkey}"
                with winreg.OpenKey(root, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    if val and os.path.exists(val):
                        return val
            except OSError:
                pass
    return None


def open_application(app_name: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """Launch an application or web service by name with smart resolution."""
    raw_name = clean_target_name(app_name)

    # Detect if user specified browser: 'mở youtube bằng chrome'
    browser_match = re.search(r"^(.*?)\s+(?:bằng|qua|trên|với|in|with)\s+(chrome|cốc cốc|coc coc|edge|firefox)$", raw_name)
    if browser_match:
        raw_name = clean_target_name(browser_match.group(1))
        specific_browser = browser_match.group(2).strip()

    target = APP_ALIASES.get(raw_name, raw_name)

    # 1. Opening a Website URL
    if target.startswith("http://") or target.startswith("https://"):
        return _open_url(target, raw_name, specific_browser)

    # 2. Windows Settings URI
    if target.startswith("ms-settings:"):
        try:
            os.startfile(target)
            return True, "Đang mở Cài đặt Windows"
        except Exception as e:
            return False, f"Không thể mở Cài đặt: {e}"

    # 3. Known web domain pattern (e.g. 'nhaccuatui.com' or single known word)
    if "." in raw_name and not raw_name.endswith((".exe", ".bat", ".cmd", ".ps1")):
        url = raw_name if raw_name.startswith("http") else f"https://{raw_name}"
        return _open_url(url, raw_name, specific_browser)

    # 4. Desktop Application Executable
    resolved = _find_app_path(target)
    if resolved:
        try:
            os.startfile(resolved)
            return True, f"Đang mở {raw_name}"
        except Exception as e:
            return False, f"Lỗi khi mở {raw_name}: {e}"

    # Try direct startfile for shell URIs or special handlers
    try:
        os.startfile(target)
        return True, f"Đang mở {raw_name}"
    except (FileNotFoundError, OSError):
        pass

    # 5. Fallback: Not a known app or file -> search Google smoothly without OS popups!
    search_google(raw_name, specific_browser)
    return True, f"Không tìm thấy ứng dụng '{raw_name}', đang tìm kiếm trên Google..."


def _open_url(url: str, label: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    if specific_browser:
        browser_cmd = APP_ALIASES.get(specific_browser, specific_browser)
        try:
            subprocess.Popen(f'start {browser_cmd} "{url}"', shell=True)
            return True, f"Đang mở {label} qua {specific_browser}"
        except Exception:
            webbrowser.open(url)
            return True, f"Đang mở {label}"
    else:
        webbrowser.open(url)
        return True, f"Đang mở {label}"


def search_google(query: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """Search Google with clean query."""
    clean_q = query.strip()
    clean_q = re.sub(r"\s+(?:trên|qua|ở|tại|bằng|on)\s+(?:google|youtube|web|mạng)$", "", clean_q, flags=re.IGNORECASE)
    clean_q = re.sub(r"^(?:thông tin về|về|cho tôi|giùm tôi)\s+", "", clean_q, flags=re.IGNORECASE)
    clean_q = clean_q.strip()
    if not clean_q:
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_q)}"
    return _open_url(url, f"Google: '{clean_q}'", specific_browser)


def search_youtube(query: str, specific_browser: Optional[str] = None) -> Tuple[bool, str]:
    """Search YouTube with clean query."""
    clean_q = query.strip()
    clean_q = re.sub(r"\s+(?:trên|qua|ở|tại|bằng|on)\s+(?:youtube|google|web|mạng)$", "", clean_q, flags=re.IGNORECASE)
    clean_q = re.sub(r"^(?:bài hát|bản nhạc|ca khúc|bài|video|clip|kênh|về|cho tôi)\s+", "", clean_q, flags=re.IGNORECASE)
    clean_q = clean_q.strip()
    if not clean_q:
        return False, "Nội dung tìm kiếm trống"
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"
    return _open_url(url, f"YouTube: '{clean_q}'", specific_browser)
