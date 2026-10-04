import re
import threading
from typing import Callable, List, Optional, Tuple

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class WakeWordDetector:
    def __init__(self, config: dict, on_activation: Callable[[str], None]):
        self.config = config
        gen_cfg = config.get("general", {})
        self.wake_words: List[str] = [w.lower().strip() for w in gen_cfg.get("wake_words", ["hey google", "trợ lý ơi"])]
        self.hotkey: str = gen_cfg.get("activation_hotkey", "ctrl+space")
        self.on_activation = on_activation
        self.is_registered = False

    def start_hotkey_listener(self):
        """Register system-wide global hotkey."""
        if not KEYBOARD_AVAILABLE:
            print("[WakeWord Warning] Thư viện keyboard chưa sẵn sàng")
            return

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            self.is_registered = True
            print(f"[WakeWord] Đã kích hoạt phím tắt toàn cầu: {self.hotkey}")
        except Exception as e:
            print(f"[WakeWord Hotkey Error] {e}")

    def _on_hotkey_pressed(self):
        print(f"[WakeWord] Phím tắt {self.hotkey} được nhấn!")
        self.on_activation("hotkey")

    def check_wake_word_in_text(self, text: str) -> Tuple[bool, str]:
        """
        Check if any wake word exists in transcribed text.
        If found, returns (True, command_after_wake_word).
        Example: "Hey Google mở YouTube" -> (True, "mở YouTube")
        Example: "Hey Google" -> (True, "")
        """
        lower = text.strip().lower()
        for ww in self.wake_words:
            # Pattern matching word boundary or start
            pattern = r"(?:^|\b)" + re.escape(ww) + r"(?:\b|$)"
            match = re.search(pattern, lower)
            if match:
                # Extract text after wake word
                end_pos = match.end()
                remainder = lower[end_pos:].strip()
                # Remove common leading punctuation
                remainder = re.sub(r"^[\s,.:;!?-]+", "", remainder)
                return True, remainder
        return False, text
