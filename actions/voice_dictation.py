import time
import ctypes
import subprocess
from typing import Tuple

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False


def _set_clipboard_text(text: str) -> bool:
    """Set text into Windows clipboard using ctypes/powershell without external dependencies."""
    try:
        # Powershell Set-Clipboard handles UTF-8 / Vietnamese characters accurately
        cmd = f"Set-Clipboard -Value @'\n{text}\n'@"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=True, creationflags=0x08000000)
        return True
    except Exception:
        return False


class VoiceDictationManager:
    def __init__(self):
        self.is_dictating = False

    def toggle(self) -> Tuple[bool, str]:
        self.is_dictating = not self.is_dictating
        if self.is_dictating:
            return True, "Chế độ gõ văn bản bằng giọng nói đã BẬT. Mọi câu bạn nói sẽ được gõ vào vị trí con trỏ chuột."
        else:
            return False, "Đã TẮT chế độ gõ văn bản bằng giọng nói."

    def type_text(self, text: str) -> bool:
        if not text.strip():
            return False
        # Add space after phrase
        formatted_text = text.strip() + " "
        try:
            if _set_clipboard_text(formatted_text):
                time.sleep(0.05)
                pyautogui.hotkey('ctrl', 'v')
                return True
            else:
                pyautogui.write(formatted_text)
                return True
        except Exception as e:
            print(f"[Dictation Error] {e}")
            return False

dictation_manager = VoiceDictationManager()
