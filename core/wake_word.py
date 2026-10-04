import re
from typing import Callable, List, Optional, Tuple

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class WakeWordDetector:
    def __init__(
        self,
        config: dict,
        on_activation: Callable[[str], None],
        on_text_activation: Optional[Callable[[], None]] = None
    ):
        self.config = config
        gen_cfg = config.get("general", {})
        self.wake_words: List[str] = [w.lower().strip() for w in gen_cfg.get("wake_words", ["hey nova", "nova ơi", "nova"])]
        self.hotkey: str = gen_cfg.get("activation_hotkey", "ctrl+space")
        self.text_hotkey: str = gen_cfg.get("text_activation_hotkey", "ctrl+shift+space")
        self.on_activation = on_activation
        self.on_text_activation = on_text_activation

    def start_hotkey_listener(self):
        """Register system-wide global hotkeys for voice and text chat."""
        if not KEYBOARD_AVAILABLE:
            print("[WakeWord Warning] Thư viện keyboard chưa sẵn sàng")
            return

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            print(f"[WakeWord] Phím tắt giọng nói: {self.hotkey}")
        except Exception as e:
            print(f"[WakeWord Hotkey Error] {e}")

        if self.on_text_activation:
            try:
                keyboard.add_hotkey(self.text_hotkey, self._on_text_hotkey_pressed)
                print(f"[WakeWord] Phím tắt thanh chat Spotlight: {self.text_hotkey}")
            except Exception as e:
                print(f"[Text Hotkey Error] {e}")

    def _on_hotkey_pressed(self):
        print(f"[WakeWord] Phím tắt giọng nói {self.hotkey} được nhấn!")
        self.on_activation("hotkey")

    def _on_text_hotkey_pressed(self):
        print(f"[WakeWord] Phím tắt thanh chat {self.text_hotkey} được nhấn!")
        if self.on_text_activation:
            self.on_text_activation()

    def check_wake_word_in_text(self, text: str) -> Tuple[bool, str]:
        """
        Check if any wake word exists in transcribed text.
        If found, returns (True, command_after_wake_word).
        """
        lower = text.strip().lower()
        for ww in self.wake_words:
            pattern = r"(?:^|\b)" + re.escape(ww) + r"(?:\b|$)"
            match = re.search(pattern, lower)
            if match:
                end_pos = match.end()
                remainder = lower[end_pos:].strip()
                remainder = re.sub(r"^[\s,.:;!?-]+", "", remainder)
                return True, remainder
        return False, text
