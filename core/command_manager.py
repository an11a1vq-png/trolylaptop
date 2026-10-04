import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple


BUILTIN_COMMANDS: List[Dict[str, Any]] = [
    {
        "name": "/hoi",
        "icon": "⚡",
        "desc": "Hỏi đáp AI siêu nhanh, ngắn gọn và súc tích (1-3 câu)",
        "type": "ai_quick",
        "insert_text": "/hoi ",
        "placeholder": "Nhập câu hỏi nhanh...",
        "is_immediate": False
    },
    {
        "name": "/tuvan",
        "icon": "💡",
        "desc": "Tư vấn chuyên sâu, phân tích chi tiết từng bước",
        "type": "ai_deep",
        "insert_text": "/tuvan ",
        "placeholder": "Nhập vấn đề bạn cần tư vấn chuyên sâu...",
        "is_immediate": False
    },
    {
        "name": "/nhac",
        "icon": "🎵",
        "desc": "Tìm và phát nhạc/video trên YouTube",
        "type": "action",
        "insert_text": "mở bài hát ",
        "placeholder": "Nhập tên bài hát hoặc ca sĩ...",
        "is_immediate": False
    },
    {
        "name": "/app",
        "icon": "🚀",
        "desc": "Mở ứng dụng hoặc game trên máy tính",
        "type": "action",
        "insert_text": "mở ",
        "placeholder": "Nhập tên phần mềm, game (như lol, chrome, steam)...",
        "is_immediate": False
    },
    {
        "name": "/tim",
        "icon": "🔍",
        "desc": "Tìm kiếm thông tin trên Google",
        "type": "action",
        "insert_text": "tìm google ",
        "placeholder": "Nhập từ khóa tìm kiếm...",
        "is_immediate": False
    },
    {
        "name": "/yt",
        "icon": "▶",
        "desc": "Tìm kiếm video trên YouTube",
        "type": "action",
        "insert_text": "tìm youtube ",
        "placeholder": "Nhập nội dung video cần tìm...",
        "is_immediate": False
    },
    {
        "name": "/amluong",
        "icon": "🔊",
        "desc": "Đặt âm lượng loa máy tính (0-100%)",
        "type": "action",
        "insert_text": "đặt âm lượng ",
        "placeholder": "Nhập mức âm lượng (ví dụ: 50)...",
        "is_immediate": False
    },
    {
        "name": "/chup",
        "icon": "📸",
        "desc": "Chụp ảnh màn hình ngay lập tức",
        "type": "action",
        "insert_text": "chụp màn hình",
        "placeholder": "",
        "is_immediate": True
    },
    {
        "name": "/khoa",
        "icon": "🔒",
        "desc": "Khóa màn hình máy tính ngay lập tức",
        "type": "action",
        "insert_text": "khóa máy",
        "placeholder": "",
        "is_immediate": True
    },
    {
        "name": "/desktop",
        "icon": "💻",
        "desc": "Thu nhỏ tất cả cửa sổ, hiện màn hình Desktop",
        "type": "action",
        "insert_text": "hiện màn hình chính",
        "placeholder": "",
        "is_immediate": True
    },
    {
        "name": "/clear",
        "icon": "🧹",
        "desc": "Xóa lịch sử trò chuyện trên màn hình",
        "type": "action",
        "insert_text": "xóa lịch sử",
        "placeholder": "",
        "is_immediate": True
    },
]


