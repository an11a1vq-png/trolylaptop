import os
import shutil
import subprocess
import urllib.parse
import webbrowser
import re
import winreg
import difflib
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
    "trình duyệt": "chrome",
    "browser": "chrome",
    
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
    
    # Windows Built-in UWP & Utilities
    "camera": "microsoft.windows.camera:",
    "máy ảnh": "microsoft.windows.camera:",
    "chụp hình": "microsoft.windows.camera:",
    "chụp ảnh": "microsoft.windows.camera:",
    "paint": "mspaint",
    "vẽ": "mspaint",
    "vẽ tranh": "mspaint",
    "photos": "ms-photos:",
    "ảnh": "ms-photos:",
    "xem ảnh": "ms-photos:",
    "album": "ms-photos:",
    "snipping tool": "snippingtool",
    "cắt màn hình": "snippingtool",
    "chụp vùng": "snippingtool",
    "clock": "ms-clock:",
    "đồng hồ": "ms-clock:",
    "báo thức": "ms-clock:",
    "hẹn giờ": "ms-clock:",
    "ghi âm": "ms-voice-recorder:",
    "voice recorder": "ms-voice-recorder:",
    "cửa hàng": "ms-windows-store:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",

    # Office
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "soạn thảo": "winword",
    "bảng tính": "excel",
    "trình chiếu": "powerpnt",
    
    # Desktop Apps & Games
    "spotify": "spotify",
    "nghe nhạc": "spotify",
    "zalo": "zalo",
    "telegram": "telegram",
    "discord": "discord",
    "steam": "steam",
    "goose goose duck": "Goose Goose Duck",
    "game ngỗng": "Goose Goose Duck",
    "ngỗng": "Goose Goose Duck",
    "vịt": "Goose Goose Duck",
    "ngỗng ngỗng vịt": "Goose Goose Duck",
    "lol": "League of Legends",
    "liên minh": "League of Legends",
    "liên minh huyền thoại": "League of Legends",
    "league of legends": "League of Legends",
    "tft": "Teamfight Tactics",
    "đấu trường chân lý": "Teamfight Tactics",
    "teamfight tactics": "Teamfight Tactics",
    "riot": "Riot Client",
    "riot client": "Riot Client",
    "ldplayer": "LDPlayer 9",
    "ld player": "LDPlayer 9",
    "giả lập": "LDPlayer 9",
    "foxit": "Foxit PhantomPDF",
    "foxit reader": "Foxit PhantomPDF",
    "pdf": "Foxit PhantomPDF",
    "winrar": "WinRAR",
    "giải nén": "WinRAR",
    "ultraviewer": "UltraViewer",
    "ultra view": "UltraViewer",
    "điều khiển từ xa": "UltraViewer",
    "control panel": "control",
    "bảng điều khiển": "control",
    "bàn phím ảo": "osk",
    "keyboard": "osk",
    "easyfun": "Easyfun",
    
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
    """Strip filler words like 'trang web', 'ứng dụng', 'cho tôi', 'chơi game', etc."""
    cleaned = name.strip().lower()
    # Remove polite phrases
    cleaned = re.sub(r"^(?:hãy\s+|làm ơn\s+|cho tôi\s+|cho mình\s+|giúp tôi\s+|giùm tôi\s+|hộ tôi\s+|hộ mình\s+|vui lòng\s+)", "", cleaned)
    # Remove app/web/game prefix fillers
    cleaned = re.sub(r"^(?:chơi\s+|mở\s+|bật\s+|vào\s+)?(?:game\s+|trò chơi\s+|ứng dụng\s+|phần mềm\s+|app\s+|trang web\s+|trang\s+|web\s+|website\s+)", "", cleaned)
    # Remove trailing platform references
    cleaned = re.sub(r"\s+(?:trên|qua|ở|tại|bằng|on)\s+(?:youtube|google|web|mạng)$", "", cleaned, flags=re.IGNORECASE)
    # Remove trailing words
    cleaned = re.sub(r"\s+(?:lên|đi|giùm|hộ|nào)$", "", cleaned)
    return cleaned.strip()


