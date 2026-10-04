import re
import unicodedata
from typing import Tuple, Optional

from actions.system_controls import (
    set_volume, change_volume, toggle_mute, lock_screen,
    shutdown_computer, restart_computer, cancel_shutdown
)
from actions.app_launcher import (
    open_application, search_google, search_youtube
)
from actions.window_manager import (
    take_screenshot, minimize_all_windows, close_active_window, switch_window
)
from actions.voice_dictation import dictation_manager
from actions.custom_scripts import open_folder, run_custom_script


def _normalize(text: str) -> str:
    """Normalize text by lowercasing and stripping extra whitespace."""
    return text.strip().lower()


class IntentRouter:
    def __init__(self, config: dict):
        self.config = config
        self.pending_confirmation: Optional[str] = None  # e.g. "shutdown", "restart"

    def route_text(self, text: str) -> Tuple[bool, str, str]:
        """
        Routes text input to either:
        1. An immediate rule-based action (returns: True, message, "action")
        2. Safety confirmation handler (returns: True, message, "confirm")
        3. Dictation input (returns: True, message, "dictation")
        4. Pass through to Hybrid Brain / LLM (returns: False, text, "llm")
        """
        raw_text = text.strip()
        norm = _normalize(raw_text)

        if not norm:
            return True, "", "empty"

        # 1. Handle Pending Confirmation (Safety mechanism)
        if self.pending_confirmation:
            action = self.pending_confirmation
            self.pending_confirmation = None
            yes_keywords = ["có", "xác nhận", "đồng ý", "yes", "chắc chắn", "ok", "được", "chắc"]
            no_keywords = ["không", "hủy", "thôi", "no", "cancel", "bỏ qua"]

            if any(k in norm for k in yes_keywords):
                if action == "shutdown":
                    success, msg = shutdown_computer(10)
                    return True, msg, "action"
                elif action == "restart":
                    success, msg = restart_computer(10)
                    return True, msg, "action"
            elif any(k in norm for k in no_keywords):
                return True, "Đã hủy thao tác theo yêu cầu của bạn.", "action"
            else:
                return True, "Không xác nhận được lệnh. Thao tác đã được hủy để đảm bảo an toàn.", "action"

        # 2. Check Dictation Mode Toggle
        if any(p in norm for p in ["bật gõ văn bản", "bật chế độ gõ", "start dictation", "bắt đầu gõ"]):
            dictation_manager.is_dictating = True
            return True, "Đã bật chế độ gõ văn bản bằng giọng nói. Bạn hãy nói, tôi sẽ gõ vào màn hình.", "action"

        if any(p in norm for p in ["tắt gõ văn bản", "dừng gõ văn bản", "stop dictation", "dừng gõ", "ngừng gõ"]):
            dictation_manager.is_dictating = False
            return True, "Đã tắt chế độ gõ văn bản.", "action"

        # If dictation is currently active, type it out directly!
        if dictation_manager.is_dictating:
            dictation_manager.type_text(raw_text)
            return True, f"Đã gõ: {raw_text}", "dictation"

        # 3. System Volume & Audio
        # Volume set specific percentage: "âm lượng 50", "set volume to 80"
        vol_match = re.search(r"(?:âm lượng|volume|âm thanh)\s*(?:thành|lên|về|to)?\s*(\d{1,3})", norm)
        if vol_match:
            val = int(vol_match.group(1))
            success, msg = set_volume(val)
            return True, msg, "action"

        if any(k in norm for k in ["tăng âm lượng", "tăng volume", "volume up", "to lên", "cho to lên", "bật to"]):
            success, msg = change_volume(10)
            return True, msg, "action"

        if any(k in norm for k in ["giảm âm lượng", "giảm volume", "volume down", "nhỏ lại", "cho nhỏ lại"]):
            success, msg = change_volume(-10)
            return True, msg, "action"

        if any(k in norm for k in ["tắt tiếng", "bật tiếng", "mute", "unmute", "im lặng"]):
            success, msg = toggle_mute()
            return True, msg, "action"

        # 4. Search Commands
        # Google search
        google_match = re.search(r"(?:tìm kiếm google|tìm google|search google for|tra google|google)\s+(.+)", norm)
        if google_match:
            query = google_match.group(1)
            success, msg = search_google(query)
            return True, msg, "action"

        # YouTube search
        youtube_match = re.search(r"(?:tìm kiếm youtube|mở youtube tìm|tìm trên youtube|search youtube for)\s+(.+)", norm)
        if youtube_match:
            query = youtube_match.group(1)
            success, msg = search_youtube(query)
            return True, msg, "action"

        # 5. Open Applications / Websites
        open_match = re.search(r"^(?:mở|bật|khởi động|chạy|open|launch)\s+(.+)", norm)
        if open_match:
            target = open_match.group(1).strip()
            # If target is folder
            if target in ["thư mục dự án", "project folder", "code"]:
                success, msg = open_folder("d:\\ailap")
                return True, msg, "action"
            # Launch app
            success, msg = open_application(target)
            return True, msg, "action"

        # 6. Windows Window Management & Screenshot
        if any(k in norm for k in ["chụp màn hình", "chụp ảnh màn hình", "screenshot", "screen capture", "take a screenshot"]):
            success, msg = take_screenshot()
            return True, msg, "action"

        if any(k in norm for k in ["đóng cửa sổ", "tắt ứng dụng", "close window", "đóng app"]):
            success, msg = close_active_window()
            return True, msg, "action"

        if any(k in norm for k in ["hiện màn hình chính", "thu nhỏ tất cả", "show desktop", "minimize all"]):
            success, msg = minimize_all_windows()
            return True, msg, "action"

        if any(k in norm for k in ["chuyển tab", "đổi cửa sổ", "switch window", "next tab"]):
            success, msg = switch_window()
            return True, msg, "action"

        # 7. System Power & Security (With Safety confirmation)
        if any(k in norm for k in ["khóa máy", "khóa màn hình", "lock screen", "lock pc"]):
            success, msg = lock_screen()
            return True, msg, "action"

        if any(k in norm for k in ["hủy tắt máy", "cancel shutdown"]):
            success, msg = cancel_shutdown()
            return True, msg, "action"

        if any(k in norm for k in ["tắt máy", "tắt máy tính", "shutdown", "shutdown pc", "power off"]):
            if self.config.get("safety", {}).get("confirm_shutdown", True):
                self.pending_confirmation = "shutdown"
                return True, "Bạn có chắc chắn muốn tắt máy tính không? Hãy nói 'Có' để xác nhận hoặc 'Hủy' để dừng lại.", "confirm"
            else:
                success, msg = shutdown_computer(10)
                return True, msg, "action"

        if any(k in norm for k in ["khởi động lại", "restart", "reboot"]):
            if self.config.get("safety", {}).get("confirm_restart", True):
                self.pending_confirmation = "restart"
                return True, "Bạn có chắc chắn muốn khởi động lại máy tính không?", "confirm"
            else:
                success, msg = restart_computer(10)
                return True, msg, "action"

        # 8. Run custom scripts
        script_match = re.search(r"^(?:chạy script|run script|thực thi)\s+(.+)", norm)
        if script_match:
            script_name = script_match.group(1).strip()
            if not script_name.endswith((".py", ".bat", ".cmd", ".ps1")):
                script_name += ".py"
            success, msg = run_custom_script(script_name)
            return True, msg, "action"

        # 9. Fallback to LLM / Hybrid Brain for general chat, questions, knowledge
        return False, raw_text, "llm"
