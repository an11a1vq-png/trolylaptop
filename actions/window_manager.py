import os
import time
from datetime import datetime
from typing import Tuple

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False


def take_screenshot() -> Tuple[bool, str]:
    """Capture full screen and save to Pictures/Screenshots."""
    if not PYAUTOGUI_AVAILABLE:
        return False, "Thư viện chụp màn hình chưa sẵn sàng"
    try:
        user_pictures = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        os.makedirs(user_pictures, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(user_pictures, f"Screenshot_{timestamp}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return True, f"Đã chụp ảnh màn hình và lưu tại Pictures\\Screenshots"
    except Exception as e:
        return False, f"Lỗi chụp ảnh màn hình: {e}"


def minimize_all_windows() -> Tuple[bool, str]:
    """Show desktop by minimizing all windows (Win + D)."""
    if not PYAUTOGUI_AVAILABLE:
        return False, "Lỗi pyautogui"
    try:
        pyautogui.hotkey('win', 'd')
        return True, "Đã hiện màn hình chính (Desktop)"
    except Exception as e:
        return False, f"Lỗi: {e}"


def close_active_window() -> Tuple[bool, str]:
    """Close currently active window (Alt + F4)."""
    if not PYAUTOGUI_AVAILABLE:
        return False, "Lỗi pyautogui"
    try:
        pyautogui.hotkey('alt', 'f4')
        return True, "Đã đóng cửa sổ hiện tại"
    except Exception as e:
        return False, f"Lỗi: {e}"


def switch_window() -> Tuple[bool, str]:
    """Switch active window (Alt + Tab)."""
    if not PYAUTOGUI_AVAILABLE:
        return False, "Lỗi pyautogui"
    try:
        pyautogui.hotkey('alt', 'tab')
        return True, "Đã chuyển cửa sổ"
    except Exception as e:
        return False, f"Lỗi: {e}"