def _find_app_path(target: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Find absolute path of an application via filesystem, PATH, Windows Registry,
    or Desktop/Start Menu shortcuts with exact, substring, token overlap, and fuzzy matching.
    Returns: (resolved_path, matched_display_name)
    """
    # 0. Skip protocol URIs (e.g. microsoft.windows.camera:, ms-settings:)
    if ":" in target and not re.match(r"^[a-zA-Z]:[\\/]", target):
        return None, None

    # 1. Full path exists
    if os.path.exists(target):
        return target, os.path.basename(target)

    # 2. Check PATH with PATHEXT
    w = shutil.which(target)
    if w:
        return w, target
    if not target.endswith((".exe", ".cmd", ".bat")):
        w = shutil.which(f"{target}.exe")
        if w:
            return w, target

    # 3. Check Windows Registry App Paths (HKCU and HKLM)
    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        for subkey in [f"{target}.exe", target]:
            try:
                key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{subkey}"
                with winreg.OpenKey(root, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    if val and os.path.exists(val):
                        return val, target
            except OSError:
                pass

    # 4. Check Desktop and Start Menu Shortcuts (.lnk, .url for Steam/Epic games and Windows apps)
    norm_target = target.lower().strip()
    norm_clean = re.sub(r"^(?:game\s+|trò chơi\s+)", "", norm_target).strip()
    search_dirs = [
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        os.path.expandvars(r"%PUBLIC%\Desktop"),
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]

    all_shortcuts: dict[str, str] = {}
    display_names: dict[str, str] = {}

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        try:
            for root, _, files in os.walk(sdir):
                for f in files:
                    fname_no_ext, ext = os.path.splitext(f)
                    if ext.lower() in [".lnk", ".url"]:
                        key = fname_no_ext.lower().strip()
                        if key not in all_shortcuts:
                            all_shortcuts[key] = os.path.join(root, f)
                            display_names[key] = fname_no_ext
        except Exception:
            continue

    # A. Exact match
    if norm_target in all_shortcuts:
        return all_shortcuts[norm_target], display_names[norm_target]
    if norm_clean in all_shortcuts:
        return all_shortcuts[norm_clean], display_names[norm_clean]

    # B. Substring match
    for key, path in all_shortcuts.items():
        if norm_clean and (norm_clean in key or key in norm_clean):
            return path, display_names[key]

    # C. Token / Word-set overlap match (e.g. 'duck duck goose' matches 'Goose Goose Duck')
    STOP_WORDS = {"microsoft", "windows", "app", "the", "of", "for", "and", "a", "an", "pro", "64", "bit", "tool", "tools", "version", "edition"}
    query_str = norm_clean or norm_target
    target_tokens = set(re.findall(r"\w+", query_str))
    meaningful_target = target_tokens - STOP_WORDS or target_tokens

    if meaningful_target:
        for key, path in all_shortcuts.items():
            key_tokens = set(re.findall(r"\w+", key))
            meaningful_key = key_tokens - STOP_WORDS or key_tokens
            if meaningful_target.issubset(meaningful_key) or meaningful_key.issubset(meaningful_target):
                return path, display_names[key]
            intersection = len(meaningful_target & meaningful_key)
            if intersection > 0 and (intersection / len(meaningful_target) >= 0.6):
                return path, display_names[key]

    # D. Fuzzy string match (Find closest installed app name)
    close_matches = difflib.get_close_matches(norm_clean or norm_target, all_shortcuts.keys(), n=1, cutoff=0.55)
    if close_matches:
        best_key = close_matches[0]
        return all_shortcuts[best_key], display_names[best_key]

    return None, None


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

    # 2. Windows Settings URI or UWP Protocol URI (e.g. microsoft.windows.camera:, ms-settings:, ms-photos:)
    if target.startswith("ms-") or target.startswith("microsoft.") or ":" in target:
        try:
            os.startfile(target)
            return True, f"Đang mở {raw_name}"
        except Exception as e:
            pass

    # 3. Known web domain pattern (e.g. 'nhaccuatui.com' or single known word)
    if "." in raw_name and not raw_name.endswith((".exe", ".bat", ".cmd", ".ps1")):
        url = raw_name if raw_name.startswith("http") else f"https://{raw_name}"
        return _open_url(url, raw_name, specific_browser)

    # 4. Desktop Application Executable or Shortcut (with fuzzy matching)
    resolved, matched_name = _find_app_path(target)
    if resolved:
        try:
            os.startfile(resolved)
            display = matched_name if matched_name else raw_name
            return True, f"Đang mở {display}"
        except Exception as e:
            return False, f"Lỗi khi mở {raw_name}: {e}"

    # Try direct startfile for shell URIs or special handlers
    try:
        os.startfile(target)
        return True, f"Đang mở {raw_name}"
    except (FileNotFoundError, OSError):
        pass

    # 5. Fallback: Checked all apps, shortcuts, registry, and protocols -> none matched on PC
    search_google(raw_name, specific_browser)
    return True, f"Không tìm thấy ứng dụng hay phần mềm nào tương tự trên máy, đang tìm kiếm trên Google..."


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
