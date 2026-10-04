import re
from typing import Tuple, Optional

from actions.system_controls import (
    set_volume, change_volume, toggle_mute, lock_screen,
    shutdown_computer, restart_computer, cancel_shutdown
)
from actions.app_launcher import (
    open_application, search_google, search_youtube
)
from actions.window_manager import (
    take_screenshot, minimize_all_windows, close_active_window,
    close_active_tab, maximize_window, switch_window
)
from actions.voice_dictation import dictation_manager
from actions.custom_scripts import open_folder, run_custom_script


def _clean_conversational_fillers(text: str) -> str:
    """Strip polite/conversational particles from text across the entire sentence."""
    cleaned = text.strip().lower()
    fillers = [
        'làm ơn', 'vui lòng', 'hãy', 'giúp tôi', 'giùm tôi',
        'hộ tôi', 'cho tôi', 'cho mình', 'hộ mình', 'giùm', 'hộ',
        'nhé', 'nha', 'đi', 'nào', 'với'
    ]
    for f in fillers:
        cleaned = re.sub(r'(?:^|\s)' + re.escape(f) + r'(?:\s|$)', ' ', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


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
        norm = _clean_conversational_fillers(raw_text)

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
        if any(p in norm for p in ["bật gõ văn bản", "bật chế độ gõ", "start dictation", "bắt đầu gõ", "mở gõ văn bản"]):
            dictation_manager.is_dictating = True
            return True, "Đã bật chế độ gõ văn bản bằng giọng nói. Mọi câu bạn nói sẽ được gõ vào màn hình.", "action"

        if any(p in norm for p in ["tắt gõ văn bản", "dừng gõ văn bản", "stop dictation", "dừng gõ", "ngừng gõ", "đóng gõ văn bản"]):
            dictation_manager.is_dictating = False
            return True, "Đã tắt chế độ gõ văn bản.", "action"

        # If dictation is currently active, type it out directly!
        if dictation_manager.is_dictating:
            dictation_manager.type_text(raw_text)
            return True, f"Đã gõ: {raw_text}", "dictation"

        # 3. System Volume & Audio Control (Bulletproof matching without false positives on 'nhạc')
        # Volume Up
        m_vol_up = re.search(r'(?:^|\s)(?:tăng|bật to)\s*(?:âm lượng|volume|âm thanh)?\s*(?:lên|thêm)?\s*(\d+)?|(?:^|\s)to lên', norm)
        if m_vol_up:
            delta = int(m_vol_up.group(1)) if m_vol_up.group(1) else 10
            success, msg = change_volume(delta)
            return True, msg, "action"

        # Volume Down
        m_vol_down = re.search(r'(?:^|\s)(?:giảm|hạ|cho nhỏ)\s*(?:âm lượng|volume|âm thanh)?\s*(?:xuống|đi|bớt)?\s*(\d+)?|(?:^|\s)(?:nhỏ lại|nhỏ đi)', norm)
        if m_vol_down:
            delta = int(m_vol_down.group(1)) if m_vol_down.group(1) else 10
            success, msg = change_volume(-delta)
            return True, msg, "action"

        # Absolute Volume Set
        m_vol_set = re.search(r'(?:^|\s)(?:đặt|chỉnh|cài|set)?\s*(?:âm lượng|volume|âm thanh)\s*(?:thành|về|to|=|là)?\s*(\d{1,3})%?', norm)
        if m_vol_set and not any(w in norm for w in ["tăng", "giảm", "to", "nhỏ"]):
            val = int(m_vol_set.group(1))
            success, msg = set_volume(val)
            return True, msg, "action"

        # Mute / Unmute
        if any(k in norm for k in ["tắt tiếng", "bật tiếng", "mute", "unmute", "im lặng"]):
            success, msg = toggle_mute()
            return True, msg, "action"

        # 4. Search Commands
        # Flexible Pattern 1: Search [query] on [engine] ("tìm nhạc lofi trên youtube", "tìm thời tiết trên google")
        search_target_match = re.search(r"^(?:tìm kiếm|tìm|search|tra cứu)\s+(.+?)\s+(?:trên|qua|ở|bằng|on)\s+(youtube|google)$", norm)
        if search_target_match:
            query = search_target_match.group(1).strip()
            engine = search_target_match.group(2).strip()
            if engine == "youtube":
                success, msg = search_youtube(query)
            else:
                success, msg = search_google(query)
            return True, msg, "action"

        # Flexible Pattern 2: Search Google ("tìm kiếm google [query]", "tìm google [query]", "tra google [query]")
        google_match = re.search(r"^(?:tìm kiếm google|tìm google|search google for|tra google|google)\s+(.+)", norm)
        if google_match:
            query = google_match.group(1)
            success, msg = search_google(query)
            return True, msg, "action"

        # Flexible Pattern 3: Search YouTube ("tìm kiếm youtube [query]", "mở youtube tìm [query]", "tìm trên youtube [query]")
        youtube_match = re.search(r"^(?:tìm kiếm youtube|mở youtube tìm|tìm trên youtube|search youtube for)\s+(.+)", norm)
        if youtube_match:
            query = youtube_match.group(1)
            success, msg = search_youtube(query)
            return True, msg, "action"

        # 5. Open Applications / Websites / Folders
        # Supports verbs: mở, bật, khởi động, chạy, vào, truy cập, open, launch
        open_match = re.search(r"^(?:mở|bật|khởi động|chạy|vào|truy cập|open|launch)\s+(.+)", norm)
        if open_match:
            target = open_match.group(1).strip()
            # If target is project folder
            if target in ["thư mục dự án", "project folder", "code", "mã nguồn"]:
                success, msg = open_folder("d:\\ailap")
                return True, msg, "action"
            # Launch app / website
            success, msg = open_application(target)
            return True, msg, "action"

        # 6. Windows Window Management & Screenshot
        if any(k in norm for k in ["chụp màn hình", "chụp ảnh màn hình", "chụp lại màn hình", "screenshot", "screen capture", "take a screenshot"]):
            success, msg = take_screenshot()
            return True, msg, "action"

        if any(k in norm for k in ["đóng tab", "tắt tab", "close tab"]):
            success, msg = close_active_tab()
            return True, msg, "action"

        if any(k in norm for k in ["phóng to", "phóng to cửa sổ", "maximize window"]):
            success, msg = maximize_window()
            return True, msg, "action"

        if any(k in norm for k in ["đóng cửa sổ", "tắt cửa sổ", "tắt ứng dụng", "close window", "đóng app", "tắt app"]):
            success, msg = close_active_window()
            return True, msg, "action"

        if any(k in norm for k in ["hiện màn hình chính", "thu nhỏ tất cả", "show desktop", "minimize all", "về màn hình chính", "hiện desktop", "màn hình chính"]):
            success, msg = minimize_all_windows()
            return True, msg, "action"

        if any(k in norm for k in ["chuyển tab", "đổi cửa sổ", "switch window", "next tab", "đổi tab"]):
            success, msg = switch_window()
            return True, msg, "action"

        # 7. System Power & Security (With Safety confirmation)
        if any(k in norm for k in ["khóa máy", "khóa màn hình", "lock screen", "lock pc"]):
            success, msg = lock_screen()
            return True, msg, "action"

        if any(k in norm for k in ["hủy tắt máy", "cancel shutdown"]):
            success, msg = cancel_shutdown()
            return True, msg, "action"

        if any(k in norm for k in ["tắt máy", "tắt máy tính", "shutdown", "shutdown pc", "power off", "tắt pc"]):
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
