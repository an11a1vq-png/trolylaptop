import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class MemoryManager:
    """
    Persistent Long-term Memory for NOVA Assistant.
    Saves conversation history and user knowledge to disk so NOVA never forgets
    even when computer is shut down or restarted.
    """
    def __init__(self, storage_path: Optional[str] = None):
        if not storage_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_path = os.path.join(base_dir, "data", "memory.json")
        self.storage_path = storage_path
        self.user_profile: Dict[str, any] = {"name": "", "facts": []}
        self.conversation_history: List[Dict[str, str]] = []
        self._load()

    def _load(self):
        """Load persistent memory from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_profile = data.get("user_profile", {"name": "", "facts": []})
                    self.conversation_history = data.get("conversation_history", [])
            except Exception as e:
                print(f"[Memory Init Notice] Error reading memory.json: {e}")
                self.user_profile = {"name": "", "facts": []}
                self.conversation_history = []
        else:
            self._save()

    def _save(self):
        """Save memory state to disk atomically."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            temp_path = self.storage_path + ".tmp"
            data = {
                "user_profile": self.user_profile,
                "conversation_history": self.conversation_history[-100:]  # Keep last 100 turns on disk
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if os.path.exists(self.storage_path):
                os.replace(temp_path, self.storage_path)
            else:
                os.rename(temp_path, self.storage_path)
        except Exception as e:
            print(f"[Memory Save Error] {e}")

    def add_turn(self, role: str, content: str):
        """Record a single turn and save to disk."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save()

    def get_recent_history_for_llm(self, max_turns: int = 16) -> List[Dict[str, str]]:
        """Return history in role/content format suitable for LLMs."""
        formatted = []
        for msg in self.conversation_history[-max_turns:]:
            formatted.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        return formatted

    def detect_and_learn_facts(self, query: str) -> Optional[str]:
        """
        Detect if user is teaching NOVA their name, preferences, or rules to remember.
        Returns a friendly confirmation response if an explicit teaching pattern was detected.
        """
        q = query.strip()
        q_lower = q.lower()

        # 1. User tells their name: 'tôi tên là An', 'tên tôi là An', 'tên tao là An', 'gọi tôi là An'
        m_name = re.search(r"^(?:tôi tên là|tên tôi là|tên của tôi là|tên tao là|gọi tôi là|gọi anh là|gọi em là)\s+([^\.,!?]+)", q_lower)
        if m_name:
            name = m_name.group(1).strip().title()
            self.user_profile["name"] = name
            self._save()
            return f"Tôi đã ghi nhớ tên của bạn là {name}. Từ giờ tôi sẽ nhớ điều này kể cả khi bạn tắt máy!"

        # 2. User explicitly instructs to remember: 'hãy nhớ rằng...', 'ghi nhớ: ...', 'nhớ là...', 'sau này nhớ...'
        m_remember = re.search(r"^(?:hãy nhớ rằng|hãy nhớ là|ghi nhớ là|ghi nhớ:|ghi nhớ|nhớ là|sau này nhớ|từ nay nhớ)\s+(.+)", q_lower)
        if m_remember:
            fact = m_remember.group(1).strip()
            if fact and fact not in self.user_profile["facts"]:
                self.user_profile["facts"].append(fact)
                self._save()
            return f"Tôi đã ghi nhớ điều này vào bộ nhớ vĩnh viễn: '{fact}'."

        # 3. User states preference: 'tôi thích nghe nhạc lofi', 'sở thích của tôi là...'
        m_like = re.search(r"^(?:tôi thích|sở thích của tôi là|tôi hay)\s+(.+)", q_lower)
        if m_like:
            preference = m_like.group(1).strip()
            fact_str = f"Sở thích: {preference}"
            if fact_str not in self.user_profile["facts"]:
                self.user_profile["facts"].append(fact_str)
                self._save()
            return f"Tôi đã ghi nhớ sở thích của bạn: '{preference}'."

        # 4. User states occupation: 'tôi là lập trình viên', 'nghề nghiệp của tôi là...'
        m_job = re.search(r"^(?:tôi là|nghề của tôi là|nghề nghiệp của tôi là)\s+(lập trình viên|bác sĩ|kỹ sư|học sinh|sinh viên|giáo viên|nhà thiết kế|coder|developer|game thủ|[^\.,!?]+)", q_lower)
        if m_job and not any(p in q_lower for p in ["ai", "gì"]):
            job = m_job.group(1).strip()
            fact_str = f"Nghề nghiệp / danh tính: {job}"
            if fact_str not in self.user_profile["facts"]:
                self.user_profile["facts"].append(fact_str)
                self._save()
            return f"Tôi đã ghi nhận thông tin nghề nghiệp của bạn: '{job}'."

        return None

    def query_memory_explicitly(self, query: str) -> Optional[str]:
        """Check if user is asking NOVA what it remembers about them."""
        q_lower = query.strip().lower()

        # Asking for name
        if any(p in q_lower for p in ["tôi tên gì", "tên tôi là gì", "tên tao là gì", "tôi tên là gì", "nhớ tôi tên gì không"]):
            name = self.user_profile.get("name")
            if name:
                return f"Bạn tên là {name}, tôi luôn ghi nhớ điều đó!"
            else:
                return "Bạn chưa cho tôi biết tên của bạn. Hãy nói 'Tôi tên là...' để tôi ghi nhớ nhé!"

        # Asking what NOVA remembers
        if any(p in q_lower for p in ["bạn biết gì về tôi", "bạn nhớ gì về tôi", "tôi đã dạy bạn điều gì", "bạn đã nhớ được những gì", "xem bộ nhớ"]):
            name = self.user_profile.get("name")
            facts = self.user_profile.get("facts", [])
            if not name and not facts:
                return "Hiện tại tôi chưa có thông tin ghi nhớ nào về bạn. Hãy dạy tôi bằng cách nói 'Tôi tên là...', 'Tôi thích...', hoặc 'Hãy nhớ rằng...' nhé!"
            
            lines = ["Dưới đây là những gì tôi đã ghi nhớ về bạn trong bộ nhớ vĩnh viễn:"]
            if name:
                lines.append(f"• Tên của bạn: {name}")
            if facts:
                lines.append("• Những điều bạn đã dạy tôi:")
                for f in facts:
                    lines.append(f"  - {f}")
            return "\n".join(lines)

        return None

    def get_system_prompt_injection(self) -> str:
        """Generate text to inject into the LLM system prompt so the model always acts on learned facts."""
        name = self.user_profile.get("name")
        facts = self.user_profile.get("facts", [])
        if not name and not facts:
            return ""

        context_lines = ["\n[THÔNG TIN BỘ NHỚ DÀI HẠN VỀ NGƯỜI DÙNG - ĐÃ GHI NHỚ VĨNH VIỄN]:"]
        if name:
            context_lines.append(f"- Tên người dùng: {name} (Hãy xưng hô thân thiện với tên này).")
        if facts:
            context_lines.append("- Những điều người dùng đã dạy bạn / sở thích:")
            for f in facts:
                context_lines.append(f"  + {f}")
        context_lines.append("Hãy luôn nhớ và áp dụng những thông tin trên khi trò chuyện với người dùng.")
        return "\n".join(context_lines)

    def clear_history_only(self) -> str:
        """Clear conversation context while preserving user profile and learned facts."""
        self.conversation_history.clear()
        self._save()
        return "Đã xóa lịch sử trò chuyện gần đây. Các thông tin bạn đã dạy tôi (tên, sở thích) vẫn được giữ nguyên vẹn trong bộ nhớ vĩnh viễn!"

    def clear_all(self) -> str:
        """Reset everything."""
        self.conversation_history.clear()
        self.user_profile = {"name": "", "facts": []}
        self._save()
        return "Đã xóa toàn bộ dữ liệu ghi nhớ vĩnh viễn và lịch sử trò chuyện."


# Global singleton instance
memory_manager = MemoryManager()