class CommandManager:
    """
    Manages built-in and user-trained slash commands.
    Supports persistent storage in data/slash_commands.json.
    """
    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            self.data_path = os.path.join(base_dir, "data", "slash_commands.json")
        else:
            self.data_path = data_path

        self.custom_commands: List[Dict[str, Any]] = []
        self._load_custom_commands()

    def _load_custom_commands(self):
        """Load user-defined slash commands from JSON file."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.custom_commands = data.get("custom_commands", [])
            except Exception as e:
                print(f"[CommandManager] Lỗi đọc slash_commands.json: {e}")
                self.custom_commands = []
        else:
            self.custom_commands = []
            self._save_custom_commands()

    def _save_custom_commands(self):
        """Save custom commands to disk."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({"custom_commands": self.custom_commands}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CommandManager] Lỗi ghi slash_commands.json: {e}")

    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Return all available commands: built-ins followed by custom commands."""
        return BUILTIN_COMMANDS + self.custom_commands

    def search_commands(self, query: str) -> List[Dict[str, Any]]:
        """Filter commands by user input prefix (e.g. '/' or '/nh' or '/tu'), prioritized by relevance."""
        q = query.strip().lower()
        if not q.startswith("/"):
            q = "/" + q

        all_cmds = self.get_all_commands()
        if q == "/":
            return all_cmds

        exact_matches = []
        prefix_matches = []
        name_sub_matches = []
        desc_matches = []

        sub = q[1:]  # without '/'

        for cmd in all_cmds:
            name = cmd["name"].lower()
            desc = cmd.get("desc", "").lower()

            if name == q:
                exact_matches.append(cmd)
            elif name.startswith(q):
                prefix_matches.append(cmd)
            elif sub and sub in name:
                name_sub_matches.append(cmd)
            elif len(sub) >= 2 and sub in desc:
                desc_matches.append(cmd)

        return exact_matches + prefix_matches + name_sub_matches + desc_matches

    def add_custom_command(
        self,
        name: str,
        desc: str,
        cmd_type: str,
        action_or_prompt: str,
        icon: str = "✨",
        is_immediate: bool = False
    ) -> Tuple[bool, str]:
        """
        Add or update a custom slash command.
        cmd_type can be:
        - 'action': runs system action / opens app or URL
        - 'ai_prompt': prefixes the query with specialized prompt
        - 'web': opens specific URL
        """
        clean_name = name.strip().lower()
        if not clean_name.startswith("/"):
            clean_name = "/" + clean_name

        # Check if conflicts with built-ins
        if any(b["name"] == clean_name for b in BUILTIN_COMMANDS):
            return False, f"Lệnh '{clean_name}' là lệnh hệ thống mặc định, không thể ghi đè."

        # Remove existing if updating
        self.custom_commands = [c for c in self.custom_commands if c["name"] != clean_name]

        insert_text = action_or_prompt if is_immediate else f"{clean_name} "
        if cmd_type == "action" and not is_immediate and not action_or_prompt.endswith(" "):
            insert_text = action_or_prompt + " "

        new_cmd = {
            "name": clean_name,
            "icon": icon,
            "desc": desc.strip() or f"Lệnh tùy chỉnh: {action_or_prompt}",
            "type": cmd_type,
            "action_content": action_or_prompt,
            "insert_text": insert_text,
            "placeholder": f"Nội dung cho {clean_name}...",
            "is_immediate": is_immediate
        }

        self.custom_commands.append(new_cmd)
        self._save_custom_commands()
        return True, f"Đã lưu lệnh tùy chỉnh '{clean_name}' thành công!"

    def delete_custom_command(self, name: str) -> Tuple[bool, str]:
        """Delete a custom command by name."""
        clean_name = name.strip().lower()
        if not clean_name.startswith("/"):
            clean_name = "/" + clean_name

        initial_len = len(self.custom_commands)
        self.custom_commands = [c for c in self.custom_commands if c["name"] != clean_name]
        if len(self.custom_commands) < initial_len:
            self._save_custom_commands()
            return True, f"Đã xóa lệnh '{clean_name}'."
        return False, f"Không tìm thấy lệnh tùy chỉnh '{clean_name}'."

    def parse_and_teach(self, natural_text: str) -> Optional[Tuple[bool, str]]:
        """
        Parse natural language teaching queries:
        - 'dạy lệnh /game: mở goose goose duck'
        - 'huấn luyện lệnh /dich: Dịch sang tiếng Anh:'
        - 'thêm lệnh /fb: mở https://facebook.com'
        - 'tạo lệnh /chill: mở bài hát lofi chill trên youtube'
        """
        text = natural_text.strip()
        pattern = r"^(?:dạy lệnh|huấn luyện lệnh|thêm lệnh|tạo lệnh)\s+(/[a-zA-Z0-9_\-]+)\s*[:=\-]\s*(.+)$"
        m = re.match(pattern, text, flags=re.IGNORECASE)
        if not m:
            # Also support without slash: 'dạy lệnh game: mở goose goose duck'
            alt_pattern = r"^(?:dạy lệnh|huấn luyện lệnh|thêm lệnh|tạo lệnh)\s+([a-zA-Z0-9_\-]+)\s*[:=\-]\s*(.+)$"
            m = re.match(alt_pattern, text, flags=re.IGNORECASE)
            if not m:
                return None

        cmd_name = m.group(1).strip()
        if not cmd_name.startswith("/"):
            cmd_name = "/" + cmd_name
        action_content = m.group(2).strip()

        # Determine type & icon
        lower_action = action_content.lower()
        if lower_action.startswith("http://") or lower_action.startswith("https://") or "facebook" in lower_action or "github" in lower_action:
            cmd_type = "web"
            icon = "🌐"
            desc = f"Mở liên kết web {action_content}"
            is_immediate = True
        elif any(k in lower_action for k in ["dịch", "tóm tắt", "viết code", "đóng vai", "prompt", "hỏi", "giải thích"]):
            cmd_type = "ai_prompt"
            icon = "🧠"
            desc = f"Prompt AI chuyên biệt: {action_content}"
            is_immediate = False
        else:
            cmd_type = "action"
            icon = "🎮" if any(g in lower_action for g in ["game", "ngỗng", "lol", "chơi"]) else "⚙"
            desc = f"Thực hiện: {action_content}"
            # Immediate if it has no variable parameters (e.g. 'mở goose goose duck')
            is_immediate = True

        success, msg = self.add_custom_command(
            name=cmd_name,
            desc=desc,
            cmd_type=cmd_type,
            action_or_prompt=action_content,
            icon=icon,
            is_immediate=is_immediate
        )
        return success, f"{msg} Bạn có thể gõ '{cmd_name}' bất kỳ lúc nào để kích hoạt."


command_manager = CommandManager()
