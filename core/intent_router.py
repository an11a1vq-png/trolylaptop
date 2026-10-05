import re
from typing import Tuple, Optional

from actions.system_controls import (
    set_volume, change_volume, toggle_mute, lock_screen,
    shutdown_computer, restart_computer, cancel_shutdown,
    media_play_pause, media_next, media_previous
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
from actions.math_solver import solve_math_query
from core.command_manager import command_manager


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

        # 3. Quick Math Solver (< 0.5ms instant response for all arithmetic in Vietnamese & numbers)
        math_reply = solve_math_query(raw_text) or solve_math_query(norm)
        if math_reply:
            return True, math_reply, "action"

        # 3. Natural Language Command Training (e.g. 'Dạy lệnh /game: mở goose goose duck')
        teach_result = command_manager.parse_and_teach(raw_text)
        if teach_result is not None:
            success, msg = teach_result
            return True, msg, "action"

        # 4. Direct Slash Commands (e.g. /hoi, /tuvan, /nhac, /app, /tim, /chup, /khoa, /clear)
        if raw_text.startswith("/"):
            parts = raw_text.split(maxsplit=1)
            cmd_name = parts[0].lower()
            args = parts[1].strip() if len(parts) > 1 else ""

            if cmd_name == "/hoi":
                if not args:
                    return True, "Vui lòng nhập câu hỏi sau /hoi. Ví dụ: /hoi thủ đô nước Pháp là gì?", "action"
                prompt = f"[CHẾ ĐỘ HỎI ĐÁP NHANH] Trả lời cực kỳ ngắn gọn, súc tích (1-3 câu), đi thẳng vào câu trả lời chính, không dài dòng: {args}"
                return False, prompt, "llm"

            elif cmd_name == "/tuvan":
                if not args:
                    return True, "Vui lòng nhập vấn đề cần tư vấn sau /tuvan. Ví dụ: /tuvan cách học lập trình Python", "action"
                prompt = f"[CHẾ ĐỘ TƯ VẤN CHUYÊN GIA] Hãy đóng vai chuyên gia tư vấn hàng đầu, phân tích sâu, đưa ra lời khuyên chi tiết từng bước và phương án tối ưu cho: {args}"
                return False, prompt, "llm"

            elif cmd_name == "/nhac":
                if not args:
                    return True, "Vui lòng nhập tên bài hát sau /nhac. Ví dụ: /nhac lưu niên", "action"
                success, msg = search_youtube(args)
                return True, msg, "action"

            elif cmd_name == "/app":
                if not args:
                    return True, "Vui lòng nhập tên ứng dụng sau /app. Ví dụ: /app lol hoặc /app chrome", "action"
                success, msg = open_application(args)
                return True, msg, "action"

            elif cmd_name == "/tim":
                if not args:
                    return True, "Vui lòng nhập nội dung tìm kiếm sau /tim.", "action"
                success, msg = search_google(args)
                return True, msg, "action"

            elif cmd_name == "/yt":
                if not args:
                    return True, "Vui lòng nhập từ khóa tìm kiếm YouTube sau /yt.", "action"
                success, msg = search_youtube(args)
                return True, msg, "action"

            elif cmd_name in ["/chup", "/screenshot"]:
                success, msg = take_screenshot()
                return True, msg, "action"

            elif cmd_name in ["/khoa", "/lock"]:
                success, msg = lock_screen()
                return True, msg, "action"

            elif cmd_name == "/desktop":
                success, msg = minimize_all_windows()
                return True, msg, "action"

            elif cmd_name in ["/amluong", "/vol"]:
                if not args:
                    return True, "Vui lòng nhập mức âm lượng sau /amluong. Ví dụ: /amluong 50", "action"
                try:
                    val_match = re.search(r'\d+', args)
                    if val_match:
                        val = int(val_match.group())
                        success, msg = set_volume(val)
                        return True, msg, "action"
                except Exception:
                    pass
                return False, "Mức âm lượng không hợp lệ", "action"

            elif cmd_name == "/clear":
                return True, "CLEAR_CHAT_HISTORY", "clear"

            # Check user-defined custom commands
            for c in command_manager.custom_commands:
                if c["name"] == cmd_name:
                    c_type = c.get("type", "action")
                    c_action = c.get("action_content", "")
                    if c_type == "web":
                        success, msg = open_application(c_action)
                        return True, msg, "action"
                    elif c_type == "ai_prompt":
                        full_prompt = f"{c_action} {args}".strip()
                        return False, full_prompt, "llm"
                    else:  # action
                        action_text = f"{c_action} {args}".strip() if args else c_action
                        return self.route_text(action_text)

            return True, f"Không tìm thấy lệnh '{cmd_name}'. Hãy gõ '/' để xem danh sách lệnh có sẵn.", "action"

        # 5. System Volume & Audio Control (Bulletproof matching without false positives on 'nhạc')
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

        # Media Playback Controls (Play / Pause / Next / Prev)
        if any(k in norm for k in ["tạm dừng", "dừng nhạc", "dừng video", "tiếp tục phát", "phát tiếp", "pause video", "play video", "dừng bài"]):
            success, msg = media_play_pause()
            return True, msg, "action"

        if any(k in norm for k in ["chuyển bài", "bài tiếp theo", "next bài", "bài kế tiếp", "qua bài"]):
            success, msg = media_next()
            return True, msg, "action"

        if any(k in norm for k in ["bài trước", "lùi bài", "quay lại bài trước", "previous bài"]):
            success, msg = media_previous()
            return True, msg, "action"

        # 4. Search Commands
        # Flexible Pattern 1: Search [query] on [engine] ("mở bài lưu niên trên youtube", "tìm nhạc lofi trên youtube", "tìm thời tiết trên google")
        search_target_match = re.search(r"^(?:tìm kiếm|tìm|search|tra cứu|mở|bật|xem|phát)\s+(.+?)\s+(?:trên|qua|ở|tại|on)\s+(youtube|google)$", norm)
        if search_target_match:
            raw_query = search_target_match.group(1).strip()
            engine = search_target_match.group(2).strip()
            if engine == "youtube":
                clean_query = re.sub(r"^(?:bài hát|bản nhạc|ca khúc|bài|video|clip|kênh)\s+", "", raw_query, flags=re.IGNORECASE).strip()
                success, msg = search_youtube(clean_query)
            else:
                clean_query = re.sub(r"^(?:thông tin về|về)\s+", "", raw_query, flags=re.IGNORECASE).strip()
                success, msg = search_google(clean_query)
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

        # 5. Media / Music / Video Playback (e.g. 'mở bài lưu niên', 'nghe nhạc lofi', 'bật bài hát abc', 'xem clip hài', 'mở kênh phd troll')
        media_match = re.search(r"^(?:mở|bật|nghe|phát|chơi|xem)\s+(bài hát|bản nhạc|ca khúc|bài|nhạc|video|clip|phim|kênh)\s+(.+)|^nghe\s+(.+)", norm)
        if media_match:
            if media_match.group(1):
                kw = media_match.group(1).strip()
                rest = media_match.group(2).strip()
                rest = re.sub(r"\s+(?:trên|qua|ở|tại|on)\s+(?:youtube|google|web|mạng)$", "", rest, flags=re.IGNORECASE).strip()
                if kw in ["nhạc", "phim", "video", "clip", "kênh"]:
                    song_or_video = f"{kw} {rest}"
                else:
                    song_or_video = rest
            else:
                song_or_video = media_match.group(3).strip()
                song_or_video = re.sub(r"\s+(?:trên|qua|ở|tại|on)\s+(?:youtube|google|web|mạng)$", "", song_or_video, flags=re.IGNORECASE).strip()

            # Check if user specified a browser (e.g. 'mở bài lưu niên bằng chrome')
            browser_match = re.search(r"^(.*?)\s+(?:bằng|qua|trên|với|in|with)\s+(chrome|cốc cốc|coc coc|edge|firefox)$", song_or_video)
            specific_browser = None
            if browser_match:
                song_or_video = browser_match.group(1).strip()
                specific_browser = browser_match.group(2).strip()
            success, msg = search_youtube(song_or_video, specific_browser=specific_browser)
            return True, msg, "action"

        # 6. Open Applications / Websites / Folders / Games
        # Supports verbs: mở, bật, khởi động, chạy, vào, truy cập, chơi, open, launch
        open_match = re.search(r"^(?:mở|bật|khởi động|chạy|vào|truy cập|chơi|open|launch)\s+(.+)", norm)
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
