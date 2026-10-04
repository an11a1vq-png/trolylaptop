import os
import subprocess
from typing import Tuple

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False


def open_folder(folder_path: str) -> Tuple[bool, str]:
    """Open a folder in Windows File Explorer."""
    expanded_path = os.path.expandvars(os.path.expanduser(folder_path))
    if not os.path.exists(expanded_path):
        return False, f"Thư mục không tồn tại: {expanded_path}"
    try:
        os.system(f'explorer "{expanded_path}"')
        return True, f"Đã mở thư mục {expanded_path}"
    except Exception as e:
        return False, f"Lỗi mở thư mục: {e}"


def run_custom_script(script_name: str) -> Tuple[bool, str]:
    """Execute a user script located in d:\\ailap\\scripts."""
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
    script_path = os.path.join(scripts_dir, script_name)

    if not os.path.exists(script_path):
        return False, f"Không tìm thấy script: {script_name} trong thư mục scripts"

    try:
        if script_name.endswith(".py"):
            subprocess.Popen(["python", script_path], shell=True)
        elif script_name.endswith(".bat") or script_name.endswith(".cmd"):
            subprocess.Popen([script_path], shell=True)
        elif script_name.endswith(".ps1"):
            subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], shell=True)
        else:
            os.startfile(script_path)
        return True, f"Đang thực thi script: {script_name}"
    except Exception as e:
        return False, f"Lỗi chạy script: {e}"


def click_center_screen() -> Tuple[bool, str]:
    """Click at screen center."""
    if not PYAUTOGUI_AVAILABLE:
        return False, "pyautogui chưa sẵn sàng"
    w, h = pyautogui.size()
    pyautogui.click(w // 2, h // 2)
    return True, "Đã nhấp chuột giữa màn hình"
